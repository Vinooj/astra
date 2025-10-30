## `class ToolManager`

Manages tool registration, definition generation, and execution.

### `def __init__`

Initializes the ToolManager. Can be initialized with a list of 
tools.

### `def register`

Decorator or method to register a function as a tool.

### `def get_tool_definitions`

Generates JSON Schema definitions for all registered tools.

### `def _generate_tool_definition`

Generates the JSON schema for a single function.

### `def _map_type_to_json_schema`

Maps Python types to JSON schema types.

### `def execute_tool`

Executes a tool by name with a dictionary of arguments.

### `def _execute_function`

Executes a function, handling both sync and async functions.

