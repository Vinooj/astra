from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union
from astra_framework.core.state import ChatMessage

class BaseLLMClient(ABC):
    """
    Abstract base class for all LLM clients.

    This class defines the common interface for all LLM clients in the Astra
    framework. It ensures that any LLM client can be used interchangeably by
    the `LLMAgent`.
    """

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
