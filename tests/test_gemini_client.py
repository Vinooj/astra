import pytest
from astra_framework.services.gemini_client import GeminiClient
from astra_framework.core.state import ChatMessage
from typing import List, Dict, Any, Union

@pytest.fixture
def gemini_client():
    return GeminiClient(model="test_model")

def test_gemini_client_instantiation(gemini_client):
    assert gemini_client.model == "test_model"

@pytest.mark.asyncio
async def test_gemini_client_generate(gemini_client):
    history = [ChatMessage(role="user", content="hello")]
    tools = []
    response = await gemini_client.generate(history, tools)
    assert response == "This is a placeholder response from GeminiClient."
