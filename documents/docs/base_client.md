## `class BaseLLMClient`

Abstract base class for all LLM clients.

### `def generate`

Generates a response from the LLM.

Args:
    history: A list of ChatMessage objects representing the conversation history.
    tools: A list of tool definitions in JSON Schema format.

Returns:
    A string containing the text response, or a dictionary
    representing a tool call.

