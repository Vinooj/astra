import pytest
from unittest.mock import AsyncMock, MagicMock
from astra_framework.agents.parallel_agent import ParallelAgent
from astra_framework.core.agent import BaseAgent
from astra_framework.core.state import SessionState
from astra_framework.core.models import AgentResponse
from pydantic import BaseModel
from typing import Any

class MockChildAgent(BaseAgent):
    def __init__(self, agent_name: str, response_content: Any):
        super().__init__(agent_name)
        self._response_content = response_content

    async def execute(self, state: SessionState) -> AgentResponse:
        # Simulate some work and state modification (though it won't affect the parent's state)
        state.data[self.agent_name] = self._response_content
        return AgentResponse(status="success", final_content=self._response_content)

@pytest.fixture
def session_state():
    return SessionState(session_id="test_session")

@pytest.mark.asyncio
async def test_parallel_agent_execution(session_state):
    child1 = MockChildAgent("Child1", "result1")
    child2 = MockChildAgent("Child2", "result2")
    child3 = MockChildAgent("Child3", "result3")

    agent = ParallelAgent(agent_name="TestParallelAgent", children=[child1, child2, child3])

    # Initial state should not be modified by children
    initial_state_data = dict(session_state.data)
    initial_history = list(session_state.history)

    response = await agent.execute(session_state)

    assert response.status == "success"
    assert response.final_content == ["result1", "result2", "result3"]

    # Verify that the original state was not modified by child agents
    assert session_state.data == initial_state_data
    assert session_state.history == initial_history

@pytest.mark.asyncio
async def test_parallel_agent_with_failing_child(session_state):
    class FailingChildAgent(BaseAgent):
        def __init__(self, agent_name: str):
            super().__init__(agent_name)
        async def execute(self, state: SessionState) -> AgentResponse:
            raise ValueError("Child agent failed")

    child1 = MockChildAgent("Child1", "result1")
    failing_child = FailingChildAgent("FailingChild")
    child3 = MockChildAgent("Child3", "result3")

    agent = ParallelAgent(agent_name="TestParallelAgent", children=[child1, failing_child, child3])

    response = await agent.execute(session_state)

    assert response.status == "success" # Parallel agent itself should not fail if one child fails
    assert response.final_content[0] == "result1"
    assert response.final_content[1] is None # Failing child's result should be None
    assert response.final_content[2] == "result3"
