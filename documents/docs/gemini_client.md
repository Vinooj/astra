## `class GeminiClient`

A client for interacting with the Google Gemini API using the
new 'google-genai' package.

### `def __init__`

Initializes the GeminiClient.

Args:
    model: The name of the Gemini model to use.

### `def generate`

Generates a response from the Gemini API.

Args:
    history: List of ChatMessage objects representing conversation history
    tools: Optional list of tool definitions in OpenAI format
    json_response: Whether to request JSON response format
    
Returns:
    Either a string response or a dict with tool_calls

### `def _convert_role`

Converts standard roles to Gemini roles.

### `def _convert_tools_to_gemini`

Converts OpenAI-style tool definitions to Gemini format.

Args:
    tools: List of tool definitions in OpenAI format
    
Returns:
    List of Gemini Tool objects

### `def _parse_function_call`

Converts a Gemini FunctionCall object to OpenAI-style dict.

Args:
    fc: Gemini FunctionCall object
    
Returns:
    OpenAI-style tool call dictionary

