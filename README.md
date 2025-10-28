# Astra Agentic Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An advanced, multi-agent framework for building complex, stateful, and reliable AI-driven workflows. Astra provides a robust architecture for creating, composing, and running specialized agents that can collaborate to perform intricate tasks.

## Core Features

- **Agent-Based Architecture:** Build workflows from specialized, reusable agents (`LLMAgent`, `SequentialAgent`, `LoopAgent`).
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
-   **`LoopAgent`**: Similar to `SequentialAgent`, the `LoopAgent` manages its child's execution in iterations. If `keep_alive_state` is `False`, the history is cleared at the start of each new loop iteration, and a new prompt (incorporating feedback) is added. If `keep_alive_state` is `True`, the history is preserved across iterations, and new prompts are appended.

This design ensures that developers have explicit control over the context provided to each agent, balancing the need for focused execution with the requirement for comprehensive historical awareness in complex, multi-step workflows.

## Sample Loop Agent Flow
```python
# ==============================================================================
# 1. CONFIGURE LOGGER
# ==============================================================================
logger.remove()
logger.add(
    sys.stderr,
    level="INFO", # Set to INFO for a cleaner output for this test
    format="{time:HH:mm:ss.SSS} | {level: <8} | {name: <15}:{function: <15}:{line: >3} - {message}",
    colorize=True
)

# ==============================================================================
# 2. DEFINE PYDANTIC MODELS FOR STRUCTURED OUTPUT
# ==============================================================================
class NumberProposal(BaseModel):
    number: int
    reasoning: str

class ValidationResult(BaseModel):
    approved: bool
    reason: str

# ==============================================================================
# 3. DEFINE THE WORKFLOW
# ==============================================================================
async def main():
    logger.info("============================================")
    logger.info("     STARTING LOOPAGENT VALIDATION WORKFLOW ")
    logger.info("============================================")
    
    # --- 1. Create services ---
    manager = WorkflowManager()
    ollama_llm = OllamaClient(model="qwen3:latest")

    # --- 2. Define Specialist Agents ---
    proposer_agent = LLMAgent(
        agent_name="ProposerAgent",
        llm_client=ollama_llm,
        tools=[],
        instruction="You are a random number generator. Your goal is to propose a number between 5 and 15. Use the structured_output format.",
        output_structure=NumberProposal
    )

    validator_agent = LLMAgent(
        agent_name="ValidatorAgent",
        llm_client=ollama_llm,
        tools=[],
        instruction="You are a validator. The user will provide a JSON object with a number proposal. Your job is to check if the number is greater than 10. If it is, set 'approved' to true. Otherwise, set 'approved' to false and provide a reason. Your response MUST be in the structured_output format.",
        output_structure=ValidationResult
    )

    # --- 3. Define the Loop Exit Condition ---
    def validation_is_approved(state: SessionState) -> bool:
        last_message = state.history[-1]
        if last_message.role == "user": # The validation result is passed as a user message
            try:
                validation = ValidationResult.model_validate_json(last_message.content)
                if validation.approved:
                    logger.success("Validation approved. Exiting loop.")
                    return True
                else:
                    logger.warning(f"Validation failed. Reason: {validation.reason}")
                    return False
            except Exception as e:
                logger.error(f"Could not parse validation result: {e}")
                return False
        return False

    # --- 4. Compose the Workflow ---
    validation_sequence = SequentialAgent(
        agent_name="ValidationSequence",
        children=[proposer_agent, validator_agent]
    )

    validation_loop = LoopAgent(
        agent_name="ValidationLoop",
        child=validation_sequence,
        max_loops=3,
        exit_condition=validation_is_approved
    )

    # --- 5. Register Workflow(s) with the Manager ---
    manager.register_workflow(name="loop_test", agent=validation_loop)
    
    # --- 6. Execute ---
    session_id = manager.create_session()
    prompt = "Generate a number."
    
    final_response = await manager.run(
        workflow_name="loop_test",
        session_id=session_id,
        prompt=prompt
    )
    
    logger.info("============================================")
    logger.info("            WORKFLOW COMPLETE             ")
    logger.info("============================================")
    
    print(f"\nWorkflow finished.\nInitial Prompt: {prompt}\n")
    
    if isinstance(final_response.final_content, BaseModel):
        print("--- Final Output ---")
        print(final_response.final_content.model_dump_json(indent=2))
    else:
        print(f"--- Final Answer ---\n{final_response.final_content}")
```

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
