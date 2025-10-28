import asyncio
from loguru import logger
from typing import List
from copy import deepcopy
from astra_framework.core.agent import BaseAgent
from astra_framework.core.state import SessionState
from astra_framework.core.models import AgentResponse

class ParallelAgent(BaseAgent):
    """
    (Composite Pattern)
    Executes a list of child agents in parallel and aggregates their responses.
    Each child agent receives a deep copy of the state to ensure isolation
    and prevent race conditions.
    """
    def __init__(self, agent_name: str, children: List[BaseAgent], keep_alive_state: bool = False):
        super().__init__(agent_name, keep_alive_state=keep_alive_state)
        self.children = children
        logger.debug(f"ParallelAgent '{agent_name}' initialized with {len(children)} children.")

    async def execute(self, state: SessionState) -> AgentResponse:
        logger.info(f"--- Executing ParallelAgent: {self.agent_name} ---")

        # Create deep copies of the state for each child to run in isolation
        tasks = [child.execute(deepcopy(state)) for child in self.children]
        
        child_responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate the final content from each child response
        aggregated_content = []
        for i, res in enumerate(child_responses):
            if isinstance(res, Exception):
                logger.error(f"Child agent {self.children[i].agent_name} failed with exception: {res}")
                aggregated_content.append(None) # Or some other indicator of failure
            else:
                aggregated_content.append(res.final_content)

        # The main state is not modified by the children, as they operate on copies.
        # The aggregated content is returned for a subsequent agent to process.
        logger.success(f"--- ParallelAgent '{self.agent_name}' finished ---")
        return AgentResponse(status="success", final_content=aggregated_content)
