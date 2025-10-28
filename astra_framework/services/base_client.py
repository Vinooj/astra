from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union
from astra_framework.core.state import ChatMessage

class BaseLLMClient(ABC):
    """Abstract base class for all LLM clients."""

    @abstractmethod
    async def generate(self, history: List[ChatMessage], tools: List[Dict[str, Any]]) -> Union[str, Dict[str, Any]]:
        """
        Generates a response from the LLM.

        Args:
            history: A list of ChatMessage objects representing the conversation history.
            tools: A list of tool definitions in JSON Schema format.

        Returns:
            A string containing the text response, or a dictionary
            representing a tool call.
        """
        pass
