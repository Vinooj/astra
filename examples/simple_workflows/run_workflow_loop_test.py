import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import asyncio
from loguru import logger
from pydantic import BaseModel
from typing import List, Callable

# --- Import our framework classes ---
from astra_framework.manager import WorkflowManager
from astra_framework.agents.llm_agent import LLMAgent
from astra_framework.agents.loop_agent import LoopAgent
from astra_framework.agents.sequential_agent import SequentialAgent
from astra_framework.services.client_factory import LLMClientFactory
from astra_framework.core.state import SessionState

# ==============================================================================
# 1. CONFIGURE LOGGER
# ==============================================================================
logger.remove()
logger.add(
    sys.stderr,
    level="INFO", # Set to INFO for a cleaner output for this test
    format="{time:HH:mm:ss.SSS} | {level: <8} | {name: <15}:{function: <15}:{line: >3} - {message}",
    colorize=True
)

# ==============================================================================
# 2. DEFINE PYDANTIC MODELS FOR STRUCTURED OUTPUT
# ==============================================================================
class NumberProposal(BaseModel):
    number: int
    reasoning: str

class ValidationResult(BaseModel):
    approved: bool
    reason: str

# ==============================================================================
# 3. DEFINE THE WORKFLOW
# ==============================================================================
async def main():
    logger.info("============================================")
    logger.info("     STARTING LOOPAGENT VALIDATION WORKFLOW ")
    logger.info("============================================")
    
    # --- 1. Create services ---
    manager = WorkflowManager()
    ollama_llm = LLMClientFactory.create_client(client_type="ollama", model="qwen3:latest")

    # --- 2. Define Specialist Agents ---
    proposer_agent = LLMAgent(
        agent_name="ProposerAgent",
        llm_client=ollama_llm,
        tools=[],
        instruction="You are a random number generator. Your goal is to propose a number between 5 and 15. Use the structured_output format.",
        output_structure=NumberProposal
    )

    validator_agent = LLMAgent(
        agent_name="ValidatorAgent",
        llm_client=ollama_llm,
        tools=[],
        instruction="You are a validator. The user will provide a JSON object with a number proposal. Your job is to check if the number is greater than 10. If it is, set 'approved' to true. Otherwise, set 'approved' to false and provide a reason. Your response MUST be in the structured_output format.",
        output_structure=ValidationResult
    )

    # --- 3. Define the Loop Exit Condition ---
    def validation_is_approved(state: SessionState) -> bool:
        last_message = state.history[-1]
        if last_message.role == "user": # The validation result is passed as a user message
            try:
                validation = ValidationResult.model_validate_json(last_message.content)
                if validation.approved:
                    logger.success("Validation approved. Exiting loop.")
                    return True
                else:
                    logger.warning(f"Validation failed. Reason: {validation.reason}")
                    return False
            except Exception as e:
                logger.error(f"Could not parse validation result: {e}")
                return False
        return False

    # --- 4. Compose the Workflow ---
    validation_sequence = SequentialAgent(
        agent_name="ValidationSequence",
        children=[proposer_agent, validator_agent]
    )

    validation_loop = LoopAgent(
        agent_name="ValidationLoop",
        child=validation_sequence,
        max_loops=3,
        exit_condition=validation_is_approved
    )

    # --- 5. Register Workflow(s) with the Manager ---
    manager.register_workflow(name="loop_test", agent=validation_loop)
    
    # --- 6. Execute ---
    session_id = manager.create_session()
    prompt = "Generate a number."
    
    final_response = await manager.run(
        workflow_name="loop_test",
        session_id=session_id,
        prompt=prompt
    )
    
    logger.info("============================================")
    logger.info("            WORKFLOW COMPLETE             ")
    logger.info("============================================")
    
    print(f"\nWorkflow finished.\nInitial Prompt: {prompt}\n")
    
    if isinstance(final_response.final_content, BaseModel):
        print("--- Final Output ---")
        print(final_response.final_content.model_dump_json(indent=2))
    else:
        print(f"--- Final Answer ---\n{final_response.final_content}")

if __name__ == "__main__":
    asyncio.run(main())
