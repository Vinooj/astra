# `class BaseAgent`

The `BaseAgent` is an abstract base class that defines the common interface for all agents in the Astra framework. It follows the **Strategy Pattern**, where each concrete agent is a specific strategy for executing a task.

## Technical Details

-   **Abstract Base Class**: `BaseAgent` inherits from `abc.ABC` and defines the abstract method `execute`, which must be implemented by all concrete agent classes.
-   **Initialization**: The constructor initializes the agent with a name, an optional `output_structure` (a Pydantic model), and a `keep_alive_state` flag.

## Class Methods

### `def __init__(self, agent_name: str, output_structure: Optional[Type[BaseModel]] = None, keep_alive_state: bool = False)`

-   **`agent_name`**: A string that uniquely identifies the agent.
-   **`output_structure`**: An optional Pydantic `BaseModel` that defines the expected schema for the agent's output. This is used by agents like `LLMAgent` to generate structured output.
-   **`keep_alive_state`**: A boolean flag that controls whether the conversation history is cleared in composite agents.

### `async def execute(self, state: SessionState) -> AgentResponse`

This is the core method of the agent. It takes the current `SessionState` as input and returns an `AgentResponse`.

-   **`state`**: The `SessionState` object, which acts as a blackboard for the workflow, containing the conversation history and shared data.
-   **Returns**: An `AgentResponse` object, which contains the status of the execution and the final content produced by the agent.

## Interactions with Other Classes

-   **`SessionState`**: The `BaseAgent` interacts with the `SessionState` to read the current context and write its output.
-   **`AgentResponse`**: The `execute` method returns an `AgentResponse` to communicate the result of its execution to the calling agent or `WorkflowManager`.
-   **`WorkflowManager`**: The `WorkflowManager` uses the `BaseAgent` interface to execute workflows without needing to know the specific type of agent.
-   **Composite Agents (`SequentialAgent`, `ParallelAgent`, `LoopAgent`)**: These agents are also `BaseAgent`s and can contain other `BaseAgent`s as children, forming complex workflow structures.