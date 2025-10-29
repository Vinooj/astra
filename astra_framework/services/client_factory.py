from .base_client import BaseLLMClient
from .gemini_client import GeminiClient
from .ollama_client import OllamaClient

class LLMClientFactory:
    """A factory for creating LLM clients."""

    @staticmethod
    def create_client(client_type: str, model: str, **kwargs) -> BaseLLMClient:
        """
        Creates an LLM client.

        Args:
            client_type: The type of client to create (e.g., "gemini", "ollama").
            model: The model to use for the client.
            **kwargs: Additional keyword arguments for the client.

        Returns:
            An instance of the specified LLM client.
        """
        if client_type == "gemini":
            return GeminiClient(model=model, **kwargs)
        elif client_type == "ollama":
            return OllamaClient(model=model, **kwargs)
        else:
            raise ValueError(f"Unknown client type: {client_type}")
