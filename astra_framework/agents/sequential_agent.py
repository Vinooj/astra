from loguru import logger
from typing import List
from pydantic import BaseModel
from astra_framework.core.agent import BaseAgent
from astra_framework.core.state import SessionState
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
        logger.info(f"--- Executing SequentialAgent: {self.agent_name} ---")
        final_response = None
        for i, agent in enumerate(self.children):
            logger.info(f"[{self.agent_name}] Running child {i+1}/{len(self.children)}: {agent.agent_name}")
            
            response = await agent.execute(state)
            final_response = response

            # If a structured output is returned, prune the context for the next agent
            if isinstance(response.final_content, BaseModel):
                if not self.keep_alive_state:
                    logger.debug(f"Child {agent.agent_name} returned a structured output. Pruning context for next agent.")
                    # Modify the state in-place by clearing the history and adding the new prompt
                    state.history.clear()
                    new_prompt = response.final_content.model_dump_json()
                    state.add_message(role="user", content=new_prompt)
                else:
                    logger.debug(f"Child {agent.agent_name} returned a structured output, but keep_alive_state is True. Not pruning context.")
                    new_prompt = response.final_content.model_dump_json()
                    state.add_message(role="user", content=new_prompt)

            logger.success(f"[{self.agent_name}] Child {agent.agent_name} finished.")
        
        logger.success(f"SequentialAgent '{self.agent_name}' finished.")
        return final_response