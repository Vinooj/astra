import pytest
from unittest.mock import AsyncMock, MagicMock
from astra_framework.agents.llm_agent import LLMAgent
from astra_framework.core.state import SessionState, ChatMessage
from astra_framework.core.models import AgentResponse
from astra_framework.services.ollama_client import OllamaClient
from astra_framework.core.tool import ToolManager
from pydantic import BaseModel
from typing import List

class MockOllamaClient(OllamaClient):
    def __init__(self):
        super().__init__(model="test_model")
        self.generate = AsyncMock()

class MockToolManager(ToolManager):
    def __init__(self):
        super().__init__()
        self.execute_tool = AsyncMock()

class MockOutputStructure(BaseModel):
    value: str

@pytest.fixture
def llm_agent():
    ollama_client = MockOllamaClient()
    
    mock_tool_manager = MagicMock(spec=ToolManager)
    mock_tool_manager.register = MagicMock()
    mock_tool_manager.execute_tool = AsyncMock(return_value="tool_result")
    mock_tool_manager.tools = {}
    
    agent = LLMAgent(
        agent_name="TestLLMAgent",
        llm_client=ollama_client,
        tools=[],
        instruction="Test instruction",
        output_structure=MockOutputStructure
    )
    agent.tool_manager = mock_tool_manager
    yield agent

@pytest.mark.asyncio
async def test_llm_agent_execute_structured_output(llm_agent):
    llm_agent.llm.generate.return_value = {
        "tool_calls": [
            {
                "function": {
                    "name": "structured_output",
                    "arguments": {"value": "test_output"}
                }
            }
        ]
    }
    state = SessionState(session_id="test_session")
    response = await llm_agent.execute(state)

    assert response.status == "success"
    assert isinstance(response.final_content, MockOutputStructure)
    assert response.final_content.value == "test_output"
    assert len(state.history) == 1 # Agent message
    assert state.data["last_agent_response"].value == "test_output"

@pytest.mark.asyncio
async def test_llm_agent_execute_tool_call(llm_agent):
    llm_agent.llm.generate.side_effect = [
        {
            "tool_calls": [
                {
                    "function": {
                        "name": "test_tool",
                        "arguments": {"arg1": "value1"}
                    }
                }
            ]
        },
        "final text response"
    ]
    state = SessionState(session_id="test_session")
    response = await llm_agent.execute(state)

    llm_agent.tool_manager.execute_tool.assert_called_once_with("test_tool", arg1="value1")
    assert response.status == "success"
    assert response.final_content == "final text response"
    assert len(state.history) == 3 # Agent (tool call), tool, agent (final response)
    assert state.data["last_tool_result"] == "tool_result"
    assert state.data["last_agent_response"] == "final text response"

@pytest.mark.asyncio
async def test_llm_agent_execute_string_response(llm_agent):
    llm_agent.llm.generate.return_value = "simple text response"
    state = SessionState(session_id="test_session")
    response = await llm_agent.execute(state)

    assert response.status == "success"
    assert response.final_content == "simple text response"
    assert len(state.history) == 1 # Agent message
    assert state.data["last_agent_response"] == "simple text response"

@pytest.mark.asyncio
async def test_llm_agent_execute_invalid_response(llm_agent):
    llm_agent.llm.generate.return_value = 123 # Invalid response type
    state = SessionState(session_id="test_session")
    response = await llm_agent.execute(state)

    assert response.status == "error"
    assert "Invalid LLM response." in response.final_content
