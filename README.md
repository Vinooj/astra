# Astra Agentic Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An advanced, multi-agent framework for building complex, stateful, and reliable AI-driven workflows. Astra provides a robust architecture for creating, composing, and running specialized agents that can collaborate to perform intricate tasks.

## Project Architecture and Design

The Astra framework is built on a set of powerful, decoupled software design patterns to ensure it is robust, scalable, and easy to understand.

Key architectural components include:

- **Agents (`BaseAgent`)**: The fundamental building blocks of the framework, representing a strategy for executing a task.
- **Workflows**: Compositions of agents that define a complete process. This can be a simple sequence or a complex, iterative loop.
- **State (`SessionState`)**: A central blackboard where the history and data for a given workflow execution are stored.
- **Manager (`WorkflowManager`)**: A facade that simplifies the process of registering and running workflows.

For a deep dive into the specific classes, the sequence of operations, and the design patterns that form the foundation of this framework, please see our detailed documentation:

- **[Architecture and Design Patterns](./documents/docs/architecture.md)**

| Report | Description |
|---|---|
| [Radon Report](./documents/docs/radon_report.md) | Provides code metrics and complexity analysis. |
| [Ruff Report](./documents/docs/ruff_report.md) | Details linting and formatting issues. |
| [Test Coverage](./documents/docs/test_coverage.md) | Shows the test coverage of the codebase. |

## Core Features

- **Agent-Based Architecture:** Build workflows from specialized, reusable agents (`LLMAgent`, `SequentialAgent`, `ParallelAgent`, `LoopAgent`).
- **Structured Output:** Enforce reliable, structured outputs from LLMs using Pydantic models.
- **State Management:** A centralized `SessionState` (Blackboard pattern) allows for seamless communication and context sharing between agents.
- **Iterative Workflows:** Use the `LoopAgent` to create self-correcting loops where agents can critique and refine their work.
- **Extensible Services:** Easily integrate with various LLM providers and external tools (e.g., `OllamaClient`, `TavilyClient`).

## State Management and Conversation History

The Astra framework employs a robust state management system centered around the `SessionState` object, which acts as a "blackboard" for agents to share information and maintain context throughout a workflow.

### `SessionState` (The Blackboard)

-   **`session_id`**: A unique identifier for each workflow execution.
-   **`history`**: A list of `ChatMessage` objects, representing the chronological flow of the conversation. This includes user prompts, agent responses, and tool outputs.
-   **`data`**: A flexible dictionary where agents can store and retrieve arbitrary data, acting as a shared memory space.

### `keep_alive_state` Flag

Introduced at the `BaseAgent` level, the `keep_alive_state` boolean flag provides fine-grained control over how conversation history is managed within composite agents (like `SequentialAgent` and `LoopAgent`):

-   **`keep_alive_state = False` (Default)**: When a composite agent's child agent produces a structured output, the composite agent will typically clear the `state.history` and re-initialize it with the structured output as a new "user" message. This ensures that subsequent agents in the sequence or loop start with a focused context, preventing the history from growing excessively large or becoming polluted with irrelevant past interactions.
-   **`keep_alive_state = True`**: The `state.history` is *not* cleared between child agent executions within a composite agent. Instead, the structured output is simply appended to the existing history as a new "user" message. This is crucial for workflows where agents need access to the full, cumulative conversation context to perform their tasks effectively.

### How Conversation History is Managed

-   **`LLMAgent`**: When an `LLMAgent` generates a response (either a natural language string or a structured output), it adds this response to the `state.history` as a `ChatMessage` with the role "agent". If the response is a structured output, it is also stored in `state.data['last_agent_response']`.
-   **`SequentialAgent`**: This agent iterates through its children. If a child returns a structured output, the `SequentialAgent` will either clear the history (if `keep_alive_state` is `False`) or append the structured output to the history (if `keep_alive_state` is `True`), presenting it as a new "user" message for the next agent in the sequence.
-   **`ParallelAgent`**: This agent executes all its children concurrently. To prevent race conditions, each child receives a deep copy of the session state. The `ParallelAgent` then aggregates the `final_content` from each child into a list. The original session state is not modified by the children; the aggregated list of results is returned for a subsequent agent to process.
-   **`LoopAgent`**: Similar to `SequentialAgent`, the `LoopAgent` manages its child's execution in iterations. If `keep_alive_state` is `False`, the history is cleared at the start of each new loop iteration, and a new prompt (incorporating feedback) is added. If `keep_alive_state` is `True`, the history is preserved across iterations, and new prompts are appended.

This design ensures that developers have explicit control over the context provided to each agent, balancing the need for focused execution with the requirement for comprehensive historical awareness in complex, multi-step workflows.

### Structured Output (`output_structure`)

Astra leverages Pydantic models to enforce structured outputs from LLMs, ensuring reliability and ease of parsing.

-   **Definition**: The `output_structure` is an optional parameter in the `BaseAgent` (and typically used by `LLMAgent`) that accepts a Pydantic `BaseModel` subclass. This model defines the expected schema for the LLM's response.
-   **Usage**: When an `LLMAgent` is configured with an `output_structure`, it instructs the underlying LLM to generate its response in a JSON format that conforms to the specified Pydantic model. The framework then automatically parses this JSON into a Pydantic model instance.
-   **Benefits**:
    -   **Reliability**: Guarantees that the LLM's output adheres to a predefined structure, reducing parsing errors.
    -   **Type Safety**: Allows for easy validation and manipulation of LLM responses using Python's type hinting and Pydantic's features.
    -   **Interoperability**: Structured outputs can be seamlessly passed between agents or integrated with other systems.
-   **Lifespan**: The `output_structure` *type* (the Pydantic class) lives as long as the agent instance. The *instance* of the structured output (the Pydantic object containing the data) is created when the LLM's response is parsed. This instance is then typically added to the `SessionState.history` (as a JSON string) and can be stored in `SessionState.data` for direct access.

## Getting Started

### Prerequisites

- Python 3.12+
- `uv` package manager (`pip install uv`)
- An Ollama-compatible LLM running (e.g., `ollama run qwen3:latest`)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd astra
    ```

2.  **Create the virtual environment and install dependencies:**
    `uv` will automatically create a virtual environment and install all required packages from `pyproject.toml`.
    ```bash
    uv sync
    ```

3.  **Set up environment variables:**
    The research workflow requires an API key from Tavily. Export it as an environment variable:
    ```bash
    export TAVILY_API_KEY='your-tavily-api-key'
    ```

## Usage

The project includes four primary example workflows.

**Important:** Before you run the workfolows below run 
```bash
# make sure us is installed
source .venv/bin/activate

# This command looks at the pyproject.toml in your project's root directory. 
# This file defines your main astra project, and it's configured to include 
# the astra_framework directory as part of it. So, this command installs the 
# entire project, making all its internal packages (like astra_framework) 
# available in your environment.
uv pip install -e .
```

### 1. Run the Dynamic Workflow Demo

This workflow demonstrates the `DynamicWorkflowAgent` which uses an LLM to dynamically create and execute a complex multi-agent workflow based on a high-level user prompt. It showcases the LLM's ability to plan and orchestrate other agents.

```bash
uv run python examples/simple_workflows/run_dynamic_workflow.py
```

### 2. Run the Parallel Research Workflow

This workflow demonstrates the use of `ParallelAgent` to run multiple research/write/critique loops concurrently for different sub-topics defined in a JSON file.

```bash
uv run python examples/research_workflows/run_workflow_parallel_research.py
```

### 3. Run the Research Workflow

This workflow demonstrates a multi-agent loop where a research agent, writer, and critique agent collaborate to produce a high-quality report.

```bash
uv run python examples/research_workflows/research_writer_critique_loop.py
```

### 4. Run the Math Parallel Workflow

This workflow demonstrates the use of `SequentialAgent`, `ParallelAgent`, and `LoopAgent` to perform a series of math calculations.

```bash
uv run python examples/math_workflows/run_workflow_math_parallel.py
```

### 5. Run the Loop Validation Test

This is a simpler workflow designed to test the `LoopAgent`'s exit condition logic.

```bash
uv run python examples/simple_workflows/run_workflow_loop_test.py
```

### 6. Generating Documentation

The project includes a script to automate the generation of documentation. This script will:
-   Generate markdown files for each Python file in `astra_framework`.
-   Generate class and package diagrams.
-   Generate `ruff` and `radon` reports.

To run the script, use the following command:

```bash
python examples/docs_generator/generate_docs.py
```

## Testing

To run the project's test suite, execute the following command:

```bash
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue to discuss your ideas.

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE.md) file for details.
