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

