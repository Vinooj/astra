from loguru import logger
from typing import List, Callable, Dict, Any, Optional, Type
import inspect
import json
from pydantic import BaseModel
from astra_framework.core.agent import BaseAgent
from astra_framework.core.state import SessionState, ChatMessage
from astra_framework.core.models import AgentResponse
from astra_framework.services.ollama_client import OllamaClient
from astra_framework.core.tool import ToolManager

class LLMAgent(BaseAgent):
    """The main 'thinking' agent, implementing the ReACT loop."""
    
    def __init__(self, agent_name: str, llm_client: OllamaClient, 
                 tools: List[Callable], instruction: str, 
                 output_structure: Optional[Type[BaseModel]] = None, keep_alive_state: bool = False):
        super().__init__(agent_name, output_structure, keep_alive_state=keep_alive_state)
        self.llm = llm_client
        self.instruction = instruction
        
        self.tool_manager = ToolManager()
        for tool_func in tools:
            self.tool_manager.register(tool_func)
            
        logger.debug(f"LLMAgent '{agent_name}' initialized with tools: {[t.__name__ for t in tools]}")

    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Generates JSON Schema definitions for the agent's tools.
        This is used to inform the LLM about the available tools and their parameters.
        """
        definitions = []
        for tool_name, tool_func in self.tool_manager.tools.items():
            definitions.append(self._create_tool_definition(tool_name, tool_func))
        return definitions

    def _create_tool_definition(self, tool_name: str, tool_func: Callable) -> Dict[str, Any]:
        """Creates a JSON Schema definition for a single tool."""
        sig = inspect.signature(tool_func)
        docstring = inspect.getdoc(tool_func)
        
        description = ""
        if docstring:
            description = docstring.split('\n')[0]

        parameters = self._create_tool_parameters(sig)

        return {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": description,
                "parameters": parameters,
            },
        }

    def _create_tool_parameters(self, sig: inspect.Signature) -> Dict[str, Any]:
        """Creates the JSON Schema parameters for a tool's signature."""
        parameters = {
            "type": "object",
            "properties": {},
            "required": [],
        }
        
        for name, param in sig.parameters.items():
            param_type = self._get_param_type(param)
            
            parameters["properties"][name] = {
                "type": param_type,
                "description": f"Parameter '{name}' for the tool.",
            }
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(name)
        
        return parameters

    def _get_param_type(self, param: inspect.Parameter) -> str:
        """Returns the JSON schema type for a given parameter."""
        if param.annotation is int:
            return "integer"
        if param.annotation is float:
            return "number"
        if param.annotation is bool:
            return "boolean"
        return "string"

    async def execute(self, state: SessionState) -> AgentResponse:
        logger.info(f"--- Executing LLMAgent: {self.agent_name} ---")
        
        instruction = self.instruction
        tool_definitions = self._get_tool_definitions()

        if self.output_structure:
            schema = self.output_structure.model_json_schema()
            structured_output_tool = {
                "type": "function",
                "function": {
                    "name": "structured_output",
                    "description": "Your final response MUST be in this structured format.",
                    "parameters": schema,
                },
            }
            tool_definitions.append(structured_output_tool)
            instruction += "\n\nYour final answer MUST be in the format of the 'structured_output' tool."

        llm_history = [ChatMessage(role="system", content=instruction)] + state.history

        logger.debug(f"[{self.agent_name}] Calling LLM with tools...")
        llm_response = await self.llm.generate(
            llm_history, 
            tool_definitions
        )

        if isinstance(llm_response, dict) and "tool_calls" in llm_response:
            logger.debug(f"[{self.agent_name}] Received tool_calls: {llm_response}")
            
            for tool_call in llm_response["tool_calls"]:
                func_name = tool_call.get("function", {}).get("name")
                func_args = tool_call.get("function", {}).get("arguments", {})

                if not func_name:
                    logger.warning("LLM response contained empty tool call. Skipping.")
                    continue

                if func_name == "structured_output":
                    logger.success(f"[{self.agent_name}] Received structured output.")
                    structured_data = self.output_structure(**func_args)
                    state.add_message(role="agent", content=f"Structured output generated: {structured_data.model_dump_json()}")
                    state.data["last_agent_response"] = structured_data # Store structured data
                    return AgentResponse(status="success", final_content=structured_data)

                logger.info(f"[{self.agent_name}] Parsed tool call. Name: {func_name}, Args: {func_args}")
                state.add_message(role="agent", content=f"Calling tool: {func_name}({json.dumps(func_args)})")
                
                tool_result = await self.tool_manager.execute_tool(func_name, **func_args)
                
                state.add_message(role="tool", content=str(tool_result))
                state.data["last_tool_result"] = tool_result
            
            logger.debug(f"[{self.agent_name}] Re-running after tool call(s)...")
            return await self.execute(state)
        
        elif isinstance(llm_response, str):
            logger.success(f"[{self.agent_name}] Received final response.")
            state.add_message(role="agent", content=llm_response)
            state.data["last_agent_response"] = llm_response
            return AgentResponse(status="success", final_content=llm_response)
        
        else:
            logger.error(f"[{self.agent_name}] Received invalid response from LLM: {llm_response}")
            return AgentResponse(status="error", final_content="Invalid LLM response.")