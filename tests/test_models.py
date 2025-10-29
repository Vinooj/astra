from astra_framework.core.models import AgentResponse, ToolCall

def test_agent_response_creation():
    response = AgentResponse(status="success", final_content="test content")
    assert response.status == "success"
    assert response.final_content == "test content"

def test_tool_call_creation():
    tool_call = ToolCall(name="test_tool", args={"arg1": "value1"})
    assert tool_call.name == "test_tool"
    assert tool_call.args == {"arg1": "value1"}
