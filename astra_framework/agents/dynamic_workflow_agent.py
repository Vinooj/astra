from loguru import logger
from typing import List, Callable, Dict, Any, Optional, Type
import inspect
import json
from pydantic import BaseModel, ValidationError

from astra_framework.core.agent import BaseAgent
from astra_framework.core.state import SessionState, ChatMessage
from astra_framework.core.models import AgentResponse
from astra_framework.services.ollama_client import OllamaClient
from astra_framework.core.tool import ToolManager

from astra_framework.agents.llm_agent import LLMAgent
from astra_framework.agents.sequential_agent import SequentialAgent
from astra_framework.agents.parallel_agent import ParallelAgent
from astra_framework.agents.loop_agent import LoopAgent

from astra_framework.core.workflow_models import AgentConfig, WorkflowPlan

class DynamicWorkflowAgent(LLMAgent):
    """
    A meta-agent that uses an LLM to dynamically create and execute workflows.
    It takes a high-level user prompt, generates a structured workflow plan,
    and then instantiates and runs the agents defined in that plan.
    """
    def __init__(self, agent_name: str, llm_client: OllamaClient, 
                 tools: List[Callable], instruction: str, 
                 output_structure: Optional[Type[BaseModel]] = WorkflowPlan,
                 keep_alive_state: bool = False):
        super().__init__(agent_name, llm_client, tools, instruction, output_structure, keep_alive_state)
        self.available_agents = {
            "LLMAgent": LLMAgent,
            "SequentialAgent": SequentialAgent,
            "ParallelAgent": ParallelAgent,
            "LoopAgent": LoopAgent,
        }
        self.available_tools = {tool.__name__: tool for tool in tools}
        self.available_output_structures = {}

    def register_output_structure(self, name: str, pydantic_model: Type[BaseModel]):
        self.available_output_structures[name] = pydantic_model

    def register_tool(self, tool_func: Callable):
        self.available_tools[tool_func.__name__] = tool_func

    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        # Override to provide tools for the LLM to plan with
        definitions = super()._get_tool_definitions()
        # Add a tool for defining the workflow structure itself
        definitions.append({
            "type": "function",
            "function": {
                "name": "create_workflow_plan",
                "description": "Create a structured workflow plan to achieve the user's goal.",
                "parameters": WorkflowPlan.model_json_schema(),
            },
        })
        return definitions

    async def execute(self, state: SessionState) -> AgentResponse:
        logger.info(f"--- Executing DynamicWorkflowAgent: {self.agent_name} ---")

        instruction = self.instruction
        tool_definitions = self._get_tool_definitions()

        llm_history = [ChatMessage(role="system", content=instruction)] + state.history

        logger.debug(f"[{self.agent_name}] Calling LLM to generate workflow plan...")
        llm_response = await self.llm.generate(
            llm_history, 
            tool_definitions
        )

        if not (isinstance(llm_response, dict) and "message" in llm_response and "tool_calls" in llm_response["message"]):
            logger.error(f"[{self.agent_name}] LLM did not return a tool call for workflow planning: {llm_response}")
            return AgentResponse(status="error", final_content="LLM did not return a tool call for workflow planning.")

        try:
            tool_call = llm_response["message"]["tool_calls"][0]
            func_name = tool_call.get("function", {}).get("name")
            func_args = tool_call.get("function", {}).get("arguments", {})

            if func_name != "create_workflow_plan":
                logger.error(f"[{self.agent_name}] LLM called unexpected tool: {func_name}")
                return AgentResponse(status="error", final_content=f"LLM called unexpected tool: {func_name}")

            try:
                workflow_plan = WorkflowPlan.model_validate(func_args)
            except ValidationError as e:
                # Re-raise as ValueError to match the expected error message in tests
                for error in e.errors():
                    if error["loc"] == ("root_agent", "agent_type") and error["type"] == "literal_error":
                        raise ValueError(f"Unknown agent type: {func_args.get('root_agent', {}).get('agent_type')}") from e
                raise ValueError(f"Invalid workflow plan: {e}") from e

            logger.info(f"Generated Workflow Plan: {workflow_plan.workflow_description}")
            
            root_agent_instance = self._build_agent_from_config(workflow_plan.root_agent)
            logger.info(f"Dynamically built root agent: {root_agent_instance.agent_name}")

            # Execute the dynamically built workflow
            dynamic_workflow_response = await root_agent_instance.execute(state)
            return dynamic_workflow_response
        except Exception as e:
            logger.error(f"Error building or executing dynamic workflow: {e}")
            return AgentResponse(status="error", final_content=f"Failed to build or execute dynamic workflow: {e}")

    def _build_agent_from_config(self, agent_config: AgentConfig) -> BaseAgent:
        """Recursively builds an agent instance from its configuration."""
        agent_class = self.available_agents.get(agent_config.agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_config.agent_type}")

        kwargs = {"agent_name": agent_config.agent_name, "keep_alive_state": agent_config.keep_alive_state}

        if agent_config.agent_type == "LLMAgent":
            kwargs["llm_client"] = self.llm # Use the DWA's LLM client
            kwargs["instruction"] = agent_config.instruction
            kwargs["tools"] = [self.available_tools[t] for t in agent_config.tools] if agent_config.tools else []
            if agent_config.output_structure:
                kwargs["output_structure"] = self.available_output_structures.get(agent_config.output_structure)
                if not kwargs["output_structure"]:
                    raise ValueError(f"Unknown output structure: {agent_config.output_structure}")
        elif agent_config.agent_type in ["SequentialAgent", "ParallelAgent"]:
            if not agent_config.children:
                raise ValueError(f"{agent_config.agent_type} requires children.")
            kwargs["children"] = [self._build_agent_from_config(child_config) for child_config in agent_config.children]
        elif agent_config.agent_type == "LoopAgent":
            if not agent_config.child:
                raise ValueError(f"LoopAgent requires a child.")
            kwargs["child"] = self._build_agent_from_config(agent_config.child)
            kwargs["max_loops"] = agent_config.max_loops
            # For exit_condition, we'd need a way to dynamically load/create callables
            # For simplicity in this demo, we'll assume a pre-defined exit condition or a simple one.
            # A more advanced implementation might use a registry of exit conditions.
            if agent_config.exit_condition:
                # This part would need careful design for a real system
                # For now, let's assume a simple always-true or always-false for demo
                pass # Placeholder for dynamic exit condition loading

        return agent_class(**kwargs)
