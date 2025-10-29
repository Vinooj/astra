import pytest
from astra_framework.manager import WorkflowManager
from astra_framework.core.agent import BaseAgent
from astra_framework.core.state import SessionState
from astra_framework.core.models import AgentResponse

class DummyAgent(BaseAgent):
    async def execute(self, state: SessionState) -> AgentResponse:
        return AgentResponse(status="success", final_content="dummy response")

@pytest.fixture
def manager():
    return WorkflowManager()

def test_register_workflow(manager):
    agent = DummyAgent(agent_name="dummy")
    manager.register_workflow("test_workflow", agent)
    assert "test_workflow" in manager.workflows
    assert manager.workflows["test_workflow"] == agent

def test_create_session(manager):
    session_id = manager.create_session()
    assert session_id in manager.sessions
    assert isinstance(manager.sessions[session_id], SessionState)

@pytest.mark.asyncio
async def test_run_workflow(manager):
    agent = DummyAgent(agent_name="dummy")
    manager.register_workflow("test_workflow", agent)
    session_id = manager.create_session()
    response = await manager.run("test_workflow", session_id, "test prompt")
    assert response.status == "success"
    assert response.final_content == "dummy response"

@pytest.mark.asyncio
async def test_run_unknown_workflow(manager):
    session_id = manager.create_session()
    response = await manager.run("unknown_workflow", session_id, "test prompt")
    assert response.status == "error"
    assert "Workflow 'unknown_workflow' not found." in response.final_content
