import asyncio
from core.agent import BaseAgent
from core.state import SessionState
from core.models import AgentResponse
from typing import List

class ParallelAgent(BaseAgent):
    """
    Implements the Composite pattern for parallel execution.
    Executes all child agents concurrently.
    """
    def __init__(self, children: List[BaseAgent]):
        self.children = children

    async def execute(self, state: SessionState) -> AgentResponse:
        # Run all child agents concurrently
        tasks = [agent.execute(state) for agent in self.children]
        results = await asyncio.gather(*tasks)
        
        # Add a summary of parallel execution to the state
        summary = f"Executed {len(results)} tasks in parallel."
        state.add_message(role="agent", content=summary)
        
        # Store individual results on the blackboard for later agents
        state.data["parallel_results"] = [res.final_content for res in results]
        
        return AgentResponse(status="success", final_content=summary)