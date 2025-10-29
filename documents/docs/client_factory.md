## `class LLMClientFactory`

A factory for creating LLM clients.

### `def create_client`

Creates an LLM client.

Args:
    client_type: The type of client to create (e.g., "gemini", "ollama").
    model: The model to use for the client.
    **kwargs: Additional keyword arguments for the client.

Returns:
    An instance of the specified LLM client.

