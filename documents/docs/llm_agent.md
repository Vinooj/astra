## `class LLMAgent`

The main 'thinking' agent, implementing the ReACT loop.

### `def __init__`

### `def _get_tool_definitions`

Generates JSON Schema definitions for the agent's tools.
This is used to inform the LLM about the available tools and their parameters.

### `def _create_tool_definition`

Creates a JSON Schema definition for a single tool.

### `def _create_tool_parameters`

Creates the JSON Schema parameters for a tool's signature.

### `def _get_param_type`

Returns the JSON schema type for a given parameter.

### `def execute`

Executes the agent's logic.

### `def _add_structured_output_tool`

Adds the structured_output tool to the list of tool definitions.

### `def _handle_llm_response`

Handles the response from the LLM.

### `def _handle_tool_calls`

Handles tool calls from the LLM.

### `def _handle_structured_output`

Handles the structured_output tool call.

### `def _execute_tool`

Executes a tool and updates the state.

### `def _handle_string_response`

Handles a string response from the LLM.

