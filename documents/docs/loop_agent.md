# `class LoopAgent`

The `LoopAgent` is a composite agent that executes a single child agent in a loop. This is useful for creating self-correcting workflows where an agent's work can be critiqued and refined until it meets a certain standard.

## Technical Details

-   **Inheritance**: `LoopAgent` inherits from `BaseAgent`.
-   **Child Agent**: It contains a single `BaseAgent` instance that it executes in each loop iteration.
-   **Loop Control**: The loop continues until a maximum number of iterations is reached (`max_loops`) or an `exit_condition` is met.
-   **Feedback Loop**: The output of the child agent from one iteration is used as feedback for the next iteration.

## Class Methods

### `def __init__(self, agent_name: str, child: BaseAgent, max_loops: int = 3, exit_condition: Callable[[SessionState], bool] = None, keep_alive_state: bool = False)`

-   **`agent_name`**: A string that uniquely identifies the agent.
-   **`child`**: The `BaseAgent` instance to be executed in the loop.
-   **`max_loops`**: The maximum number of times the loop can run.
-   **`exit_condition`**: A callable that takes the `SessionState` as input and returns `True` to exit the loop or `False` to continue.
-   **`keep_alive_state`**: A boolean flag that controls whether the conversation history is cleared between loop iterations.

### `async def execute(self, state: SessionState) -> AgentResponse`

This method implements the looping logic:

1.  **Execute Child**: It executes the `child` agent.
2.  **Check Exit Condition**: After the child agent has run, it calls the `exit_condition` with the updated `SessionState`. If the condition is met, the loop terminates.
3.  **Prepare for Next Iteration**: If the exit condition is not met and the maximum number of loops has not been reached, it prepares for the next iteration.
    -   It takes the `final_content` of the child's `AgentResponse` and uses it as feedback.
    -   If `keep_alive_state` is `False`, it clears the `state.history` and creates a new prompt that includes the original prompt and the feedback.
    -   If `keep_alive_state` is `True`, it appends the new prompt (with feedback) to the existing history.
4.  **Return Value**: It returns the `AgentResponse` from the last execution of the child agent.

## Interactions with Other Classes

-   **`BaseAgent`**: The `LoopAgent` is a `BaseAgent` and it contains a single `BaseAgent` child.
-   **`SessionState`**: It passes the `SessionState` to its child and can modify it between loop iterations based on the `keep_alive_state` flag.
-   **`AgentResponse`**: It receives an `AgentResponse` from its child in each iteration and returns the final `AgentResponse` when the loop terminates.