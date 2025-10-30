## `class ReActAgent`

An agent that implements the ReAct (Reason, Act, Observe) pattern.
It uses an LLM to reason about a goal, selects and executes tools to 
act, and observes the results to inform the next cycle.

### `def __init__`

### `def execute`

Executes the ReAct loop until a final answer is produced or 
max_iterations is reached.

