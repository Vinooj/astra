import asyncio
import sys
from loguru import logger
from pydantic import BaseModel
from typing import List, Callable, Optional, Union
from functools import reduce

# --- Import our framework classes ---
from astra_framework.manager import WorkflowManager
from astra_framework.agents.llm_agent import LLMAgent
from astra_framework.agents.loop_agent import LoopAgent
from astra_framework.agents.sequential_agent import SequentialAgent
from astra_framework.agents.parallel_agent import ParallelAgent
from astra_framework.services.client_factory import LLMClientFactory
from astra_framework.core.state import SessionState

# ==============================================================================
# 1. CONFIGURE LOGGER
# ==============================================================================
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="{time:HH:mm:ss.SSS} | {level: <8} | {name: <15}:{function: <15}:{line: >3} - {message}",
    colorize=True
)

# ==============================================================================
# 2. DEFINE TOOLS
# ==============================================================================
def add(numbers: Union[List[int], str]) -> int:
    """Adds a list of numbers."""
    logger.info(f"Adding numbers: {numbers}")
    if isinstance(numbers, str):
        num_list = [int(n.strip()) for n in numbers.split(',')]
    else:
        num_list = numbers
    return sum(num_list)

def multiply(numbers: Union[List[int], str]) -> int:
    """Multiplies a list of numbers."""
    logger.info(f"Multiplying numbers: {numbers}")
    if isinstance(numbers, str):
        num_list = [int(n.strip()) for n in numbers.split(',')]
    else:
        num_list = numbers
    return reduce(lambda x, y: x * y, num_list)

# ==============================================================================
# 3. DEFINE PYDANTIC MODELS FOR STRUCTURED OUTPUT
# ==============================================================================
class NumberList(BaseModel):
    numbers: List[int]

class FinalReport(BaseModel):
    addition_result: int
    multiplication_result: int
    summary: str

class CritiqueResult(BaseModel):
    approved: bool
    feedback: str

# ==============================================================================
# 4. DEFINE THE WORKFLOW
# ==============================================================================
async def main():
    logger.info("============================================")
    logger.info("     STARTING ASTRA MATH DEMO WORKFLOW      ")
    logger.info("============================================")
    
    # --- 1. Create services ---
    manager = WorkflowManager()
    ollama_llm = LLMClientFactory.create_client(client_type="ollama", model="qwen3:latest")

    # --- 2. Define Specialist Agents ---
    proposer_agent = LLMAgent(
        agent_name="ProposerAgent",
        llm_client=ollama_llm,
        tools=[],
        instruction="You are a creative agent. Propose a list of 4 random integers between 1 and 10. Your final answer must be in the structured_output format.",
        output_structure=NumberList
    )

    adder_agent = LLMAgent(
        agent_name="AdderAgent",
        llm_client=ollama_llm,
        tools=[add],
        instruction="You are an addition specialist. The user will provide a list of numbers. Use the 'add' tool to compute the sum.",
    )

    multiplier_agent = LLMAgent(
        agent_name="MultiplierAgent",
        llm_client=ollama_llm,
        tools=[multiply],
        instruction="You are a multiplication specialist. The user will provide a list of numbers. Use the 'multiply' tool to compute the product.",
    )

    parallel_math_agent = ParallelAgent(
        agent_name="ParallelMathAgent",
        children=[adder_agent, multiplier_agent]
    )

    aggregator_agent = LLMAgent(
        agent_name="AggregatorAgent",
        llm_client=ollama_llm,
        tools=[],
        instruction="You are a reporting agent. The user will provide the results of parallel computations (addition and multiplication). Your job is to create a final report summarizing these results. The addition result is the first element in the list, and the multiplication result is the second. Your final answer must be in the structured_output format.",
        output_structure=FinalReport
    )

    critique_agent = LLMAgent(
        agent_name="CritiqueAgent",
        llm_client=ollama_llm,
        tools=[],
        instruction="You are a quality assurance agent. The user will provide a final report. Your job is to verify that the summary is accurate and that the results are correct. If everything is perfect, set 'approved' to true. Otherwise, set 'approved' to false and provide feedback. Your response MUST be in the structured_output format.",
        output_structure=CritiqueResult
    )

    # --- 3. Define the Loop Exit Condition ---
    def critique_is_approved(state: SessionState) -> bool:
        last_message = state.history[-1]
        if last_message.role == "user":
            try:
                critique = CritiqueResult.model_validate_json(last_message.content)
                if critique.approved:
                    logger.success("Critique approved. Exiting loop.")
                    return True
                else:
                    logger.warning(f"Critique not approved. Feedback: {critique.feedback}")
                    return False
            except Exception as e:
                logger.error(f"Could not parse critique result: {e}")
                return False
        return False

    # --- 4. Compose the Workflow ---
    main_sequence = SequentialAgent(
        agent_name="MainSequence",
        children=[proposer_agent, parallel_math_agent, aggregator_agent, critique_agent],
        keep_alive_state=True
    )

    main_loop = LoopAgent(
        agent_name="MainLoop",
        child=main_sequence,
        max_loops=3,
        exit_condition=critique_is_approved,
        keep_alive_state=True
    )

    # --- 5. Register Workflow(s) with the Manager ---
    manager.register_workflow(name="math_parallel_workflow", agent=main_loop)
    
    # --- 6. Execute ---
    session_id = manager.create_session()
    prompt = "Generate a list of numbers and perform calculations."
    
    final_response = await manager.run(
        workflow_name="math_parallel_workflow",
        session_id=session_id,
        prompt=prompt
    )
    
    logger.info("============================================")
    logger.info("            WORKFLOW COMPLETE             ")
    logger.info("============================================")
    
    print(f"\nWorkflow finished.\nInitial Prompt: {prompt}\n")
    
    # Retrieve the final report from the history
    final_state = manager.get_session_state(session_id)
    final_report = None
    for msg in reversed(final_state.history):
        if msg.role == "user":
            try:
                report = FinalReport.model_validate_json(msg.content)
                final_report = report
                break
            except Exception:
                continue
    
    if final_report:
        print("--- Final Report ---")
        print(f"  Addition Result: {final_report.addition_result}")
        print(f"  Multiplication Result: {final_report.multiplication_result}")
        print(f"  Summary: {final_report.summary}")
        print("\n--- Full Report (JSON) ---")
        print(final_report.model_dump_json(indent=2))
    else:
        print("Could not find the final report in the session history.")

if __name__ == "__main__":
    asyncio.run(main())
