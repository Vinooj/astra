## `class DynamicWorkflowAgent`

A meta-agent that uses an LLM to dynamically create and execute workflows.
It takes a high-level user prompt, generates a structured workflow plan,
and then instantiates and runs the agents defined in that plan.

### `def __init__`

### `def register_output_structure`

### `def register_tool`

### `def _get_tool_definitions`

### `def execute`

### `def _build_agent_from_config`

Recursively builds an agent instance from its configuration.

