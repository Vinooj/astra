import pytest
from unittest.mock import MagicMock, patch
from astra_framework.services.tavily_client import TavilyClient
import os

class MockTavilyClient:
    def __init__(self, api_key: str):
        pass
    def search(self, query: str, search_depth: str, max_results: int):
        if "error" in query:
            raise Exception("Tavily API error")
        return {"results": [{"title": "Test Result", "url": "http://test.com"}]}

@pytest.fixture
def tavily_client():
    with patch('astra_framework.services.tavily_client.Tavily', return_value=MockTavilyClient(api_key="test_key")) as mock_tavily_constructor:
        client = TavilyClient(api_key="test_key")
        yield client

def test_tavily_client_init_with_api_key():
    with patch('astra_framework.services.tavily_client.Tavily', return_value=MockTavilyClient(api_key="test_key")):
        client = TavilyClient(api_key="test_key")
        assert client.client is not None

def test_tavily_client_init_without_api_key_env_var():
    # Temporarily unset the environment variable
    original_env = os.environ.get("TAVILY_API_KEY")
    if "TAVILY_API_KEY" in os.environ:
        del os.environ["TAVILY_API_KEY"]
    
    with pytest.raises(ValueError, match="Tavily API key not provided."):
        TavilyClient()
    
    # Restore the environment variable
    if original_env:
        os.environ["TAVILY_API_KEY"] = original_env
    else:
        if "TAVILY_API_KEY" in os.environ:
            del os.environ["TAVILY_API_KEY"]

def test_tavily_client_init_with_api_key_env_var():
    # Temporarily set the environment variable
    original_env = os.environ.get("TAVILY_API_KEY")
    os.environ["TAVILY_API_KEY"] = "env_test_key"
    
    with patch('astra_framework.services.tavily_client.Tavily', return_value=MockTavilyClient(api_key="env_test_key")):
        client = TavilyClient()
        assert client.client is not None
    
    # Restore the environment variable
    if original_env:
        os.environ["TAVILY_API_KEY"] = original_env
    else:
        if "TAVILY_API_KEY" in os.environ:
            del os.environ["TAVILY_API_KEY"]

def test_tavily_client_search_success(tavily_client):
    results = tavily_client.search(query="test query")
    assert len(results) == 1
    assert results[0]["title"] == "Test Result"

def test_tavily_client_search_failure(tavily_client):
    results = tavily_client.search(query="error query")
    assert results == []
