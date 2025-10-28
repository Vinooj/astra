## `class WorkflowManager`

(Facade Pattern) Manages all workflows, sessions, and is the
main entry point for the framework.

The WorkflowManager simplifies the interaction with the Astra framework by providing
a high-level API for managing the lifecycle of agentic workflows.

### `def __init__`

Initializes the WorkflowManager with empty session and workflow dictionaries.

### `def register_workflow`

Registers a fully-composed agent (like a SequentialAgent)
with a unique name.

Args:
    name: The unique name for the workflow.
    agent: The root agent of the workflow.

### `def create_session`

Creates a new session and returns the session ID.

Returns:
    The unique session ID for the new session.

### `def get_session_state`

Retrieves the state for a given session ID.

Args:
    session_id: The ID of the session to retrieve.

Returns:
    The SessionState object for the given session ID.

Raises:
    Exception: If the session is not found.

### `def run`

Main entry point to run a *named* workflow.

Args:
    workflow_name: The name of the workflow to run.
    session_id: The ID of the session to use.
    prompt: The initial user prompt.

Returns:
    The AgentResponse from the final agent in the workflow.

