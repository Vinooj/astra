# `class LLMAgent`

The `LLMAgent` is the primary "thinking" agent in the Astra framework. It uses a large language model (LLM) to understand context, use tools, and generate responses. It implements a version of the **ReAct (Reasoning and Acting)** loop, where it can reason about a problem, decide to use a tool, observe the tool's output, and then continue its reasoning process.

## Technical Details

-   **Inheritance**: `LLMAgent` inherits from `BaseAgent`.
-   **LLM Integration**: It uses an `OllamaClient` (or any other `BaseLLMClient` implementation) to interact with an LLM.
-   **Tool Management**: It has a `ToolManager` instance to register and execute tools.
-   **Structured Output**: It can be configured with a Pydantic `output_structure` to force the LLM to generate structured output.

## Class Methods

### `def __init__(self, agent_name: str, llm_client: OllamaClient, tools: List[Callable], instruction: str, output_structure: Optional[Type[BaseModel]] = None, keep_alive_state: bool = False)`

-   **`agent_name`**: A string that uniquely identifies the agent.
-   **`llm_client`**: An instance of a class that inherits from `BaseLLMClient`, used to communicate with the LLM.
-   **`tools`**: A list of Python functions that the agent can use as tools.
-   **`instruction`**: A string that provides the LLM with its core instructions or persona.
-   **`output_structure`**: An optional Pydantic `BaseModel` that defines the expected schema for the agent's output.
-   **`keep_alive_state`**: A boolean flag inherited from `BaseAgent`.

### `def _get_tool_definitions(self) -> List[Dict[str, Any]]`

This private method generates JSON Schema definitions for the agent's tools. These definitions are then passed to the LLM so that it knows what tools are available and how to use them.

### `async def execute(self, state: SessionState) -> AgentResponse`

This is the core execution logic of the `LLMAgent`. It implements the ReAct loop:

1.  **Prepare Inputs**: It constructs the prompt for the LLM by combining the `instruction`, the current conversation `history` from the `SessionState`, and the tool definitions.
2.  **Call LLM**: It calls the LLM with the prepared inputs.
3.  **Process Response**:
    -   **If the LLM calls a tool**: It parses the tool call, executes the tool using the `ToolManager`, adds the tool's output to the `history`, and then re-runs the `execute` method to continue the reasoning process.
    -   **If the LLM returns a structured output**: It parses the output into the specified `output_structure`, adds it to the `history` and `state.data`, and returns it in the `AgentResponse`.
    -   **If the LLM returns a string**: It adds the string to the `history` and `state.data`, and returns it in the `AgentResponse`.

## Interactions with Other Classes

-   **`BaseLLMClient`**: The `LLMAgent` is tightly coupled with a `BaseLLMClient` (e.g., `OllamaClient`) to communicate with the LLM.
-   **`ToolManager`**: It uses a `ToolManager` to manage the registration and execution of tools.
-   **`SessionState`**: It reads the conversation `history` from the `SessionState` and writes its own responses and tool calls/results back to it. It also writes its final response to `state.data['last_agent_response']`.
-   **`AgentResponse`**: It returns an `AgentResponse` containing the final output of its execution.