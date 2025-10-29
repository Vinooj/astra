import pytest
from astra_framework.services.base_client import BaseLLMClient
from astra_framework.core.state import ChatMessage
from typing import List, Dict, Any, Union

class DummyLLMClient(BaseLLMClient):
    async def generate(self, history: List[ChatMessage], tools: List[Dict[str, Any]]) -> Union[str, Dict[str, Any]]:
        return "dummy response"

def test_base_llm_client_instantiation():
    client = DummyLLMClient()
    assert isinstance(client, BaseLLMClient)

@pytest.mark.asyncio
async def test_base_llm_client_generate():
    client = DummyLLMClient()
    history = [ChatMessage(role="user", content="hello")]
    tools = []
    response = await client.generate(history, tools)
    assert response == "dummy response"
