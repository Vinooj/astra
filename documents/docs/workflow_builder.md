## `class WorkflowBuilder`

Provides a fluent API to construct complex agent workflows.

### `def __init__`

### `def start_with_react_agent`

Starts the workflow with a ReActAgent as the root.

### `def start_with_sequential`

Starts the workflow with a SequentialAgent as the root.

### `def add_agent`

Adds an agent to the current composite agent (e.g., a 
SequentialAgent).

### `def build`

Returns the constructed root agent of the workflow.

