import pytest
from unittest.mock import AsyncMock, MagicMock
from astra_framework.agents.loop_agent import LoopAgent
from astra_framework.core.agent import BaseAgent
from astra_framework.core.state import SessionState, ChatMessage
from astra_framework.core.models import AgentResponse
from pydantic import BaseModel
from typing import Any, List
import json

class MockChildAgent(BaseAgent):
    def __init__(self, agent_name: str, responses: List[Any]):
        super().__init__(agent_name)
        self._responses = responses
        self._call_count = 0

    async def execute(self, state: SessionState) -> AgentResponse:
        response_content = self._responses[self._call_count]
        self._call_count += 1
        # The loop agent expects the child to put its structured output into the history as a user message
        if isinstance(response_content, BaseModel):
            state.add_message(role="user", content=response_content.model_dump_json())
        else:
            state.add_message(role="user", content=str(response_content))
        return AgentResponse(status="success", final_content=response_content)

class MockCritiqueResult(BaseModel):
    approved: bool
    feedback: str

@pytest.fixture
def session_state():
    state = SessionState(session_id="test_session")
    state.add_message(role="user", content="initial prompt")
    return state

@pytest.mark.asyncio
async def test_loop_agent_exit_condition_met(session_state):
    # Child agent will return a critique that is approved on the first try
    child_responses = [MockCritiqueResult(approved=True, feedback="Perfect!")]
    child_agent = MockChildAgent("ChildAgent", child_responses)

    def exit_condition(state: SessionState) -> bool:
        last_message = state.history[-1]
        if last_message.role == "user":
            try:
                critique = MockCritiqueResult.model_validate_json(last_message.content)
                return critique.approved
            except Exception:
                return False
        return False

    loop_agent = LoopAgent(
        agent_name="TestLoopAgent",
        child=child_agent,
        max_loops=3,
        exit_condition=exit_condition,
        keep_alive_state=True
    )

    response = await loop_agent.execute(session_state)

    assert response.status == "success"
    assert isinstance(response.final_content, MockCritiqueResult)
    assert response.final_content.approved == True
    assert child_agent._call_count == 1 # Should only run once
    assert len(session_state.history) == 2 # Initial prompt + critique

@pytest.mark.asyncio
async def test_loop_agent_max_loops_reached(session_state):
    # Child agent will always return a critique that is not approved
    child_responses = [
        MockCritiqueResult(approved=False, feedback="Needs more detail."),
        MockCritiqueResult(approved=False, feedback="Still not there."),
        MockCritiqueResult(approved=False, feedback="Give up.")
    ]
    child_agent = MockChildAgent("ChildAgent", child_responses)

    def exit_condition(state: SessionState) -> bool:
        last_message = state.history[-1]
        if last_message.role == "user":
            try:
                critique = MockCritiqueResult.model_validate_json(last_message.content)
                return critique.approved
            except Exception:
                return False
        return False

    loop_agent = LoopAgent(
        agent_name="TestLoopAgent",
        child=child_agent,
        max_loops=2, # Max loops is 2, so it will run twice and then exit
        exit_condition=exit_condition,
        keep_alive_state=True
    )

    response = await loop_agent.execute(session_state)

    assert response.status == "success"
    assert isinstance(response.final_content, MockCritiqueResult)
    assert response.final_content.approved == False
    assert child_agent._call_count == 2 # Should run max_loops times
    assert len(session_state.history) == 4 # Initial prompt + 2 critiques + 2 feedback messages
