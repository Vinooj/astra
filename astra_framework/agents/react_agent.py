import asyncio
from loguru import logger
from typing import List, Callable, Optional, Type, Union
from pydantic import BaseModel

from astra_framework.core.agent import BaseAgent
from astra_framework.core.state import SessionState, ChatMessage
from astra_framework.core.models import AgentResponse
from astra_framework.services.base_client import BaseLLMClient
from astra_framework.core.tool import ToolManager

class ReActAgent(BaseAgent):
    """
    An agent that implements the ReAct (Reason, Act, Observe) pattern.
    It uses an LLM to reason about a goal, selects and executes tools to act, 
    and observes the results to inform the next cycle.
    """ 
    def __init__(self, 
                 agent_name: str, 
                 llm_client: BaseLLMClient,
                 tools: List[Callable],
                 instruction: str,
                 max_iterations: int = 10,
                 output_structure: Optional[Type[BaseModel]] = None):
        super().__init__(agent_name, output_structure)
        self.llm = llm_client
        self.tool_manager = ToolManager(tools)
        self.instruction = instruction
        self.max_iterations = max_iterations

    async def execute(self, state: SessionState) -> AgentResponse:
        """Executes the ReAct loop until a final answer is produced or max_iterations is reached."""
        logger.info(f"--- Executing ReActAgent: {self.agent_name} ---")

        # Add the main instruction to the system prompt
        system_message = ChatMessage(role="system", content=self.instruction)
        # Create a temporary history for this execution run
        execution_history = [system_message] + state.history

        for i in range(self.max_iterations):
            logger.info(f"[{self.agent_name}] Starting ReAct Iteration {i+1}/{self.max_iterations}")

            # 1. REASON: Call the LLM to decide the next action
            llm_response: Union[str, Dict[str, Any]] = await self.llm.generate(
                execution_history,
                tools=self.tool_manager.get_tool_definitions()
            )

            tool_calls = None
            final_content = None

            if isinstance(llm_response, dict):
                tool_calls = llm_response.get("tool_calls")
                if not tool_calls: # It's a dict, but no tool_calls, so it's a final message dict
                    final_content = llm_response.get("content", "")
            elif isinstance(llm_response, str):
                final_content = llm_response # It's a string, so it's a final message string
            else:
                logger.error(f"[{self.agent_name}] Unexpected LLM response type: {type(llm_response)}")
                final_content = "Error: Unexpected LLM response."

            if final_content is not None: # If we have a final content, it means no tool calls
                logger.success(f"[{self.agent_name}] LLM provided a final answer. Ending loop.")
                state.add_message(role="agent", content=final_content)
                return AgentResponse(status="success", final_content=final_content)
            else: # We must have tool_calls
                # 2. ACT: Execute the tool calls
                # Add the tool calls to the history for context in the next LLM call
                execution_history.append(ChatMessage(role="agent", content=str(tool_calls)))
                
                for tool_call in tool_calls:
                    function_name = tool_call.get("function", {}).get("name")
                    function_args = tool_call.get("function", {}).get("arguments", {})
                    
                    logger.info(f"[{self.agent_name}] LLM decided to call tool: {function_name} with args: {function_args}")
                    
                    try:
                        # Use the tool manager to execute the function
                        tool_output = await self.tool_manager.execute_tool(function_name, function_args)
                        
                        # 3. OBSERVE: Add the tool's output to history for the next loop
                        observation_message = ChatMessage(
                            role="tool",
                            content=str(tool_output)
                        )
                        execution_history.append(observation_message)
                        logger.info(f"[{self.agent_name}] Tool '{function_name}' executed successfully.")

                    except Exception as e:
                        logger.error(f"[{self.agent_name}] Error executing tool '{function_name}': {e}")
                        error_message = ChatMessage(role="tool", content=f"Error: {e}")
                        execution_history.append(error_message)
        
        logger.warning(f"[{self.agent_name}] Max iterations ({self.max_iterations}) reached. Ending loop.")
        final_content = execution_history[-1].content
        state.add_message(role="agent", content=final_content)
        return AgentResponse(status="max_iterations_reached", final_content=final_content)
