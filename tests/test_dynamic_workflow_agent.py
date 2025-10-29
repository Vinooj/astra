import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from astra_framework.agents.dynamic_workflow_agent import DynamicWorkflowAgent
from astra_framework.core.state import SessionState, ChatMessage
from astra_framework.core.models import AgentResponse
from astra_framework.core.workflow_models import WorkflowPlan, AgentConfig
from astra_framework.agents.llm_agent import LLMAgent
from astra_framework.agents.sequential_agent import SequentialAgent
from astra_framework.agents.parallel_agent import ParallelAgent
from astra_framework.agents.loop_agent import LoopAgent
from astra_framework.services.ollama_client import OllamaClient
from astra_framework.core.tool import ToolManager
from pydantic import BaseModel
from typing import List, Callable, Dict, Any

class MockOllamaClient(OllamaClient):
    def __init__(self):
        super().__init__(model="test_model")
        self.generate = AsyncMock()

class MockToolManager(ToolManager):
    def __init__(self):
        super().__init__()
        self.execute_tool = AsyncMock()
        self.tools = {}

def mock_search_tool(query: str) -> str:
    return f"Search results for {query}"

class MockOutputStructure(BaseModel):
    value: str

@pytest.fixture
def dynamic_workflow_agent():
    ollama_client = MockOllamaClient()
    agent = DynamicWorkflowAgent(
        agent_name="TestDynamicPlanner",
        llm_client=ollama_client,
        tools=[mock_search_tool],
        instruction="Test instruction for DWA"
    )
    # Register dummy output structures for the DWA's internal LLM to reference
    agent.register_output_structure("MockOutputStructure", MockOutputStructure)
    return agent

@pytest.mark.asyncio
async def test_dynamic_workflow_agent_simple_llm_plan(dynamic_workflow_agent):
    # Mock the DWA's internal LLM to return a simple LLMAgent plan directly
    dynamic_workflow_agent.llm.generate.return_value = {
        "message": {
            "tool_calls": [
                {
                    "function": {
                        "name": "create_workflow_plan",
                        "arguments": {
                            "main_topic": "Test Topic",
                            "workflow_description": "Simple LLM Agent workflow",
                            "root_agent": {
                                "agent_type": "LLMAgent",
                                "agent_name": "SimpleLLMAgent",
                                "instruction": "Respond to user",
                                "output_structure": None,
                                "tools": [],
                                "keep_alive_state": False
                            }
                        }
                    }
                }
            ]
        }
    }
    
    state = SessionState(session_id="test_session")
    state.add_message(role="user", content="Create a simple LLM agent to respond to me.")

    # Mock the execute method of the dynamically created LLMAgent
    with patch('astra_framework.agents.llm_agent.LLMAgent.execute', new_callable=AsyncMock) as mock_llm_agent_execute:
        mock_llm_agent_execute.return_value = AgentResponse(status="success", final_content="LLM Agent executed successfully")
        
        response = await dynamic_workflow_agent.execute(state)

        assert response.status == "success"
        assert response.final_content == "LLM Agent executed successfully"
        mock_llm_agent_execute.assert_called_once()

@pytest.mark.asyncio
async def test_dynamic_workflow_agent_sequential_plan(dynamic_workflow_agent):
    # Mock the DWA's internal LLM to return a SequentialAgent plan directly
    dynamic_workflow_agent.llm.generate.return_value = {
        "message": {
            "tool_calls": [
                {
                    "function": {
                        "name": "create_workflow_plan",
                        "arguments": {
                            "main_topic": "Sequential Test",
                            "workflow_description": "Sequential workflow test",
                            "root_agent": {
                                "agent_type": "SequentialAgent",
                                "agent_name": "TestSequence",
                                "children": [
                                    {
                                        "agent_type": "LLMAgent",
                                        "agent_name": "ChildLLM1",
                                        "instruction": "First step",
                                        "tools": [],
                                        "keep_alive_state": False
                                    },
                                    {
                                        "agent_type": "LLMAgent",
                                        "agent_name": "ChildLLM2",
                                        "instruction": "Second step",
                                        "tools": [],
                                        "keep_alive_state": False
                                    }
                                ],
                                "keep_alive_state": True
                            }
                        }
                    }
                }
            ]
        }
    }
    
    state = SessionState(session_id="test_session")
    state.add_message(role="user", content="Create a sequential workflow.")

    # Mock the execute method of the dynamically created SequentialAgent
    with patch('astra_framework.agents.sequential_agent.SequentialAgent.execute', new_callable=AsyncMock) as mock_sequential_agent_execute:
        mock_sequential_agent_execute.return_value = AgentResponse(status="success", final_content="Sequential Agent executed successfully")
        
        response = await dynamic_workflow_agent.execute(state)

        assert response.status == "success"
        assert response.final_content == "Sequential Agent executed successfully"
        mock_sequential_agent_execute.assert_called_once()

@pytest.mark.asyncio
async def test_dynamic_workflow_agent_invalid_plan(dynamic_workflow_agent):
    # Mock the DWA's internal LLM to return an invalid plan (e.g., unknown agent type)
    dynamic_workflow_agent.llm.generate.return_value = {
        "message": {
            "tool_calls": [
                {
                    "function": {
                        "name": "create_workflow_plan",
                        "arguments": {
                            "main_topic": "Invalid Test",
                            "workflow_description": "Invalid workflow test",
                            "root_agent": {
                                "agent_type": "UnknownAgent", # Invalid agent type
                                "agent_name": "InvalidAgent",
                                "instruction": "Should fail"
                            }
                        }
                    }
                }
            ]
        }
    }
    
    state = SessionState(session_id="test_session")
    state.add_message(role="user", content="Create an invalid workflow.")

    response = await dynamic_workflow_agent.execute(state)

    assert response.status == "error"
    assert "Failed to build or execute dynamic workflow" in response.final_content
    assert "Unknown agent type: UnknownAgent" in response.final_content
