# Astra Agentic Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An advanced, multi-agent framework for building complex, stateful, and reliable AI-driven workflows. Astra provides a robust architecture for creating, composing, and running specialized agents that can collaborate to perform intricate tasks.

## Core Features

- **Agent-Based Architecture:** Build workflows from specialized, reusable agents (`LLMAgent`, `SequentialAgent`, `LoopAgent`).
- **Structured Output:** Enforce reliable, structured outputs from LLMs using Pydantic models.
- **State Management:** A centralized `SessionState` (Blackboard pattern) allows for seamless communication and context sharing between agents.
- **Iterative Workflows:** Use the `LoopAgent` to create self-correcting loops where agents can critique and refine their work.
- **Extensible Services:** Easily integrate with various LLM providers and external tools (e.g., `OllamaClient`, `TavilyClient`).

## Project Architecture and Design

The Astra framework is built on a set of powerful, decoupled software design patterns to ensure it is robust, scalable, and easy to understand.

Key architectural components include:

- **Agents (`BaseAgent`)**: The fundamental building blocks of the framework, representing a strategy for executing a task.
- **Workflows**: Compositions of agents that define a complete process. This can be a simple sequence or a complex, iterative loop.
- **State (`SessionState`)**: A central blackboard where the history and data for a given workflow execution are stored.
- **Manager (`WorkflowManager`)**: A facade that simplifies the process of registering and running workflows.

For a deep dive into the specific classes, the sequence of operations, and the design patterns that form the foundation of this framework, please see our detailed documentation:

- **[Architecture and Design Patterns](./documents/docs/architecture.md)**

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

The project includes two primary example workflows.

### 1. Run the Research Workflow

This workflow demonstrates a multi-agent loop where a research agent, writer, and critique agent collaborate to produce a high-quality report.

```bash
uv run python run_workflow_research_loop.py
```

### 2. Run the Loop Validation Test

This is a simpler workflow designed to test the `LoopAgent`'s exit condition logic.

```bash
uv run python run_workflow_loop_test.py
```

### 3. Generating the documentation

```bash
  Hello, I need to create comprehensive documentation for this new project. Please follow the workflow I've outlined below.

  Workflow: Automated Project Documentation Generation

  Goal: To create and maintain rich, automated, and integrated project documentation.

  Core Principles:

   * Analyze First: Before making changes, thoroughly analyze the existing project structure, conventions, and tools.
   * Use Project-Specific Tools: Adhere to the project's established package manager and development tools.
   * Automate Everything: Create or modify scripts to automate the generation of all documentation artifacts, including diagrams and reports.
   * Integrate, Don't Just Generate: Ensure that all generated content is properly integrated into the main documentation site and navigation.

  Steps:

   1. Initial Analysis:
       * Read the README.md and any existing documentation generation scripts.
       * Examine pyproject.toml, package.json, or similar files to identify project dependencies and tools.
   2. Diagram Generation:
       * Use pyreverse (from pylint) or similar tools to generate class and package diagrams.
       * Identify and use existing sequence diagram files (e.g., Mermaid .seq files) or create new ones.
   3. Code Quality Reports:
       * Integrate ruff, radon, lint, or other code quality tools into the documentation generation process.
   4. Design Pattern Documentation:
       * Create a dedicated section for design patterns, explaining how they are used in the project with concrete examples.
   5. Automation:
       * Create or modify a script (e.g., generate_docs.py) to run all the necessary commands for generating diagrams and reports.
   6. Integration:
       * Update the mkdocs.yml or equivalent configuration file to include all new documentation pages in the navigation.
   7. Verification:
       * Run the documentation server (e.g., mkdocs serve) to verify that all links are working and the documentation is displayed correctly.
```

## Testing

To run the project's test suite, execute the following command:

```bash
# Placeholder for testing command
# e.g., uv run pytest
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
