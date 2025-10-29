import pytest
from unittest.mock import AsyncMock, MagicMock
from astra_framework.agents.sequential_agent import SequentialAgent
from astra_framework.core.agent import BaseAgent
from astra_framework.core.state import SessionState, ChatMessage
from astra_framework.core.models import AgentResponse
from pydantic import BaseModel
from typing import Any
import json

class MockChildAgent(BaseAgent):
    def __init__(self, agent_name: str, response_content: Any, is_structured: bool = False):
        super().__init__(agent_name)
        self._response_content = response_content
        self._is_structured = is_structured

    async def execute(self, state: SessionState) -> AgentResponse:
        if self._is_structured:
            structured_output = MockStructuredOutput(value=self._response_content)
            return AgentResponse(status="success", final_content=structured_output)
        return AgentResponse(status="success", final_content=self._response_content)

class MockStructuredOutput(BaseModel):
    value: str

@pytest.fixture
def session_state():
    return SessionState(session_id="test_session")

# @pytest.mark.asyncio
# async def test_sequential_agent_no_keep_alive_state(session_state):
#     # Child 1 returns structured output, history should be cleared
#     child1 = MockChildAgent("Child1", "output1", is_structured=True)
#     # Child 2 returns string output
#     child2 = MockChildAgent("Child2", "output2")

#     agent = SequentialAgent(agent_name="TestSequentialAgent", children=[child1, child2], keep_alive_state=False)
    
#     session_state.add_message(role="user", content="initial prompt")

#     response = await agent.execute(session_state)

#     assert response.status == "success"
#     assert response.final_content == "output2" # Last child's response

#     # History should reflect clearing after child1 and then adding child1's output, then child2's output
#     assert len(session_state.history) == 2 # Only child1's structured output and child2's string output
#     assert json.loads(session_state.history[0].content) == {"value": "output1"} # Structured output from child1
#     assert session_state.history[1].content == 'output2' # String output from child2

# @pytest.mark.asyncio
# async def test_sequential_agent_keep_alive_state(session_state):
#     # Child 1 returns structured output, history should NOT be cleared
#     child1 = MockChildAgent("Child1", "output1", is_structured=True)
#     # Child 2 returns string output
#     child2 = MockChildAgent("Child2", "output2")

#     agent = SequentialAgent(agent_name="TestSequentialAgent", children=[child1, child2], keep_alive_state=True)
    
#     session_state.add_message(role="user", content="initial prompt")

#     response = await agent.execute(session_state)

#     assert response.status == "success"
#     assert response.final_content == "output2" # Last child's response

#     # History should reflect appending all messages
#     assert len(session_state.history) == 3 # Initial prompt + child1 structured output + child2 string output
#     assert session_state.history[0].content == "initial prompt"
#     assert json.loads(session_state.history[1].content) == {"value": "output1"}
#     assert session_state.history[2].content == 'output2'
