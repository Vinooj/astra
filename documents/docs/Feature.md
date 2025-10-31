# Feature: Prompt Optimization and ReAct Agent Workflow

This document outlines the architecture and interaction between the prompt optimization process and the ReAct agent workflow within the Astra framework. It focuses on how prompts are optimized for a target LLM and subsequently used to drive an autonomous research agent.

## 1. Core Components

### `examples/research_workflows/prompt_optimizer.py`
*   **Purpose**: This script orchestrates an iterative prompt optimization process. It uses a powerful Foundation Model (FM) as an "Optimizer" to refine prompts for a less capable "Simulation LLM" (the target agent).
*   **Key Logic**:
    *   **Configuration (`Config` class)**: Defines which LLMs are used for optimization (`OPTIMIZER_LLM_MODEL`, e.g., `gemini-2.5-pro`) and simulation (`SIMULATION_LLM_MODEL`, e.g., `qwen3:latest`), along with iteration limits (`MAX_OPTIMIZATION_ITERATIONS`, `SIMULATION_DEPTH`).
    *   **`OPTIMIZER_SYSTEM_PROMPT`**: A critical system prompt given to the Optimizer LLM. It instructs the Optimizer on how to analyze simulation traces, provide feedback, and generate improved prompts. **Crucially, it now includes directives to consider the limitations of the target Simulation LLM (`qwen3:latest`) when optimizing, ensuring the generated prompt is highly explicit and structured.**
    *   **`PromptOptimizer` class**:
        *   `initialize()`: Sets up LLM clients for both the optimizer and the simulation, loads initial prompts and topic data.
        *   `_simulate_react_agent_thinking()`: Simulates the `ReActAgent`'s execution using the current prompt and task context. It captures the agent's 'Thought', 'Action', and 'Observation' steps into a `simulation_trace`. This simulation uses the `SIMULATION_LLM_MODEL`.
        *   `_get_refinement()`: Sends the `original_prompt`, `task_context`, and `simulation_trace` to the `OPTIMIZER_LLM_MODEL` (e.g., `gemini-2.5-pro`) along with the `OPTIMIZER_SYSTEM_PROMPT`. The Optimizer LLM returns structured feedback and a new, optimized prompt.
        *   `optimize()`: Runs the iterative loop. In each iteration, it simulates the agent, gets refinement from the Optimizer, and updates the prompt for the next simulation.
*   **Output**: Saves the final optimized prompt and accumulated feedback to `optimized_prompts/optimized_{OPTIMIZER_LLM_MODEL}.yaml`.
*   **Logging**: Configured to output `INFO` level logs to `logs/optimization.log` for detailed debugging of the optimization process.

### `examples/research_workflows/run_workflow_parallel_research_react.py`
*   **Purpose**: This script executes the actual autonomous research workflow using a `ReActAgent` driven by an optimized prompt.
*   **Key Logic**:
    *   Loads `main_topic` and `sub_topics_list` from `astra_framework/topics_cancer.json`.
    *   Loads the *optimized prompt* from `optimized_prompts/optimized_gemini-2.5-pro.yaml`.
    *   Initializes a `ReActAgent` (from `astra_framework/agents/react_agent.py`) using the `SIMULATION_LLM_MODEL` (e.g., `qwen3:latest`) and the loaded optimized prompt as its `instruction`.
    *   Registers `search_the_web` (using `TavilyClient`) and `generate_html_newsletter` as tools for the `ReActAgent`.
    *   Uses `WorkflowManager` to run the `ReActAgent` with an initial user prompt.
    *   Saves the final generated HTML newsletter to `newsletter.html`.

### `optimized_prompts/optimized_gemini-2.5-pro.yaml`
*   **Purpose**: This file stores the prompt that has been optimized by `prompt_optimizer.py`. It is the instruction set that `run_workflow_parallel_research_react.py` uses to guide its `ReActAgent`.
*   **Content**: Contains the `prompt` text (a detailed instruction for the `ReActAgent`), the `model` it was optimized for (`qwen3:latest`), and `feedback` from the optimization iterations.

### `examples/research_workflows/react_newsletter_prompts.yaml`
*   **Purpose**: This file contains the *initial* prompt templates that `prompt_optimizer.py` uses as a starting point for its optimization process.
*   **Content**: Defines different versions of the `react_researcher` prompt, including `react_researcher_v1` and `react_researcher_v2`. `prompt_optimizer.py` typically starts with one of these and refines it.

## 2. Workflow Interaction

1.  **Initial Prompt Selection**: `prompt_optimizer.py` selects an initial prompt template (e.g., `react_researcher_v1`) from `react_newsletter_prompts.yaml`.
2.  **Iterative Optimization**:
    *   The `PromptOptimizer` simulates the `ReActAgent` (using `qwen3:latest`) with the current prompt.
    *   It captures the agent's thinking process (`simulation_trace`).
    *   It sends this trace, along with the current prompt and task context, to the `gemini-2.5-pro` (Optimizer LLM).
    *   The `gemini-2.5-pro`, guided by `OPTIMIZER_SYSTEM_PROMPT` (which now explicitly considers `qwen3:latest`'s limitations), analyzes the trace, provides feedback, and generates a new, improved prompt.
    *   This new prompt becomes the input for the next optimization iteration.
3.  **Final Optimized Prompt**: After a set number of iterations, the best optimized prompt is saved to `optimized_prompts/optimized_gemini-2.5-pro.yaml`.
4.  **Agent Execution**: `run_workflow_parallel_research_react.py` then loads this final optimized prompt and uses it to instruct its `ReActAgent` (powered by `qwen3:latest`) to perform the actual research and newsletter generation.

## 3. Key Framework Components (Astra)

*   **`astra_framework/manager.py` (`WorkflowManager`)**: The central orchestrator. It registers workflows (which are essentially `BaseAgent` instances), creates sessions, and runs the workflows by delegating execution to the root agent.
*   **`astra_framework/builders/workflow_builder.py` (`WorkflowBuilder`)**: Provides a fluent API to construct complex agent hierarchies (e.g., `ReActAgent`, `SequentialAgent`, `ParallelAgent`, `LoopAgent`).
*   **`astra_framework/core/agent.py` (`BaseAgent`)**: The abstract base class for all agents, defining the `execute` method and common functionalities like structured output validation.
*   **`astra_framework/agents/react_agent.py` (`ReActAgent`)**: A concrete implementation of `BaseAgent` that follows the Thought-Action-Observation loop, making decisions based on an LLM and available tools.
*   **`astra_framework/core/state.py` (`SessionState`)**: Manages the shared state (history, data) for a session, implementing a Blackboard pattern. Agents interact with this state.
*   **`astra_framework/core/tool.py` (`ToolManager`)**: Registers and manages tools that agents can use (e.g., `search_the_web`, `generate_html_newsletter`). It generates JSON schema definitions for tools.
*   **`astra_framework/services/client_factory.py` (`LLMClientFactory`)**: A factory for creating instances of various LLM clients (e.g., `GeminiClient`, `OllamaClient`).
*   **`astra_framework/utils/prompt_loader.py` (`PromptLoader`)**: Utility for loading prompt templates from YAML files.

## 4. Problem Context

The initial problem was that the `ReActAgent` in `run_workflow_parallel_research_react.py` (using `qwen3:latest`) was completing prematurely and not researching all topics, despite using an "optimized" prompt. The analysis revealed that while the prompt was optimized by `gemini-2.5-pro`, it wasn't explicitly optimized *for the limitations* of `qwen3:latest`. The current change to `OPTIMIZER_SYSTEM_PROMPT` aims to address this by guiding `gemini-2.5-pro` to produce an even more robust and explicit prompt suitable for a less capable target LLM.
