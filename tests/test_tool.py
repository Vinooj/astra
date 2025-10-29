import pytest
from astra_framework.core.tool import ToolManager

def add(a: int, b: int) -> int:
    return a + b

async def async_add(a: int, b: int) -> int:
    return a + b

@pytest.fixture
def tool_manager():
    return ToolManager()

def test_register_tool(tool_manager):
    tool_manager.register(add)
    assert "add" in tool_manager.tools
    assert tool_manager.tools["add"] == add

@pytest.mark.asyncio
async def test_execute_sync_tool(tool_manager):
    tool_manager.register(add)
    result = await tool_manager.execute_tool("add", a=1, b=2)
    assert result == 3

@pytest.mark.asyncio
async def test_execute_async_tool(tool_manager):
    tool_manager.register(async_add)
    result = await tool_manager.execute_tool("async_add", a=1, b=2)
    assert result == 3

@pytest.mark.asyncio
async def test_execute_unknown_tool(tool_manager):
    result = await tool_manager.execute_tool("unknown", a=1, b=2)
    assert "Error: Tool 'unknown' not found." in result
