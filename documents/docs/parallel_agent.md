# `class ParallelAgent`

The `ParallelAgent` is a composite agent that executes a list of child agents concurrently. It implements the **Composite Pattern**.

## Technical Details

-   **Inheritance**: `ParallelAgent` inherits from `BaseAgent`.
-   **Children**: It maintains a list of `BaseAgent` instances that it executes in parallel.
-   **State Isolation**: To prevent race conditions and ensure that parallel agents don't interfere with each other's state, each child agent receives a deep copy of the `SessionState`. This means that any changes a child agent makes to the state will not be visible to other child agents or to the parent agent.

## Class Methods

### `def __init__(self, agent_name: str, children: List[BaseAgent], keep_alive_state: bool = False)`

-   **`agent_name`**: A string that uniquely identifies the agent.
-   **`children`**: A list of `BaseAgent` instances to be executed in parallel.
-   **`keep_alive_state`**: A boolean flag inherited from `BaseAgent`. This flag does not have a direct effect on the `ParallelAgent`'s execution logic, as the state is not modified.

### `async def execute(self, state: SessionState) -> AgentResponse`

This method uses `asyncio.gather` to run all child agents concurrently.

-   **State Handling**: It creates a deep copy of the `SessionState` for each child agent to ensure isolation.
-   **Return Value**: It aggregates the `final_content` from each of the child agents' responses into a single list and returns that as its own `final_content` in the `AgentResponse`. The original `SessionState` is not modified.

## Interactions with Other Classes

-   **`BaseAgent`**: The `ParallelAgent` is a `BaseAgent` and it contains a list of `BaseAgent` children.
-   **`SessionState`**: It creates deep copies of the `SessionState` to pass to its children. It does not modify the original `SessionState`.
-   **`AgentResponse`**: It receives an `AgentResponse` from each child and returns a new `AgentResponse` with the aggregated `final_content`.