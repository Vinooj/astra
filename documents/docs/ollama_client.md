## `class OllamaClient`

A client for interacting with the Ollama API.

### `def __init__`

### `def generate`

Generates a response from the Ollama API.

Args:
    history: A list of ChatMessage objects representing the conversation history.
    tools: A list of tool definitions in JSON Schema format.

Returns:
    A string containing the text response, or a dictionary
    representing a tool call.

### `def _handle_ollama_response`

Handles the response from the Ollama API.

