from loguru import logger
from typing import List
from pydantic import BaseModel
from astra_framework.core.agent import BaseAgent
from astra_framework.core.state import SessionState, ChatMessage
from astra_framework.core.models import AgentResponse

class SequentialAgent(BaseAgent):
    """
    (Composite & Chain of Responsibility Pattern)
    Executes a list of child agents in order, passing and modifying the state.
    """
    def __init__(self, agent_name: str, children: List[BaseAgent], keep_alive_state: bool = False):
        super().__init__(agent_name, keep_alive_state=keep_alive_state)
        self.children = children
        logger.debug(f"SequentialAgent '{agent_name}' initialized with {len(children)} children.")

    async def execute(self, state: SessionState) -> AgentResponse:
        """Executes the agent's logic."""
        logger.info(f"--- Executing SequentialAgent: {self.agent_name} ---")
        final_response = None
        for i, agent in enumerate(self.children):
            logger.info(f"[{self.agent_name}] Running child {i+1}/{len(self.children)}: {agent.agent_name}")
            
            response = await agent.execute(state)
            final_response = response

            self._handle_child_response(agent, response, state)

            logger.success(f"[{self.agent_name}] Child {agent.agent_name} finished.")
        
        logger.success(f"SequentialAgent '{self.agent_name}' finished.")
        return final_response

    def _handle_child_response(self, agent: BaseAgent, response: AgentResponse, state: SessionState):
        """Handles the response from a child agent."""
        if isinstance(response.final_content, BaseModel):
            content_to_add = response.final_content.model_dump_json()
            role_to_add = "user" # Structured output is often treated as a new prompt for the next agent
        else:
            content_to_add = str(response.final_content)
            role_to_add = "agent" # Unstructured output is typically an agent's response

        if not self.keep_alive_state:
            logger.debug(f"Child {agent.agent_name} returned a response. Pruning context for next agent.")
            state.history.clear()
            state.add_message(role=role_to_add, content=content_to_add)
        else:
            logger.debug(f"Child {agent.agent_name} returned a response. Not pruning context.")
            state.add_message(role=role_to_add, content=content_to_add)