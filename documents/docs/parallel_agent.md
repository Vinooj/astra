## `class ParallelAgent`

(Composite Pattern)
Executes a list of child agents in parallel and aggregates their responses.
Each child agent receives a deep copy of the state to ensure isolation
and prevent race conditions.

### `def __init__`

### `def execute`

Executes the agent's logic.

### `def _aggregate_responses`

Aggregates the responses from the child agents.

