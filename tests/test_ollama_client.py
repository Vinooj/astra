import pytest
from unittest.mock import AsyncMock, MagicMock
from astra_framework.services.ollama_client import OllamaClient
from astra_framework.core.state import ChatMessage
from typing import List, Dict, Any, Union
import httpx # Import httpx for ConnectError

@pytest.fixture
def ollama_client():
    client = OllamaClient(model="test_model")
    client.client = AsyncMock() # Mock the AsyncClient
    return client

@pytest.mark.asyncio
async def test_ollama_client_generate_text_response(ollama_client):
    ollama_client.client.chat.return_value = {
        "message": {"content": "Hello from Ollama!"}
    }
    history = [ChatMessage(role="user", content="hi")]
    tools = []
    response = await ollama_client.generate(history, tools)
    assert response == "Hello from Ollama!"
    ollama_client.client.chat.assert_called_once()

@pytest.mark.asyncio
async def test_ollama_client_generate_tool_call(ollama_client):
    ollama_client.client.chat.return_value = {
        "message": {
            "tool_calls": [
                {"function": {"name": "test_tool", "arguments": {"arg1": "value1"}}}
            ]
        }
    }
    history = [ChatMessage(role="user", content="use tool")]
    tools = [{"name": "test_tool"}]
    response = await ollama_client.generate(history, tools)
    assert response == {"tool_calls": [{"function": {"name": "test_tool", "arguments": {"arg1": "value1"}}}]}
    ollama_client.client.chat.assert_called_once()

@pytest.mark.asyncio
async def test_ollama_client_generate_connection_error(ollama_client):
    ollama_client.client.chat.side_effect = httpx.ConnectError("Connection refused")
    history = [ChatMessage(role="user", content="hi")]
    tools = []
    response = await ollama_client.generate(history, tools)
    assert "Error: Could not connect to Ollama." in response

@pytest.mark.asyncio
async def test_ollama_client_generate_unexpected_error(ollama_client):
    ollama_client.client.chat.side_effect = Exception("Something went wrong")
    history = [ChatMessage(role="user", content="hi")]
    tools = []
    response = await ollama_client.generate(history, tools)
    assert "An unexpected error occurred: Something went wrong" in response
