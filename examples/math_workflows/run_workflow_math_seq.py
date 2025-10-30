import asyncio
import sys
from loguru import logger
from pydantic import BaseModel
from typing import List, Callable, Optional

# --- Import our framework classes ---
from astra_framework.manager import WorkflowManager
from astra_framework.agents.llm_agent import LLMAgent
from astra_framework.agents.sequential_agent import SequentialAgent
from astra_framework.services.client_factory import LLMClientFactory

# ==============================================================================
# 1. CONFIGURE LOGGER
# ==============================================================================
logger.remove()
logger.add(
    sys.stderr,
    level="DEBUG",
    format="{time:HH:mm:ss.SSS} | {level: <8} | {name: <15}:{function: <15}:{line: >3} - {message}",
    colorize=True
)

# ==============================================================================
# 2. DEFINE A PYDANTIC MODEL FOR STRUCTURED OUTPUT
# ==============================================================================
class CalculationResult(BaseModel):
    result: int
    explanation: str

# ==============================================================================
# 3. EXECUTE THE WORKFLOW
# ==============================================================================
async def main():
    logger.info("============================================")
    logger.info("     STARTING ASTRA AGENTIC WORKFLOW (V3)   ")
    logger.info("============================================")
    
    # --- Define tools ---
    def add(a: int, b: int) -> int:
        """Adds two integers."""
        return a + b

    def multiply(a: int, b: int) -> int:
        """Multiplies two integers."""
        return a * b
    
    # --- 1. Create the Facade ---
    manager = WorkflowManager()
    
    # --- 2. Create the LLM service ---
    ollama_llm = LLMClientFactory.create_client(client_type="ollama", model="qwen3:latest")

    # --- 3. Define Specialist Agents ---
    calculator_agent = LLMAgent(
        agent_name="CalculatorAgent",
        llm_client=ollama_llm,
        tools=[add, multiply],
        instruction="You are a Calculator agent. Your job is to use the add and multiply tools to solve math equations. Apply the order of operations. Your final answer must be in the structured_output format.",
        output_structure=CalculationResult
    )

    reporter_agent = LLMAgent(
        agent_name="ReporterAgent",
        llm_client=ollama_llm,
        tools=[],
        instruction="You are a reporter agent. The user will provide a JSON object with a calculation result and an explanation. Your job is to present this information to the user in a clear, human-readable format."
    )

    # --- 4. Compose Workflow ---
    math_workflow = SequentialAgent(
        agent_name="MathWorkflow",
        children=[calculator_agent, reporter_agent]
    )

    # --- 5. Register Workflow(s) with the Manager ---
    manager.register_workflow(name="math_workflow", agent=math_workflow)
    
    # --- 6. Execute ---
    session_id = manager.create_session()
    prompt = "10 + 5 * 3"
    
    final_response = await manager.run(
        workflow_name="math_workflow",
        session_id=session_id,
        prompt=prompt
    )
    
    logger.info("============================================")
    logger.info("            WORKFLOW COMPLETE (V3)          ")
    logger.info("============================================")
    
    print(f"\nWorkflow finished.\nInitial Prompt: {prompt}\nFinal Answer: {final_response.final_content}\n")
    
    print("--- Final Session State (Blackboard) ---")
    final_state = manager.get_session_state(session_id)
    import json
    print(json.dumps(final_state.data, indent=2))
    
    print("\n--- Full Chat History ---")
    for msg in final_state.history:
        print(f"- {msg.role.upper()}: {msg.content}")

if __name__ == "__main__":
    asyncio.run(main())