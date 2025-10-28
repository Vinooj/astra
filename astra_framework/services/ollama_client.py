from dataclasses import asdict
import httpx
from typing import List, Dict, Any, Union
from loguru import logger
from ollama import AsyncClient
from astra_framework.core.state import ChatMessage
from .base_client import BaseLLMClient


class OllamaClient(BaseLLMClient):
    """A client for interacting with the Ollama API."""

    def __init__(self, model: str = "gemma:2b", host: str = "http://localhost:11434"):
        self.model = model
        self.client = AsyncClient(host=host)

    async def generate(self, history: List[ChatMessage], tools: List[Dict[str, Any]]) -> Union[str, Dict[str, Any]]:
        """
        Generates a response from the Ollama API.

        Args:
            history: A list of ChatMessage objects representing the conversation history.
            tools: A list of tool definitions in JSON Schema format.

        Returns:
            A string containing the text response, or a dictionary
            representing a tool call.
        """
        logger.debug(f"Generating response with model: {self.model}")

        messages = [asdict(msg) for msg in history]

        logger.debug(f"Sending to LLM: messages={messages}, tools={tools}")

        try:
            response = await self.client.chat(
                model=self.model,
                messages=messages,
                tools=tools if tools else None,
            )
            return self._handle_ollama_response(response)

        except httpx.ConnectError as e:
            logger.error(f"Connection to Ollama failed: {e}")
            return "Error: Could not connect to Ollama. Please ensure Ollama is running."
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return f"An unexpected error occurred: {e}"

    def _handle_ollama_response(self, response: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        """Handles the response from the Ollama API."""
        logger.debug(f"Received from LLM: {response}")

        message = response.get("message", {})
        tool_calls = message.get("tool_calls")

        if tool_calls:
            logger.info("Received tool calls from Ollama.")
            return {"tool_calls": tool_calls}

        logger.info("Received text response from Ollama.")
        return message.get("content", "")
