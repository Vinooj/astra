# `class SequentialAgent`

The `SequentialAgent` is a composite agent that executes a list of child agents in a specific order. It implements the **Composite Pattern** and the **Chain of Responsibility Pattern**.

## Technical Details

-   **Inheritance**: `SequentialAgent` inherits from `BaseAgent`.
-   **Children**: It maintains a list of `BaseAgent` instances that it executes in sequence.
-   **State Management**: It can modify the `SessionState` between child agent executions, depending on the `keep_alive_state` flag.

## Class Methods

### `def __init__(self, agent_name: str, children: List[BaseAgent], keep_alive_state: bool = False)`

-   **`agent_name`**: A string that uniquely identifies the agent.
-   **`children`**: A list of `BaseAgent` instances to be executed in sequence.
-   **`keep_alive_state`**: A boolean flag that controls whether the conversation history is cleared between child agent executions.

### `async def execute(self, state: SessionState) -> AgentResponse`

This method iterates through the `children` list and executes each agent in order.

-   **State Handling**:
    -   If a child agent returns a structured output (a Pydantic `BaseModel`), the `SequentialAgent`'s behavior depends on the `keep_alive_state` flag:
        -   If `keep_alive_state` is `False` (the default), the `state.history` is cleared, and the structured output is added as a new "user" message. This prunes the context for the next agent.
        -   If `keep_alive_state` is `True`, the structured output is simply appended to the existing `state.history` as a new "user" message.
-   **Return Value**: It returns the `AgentResponse` from the *last* agent in the sequence.

## Interactions with Other Classes

-   **`BaseAgent`**: The `SequentialAgent` is a `BaseAgent` and it contains a list of `BaseAgent` children.
-   **`SessionState`**: It passes the `SessionState` to its children and can modify it between executions.
-   **`AgentResponse`**: It receives an `AgentResponse` from each child and returns the final `AgentResponse` from the last child.