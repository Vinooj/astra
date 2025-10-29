import pytest
from astra_framework.core.agent import BaseAgent
from astra_framework.core.state import SessionState
from astra_framework.core.models import AgentResponse

class DummyAgent(BaseAgent):
    async def execute(self, state: SessionState) -> AgentResponse:
        return AgentResponse(status="success", final_content="dummy response")

def test_base_agent_creation():
    agent = DummyAgent(agent_name="dummy")
    assert agent.agent_name == "dummy"
    assert not agent.keep_alive_state
