# =============================================================================
#  Filename: prompt_optimizer.py
#
#  Short Description: Optimizes the ReAct agent instruction by analyzing LLM's simulated thinking process.
#
#  Creation date: 2025-10-29
#  Author: Asif Qamar
# =============================================================================

import asyncio
import sys
import os
import json
from loguru import logger
from typing import List, Dict, Any, Union
from pydantic import BaseModel, Field

# --- Import our framework classes ---
from astra_framework.manager import WorkflowManager
from astra_framework.agents.react_agent import ReActAgent
from astra_framework.agents.llm_agent import LLMAgent
from astra_framework.services.client_factory import LLMClientFactory
from astra_framework.services.tavily_client import TavilyClient
from astra_framework.core.state import SessionState, ChatMessage
from astra_framework.core.models import AgentResponse
from astra_framework.core.tool import ToolManager

# ==============================================================================
# 1. CONFIGURE LOGGER
# ==============================================================================
logger.remove()
logger.add(
    sys.stderr,
    level="INFO", # Set to INFO to observe Thought, Action, Observation steps
    format="{time:HH:mm:ss.SSS} | {level: <8} | {name: <15}:{function: <15}:{line: >3} - {message}",
    colorize=True
)

# ==============================================================================
# 2. DEFINE DATA MODELS FOR THE AGENT
#    (Copied from run_workflow_parallel_research_react.py for consistency)
# ==============================================================================
class Article(BaseModel):
    topic: str
    title: str
    summary: str
    url: str
    published_date: str

class NewsletterPayload(BaseModel):
    main_editorial: str
    articles: List[Article]

class PromptOptimizationResult(BaseModel):
    optimized_prompt: str = Field(..., description="The optimized instruction for the ReActAgent.")
    feedback: str = Field(..., description="Feedback on why this instruction is considered optimal.")

# ==============================================================================
# 3. GLOBAL INSTANCES AND TOOL DEFINITIONS
# ==============================================================================

# Global instances for LLM client
ollama_llm_client = None

# ToolManager to get JSON schema definitions of the research agent's tools
# We will NOT execute these tools in this optimizer, only use their definitions.
research_tool_definitions: List[Dict[str, Any]] = []

# ToolManager for the *optimizer* agent's tools
optimizer_tool_manager = ToolManager()

# These will be populated in main()
GLOBAL_MAIN_TOPIC: str = ""
GLOBAL_SUB_TOPICS_LIST_JSON: str = ""

# --- Define the research agent's tool definitions (for simulation) ---
# These are NOT actual executable tools in this file, but their schemas.
# We need to manually define them or get them from a ToolManager that has them registered.
# For simplicity, let's define them here as they would appear in the LLM's tool_calls.

# Define search_the_web tool schema
search_the_web_schema = {
    "type": "function",
    "function": {
        "name": "search_the_web",
        "description": "Searches the web for a given query using the Tavily API.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query."
                }
            },
            "required": ["query"]
        }
    }
}

# Define generate_html_newsletter tool schema
generate_html_newsletter_schema = {
    "type": "function",
    "function": {
        "name": "generate_html_newsletter",
        "description": "Generates a final HTML newsletter from a structured payload object. This should be the LAST step once all research and writing is complete.",
        "parameters": {
            "type": "object",
            "properties": {
                "payload": {
                    "type": "object",
                    "description": "A payload object containing the main editorial and a list of articles.",
                    "properties": {
                        "main_editorial": {"type": "string"},
                        "articles": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Article"}
                        }
                    },
                    "required": ["main_editorial", "articles"]
                }
            },
            "required": ["payload"]
        }
    }
}

# Add these to the research_tool_definitions list
research_tool_definitions.append(search_the_web_schema)
research_tool_definitions.append(generate_html_newsletter_schema)

# ==============================================================================
# 4. TOOLS FOR THE PROMPT OPTIMIZER REACT AGENT
# ==============================================================================

import uuid
# ... (rest of imports)

# ... (rest of the file)

@optimizer_tool_manager.register
async def simulate_react_agent_thinking(instruction_to_simulate: str) -> str:
    """
    Simulates the LLM's Thought-Action-Observation process given an instruction and tool definitions.
    Returns a textual trace of the simulated thinking process.

    :param instruction_to_simulate: The instruction string for the ReActAgent to simulate.
    """
    global ollama_llm_client, GLOBAL_MAIN_TOPIC, GLOBAL_SUB_TOPICS_LIST_JSON, research_tool_definitions

    if ollama_llm_client is None:
        raise ValueError("Ollama LLM client not initialized.")
    if not GLOBAL_MAIN_TOPIC or not GLOBAL_SUB_TOPICS_LIST_JSON:
        raise ValueError("Global topic information not set.")

    logger.info(f"TOOL: Simulating ReActAgent thinking for instruction: {instruction_to_simulate[:100]}...")

    sub_topics_list = json.loads(GLOBAL_SUB_TOPICS_LIST_JSON)

    try:
        # The instruction_to_simulate is expected to be a template string
        full_instruction = instruction_to_simulate.format(main_topic=GLOBAL_MAIN_TOPIC, sub_topics_list=sub_topics_list)
    except KeyError as e:
        return f"Error: Instruction template missing key: {e}. Ensure instruction uses {{main_topic}} and {{sub_topics_list}}."

    # Create a dummy session state for the simulation
    session_state = SessionState(session_id=str(uuid.uuid4())) # Generate a unique ID
    initial_react_prompt = f"Please begin your research on {GLOBAL_MAIN_TOPIC}."
    session_state.add_message(role="user", content=initial_react_prompt)

    # Simulate the ReAct loop by directly calling the LLM with the instruction and tool definitions
    # We will capture the LLM's responses (Thought, Action) but not execute tools.
    thinking_trace = []
    execution_history = [ChatMessage(role="system", content=full_instruction)] + session_state.history

    for i in range(5): # Simulate a few turns of thinking
        logger.debug(f"Simulating turn {i+1}")
        llm_response: Union[str, Dict[str, Any]] = await ollama_llm_client.generate(
            execution_history,
            tools=research_tool_definitions
        )

        if isinstance(llm_response, dict) and "tool_calls" in llm_response:
            tool_calls = llm_response["tool_calls"]
            thinking_trace.append(f"Thought: LLM decided to use tools.\nAction: {json.dumps(tool_calls, indent=2)}")
            # For simulation, we don't execute the tool, but provide a dummy observation
            dummy_observation = f"Observation: Tool call simulated. (No actual execution)."
            thinking_trace.append(dummy_observation)
            execution_history.append(ChatMessage(role="agent", content=json.dumps(tool_calls)))
            execution_history.append(ChatMessage(role="tool", content=dummy_observation))
        elif isinstance(llm_response, str):
            thinking_trace.append(f"Thought: {llm_response}\nAction: (No tool call, LLM provided a final answer or intermediate thought)")
            execution_history.append(ChatMessage(role="agent", content=llm_response))
            if "final answer" in llm_response.lower(): # Heuristic to stop simulation if LLM thinks it's done
                break
        else:
            thinking_trace.append(f"Error: Unexpected LLM response type: {type(llm_response)}")
            break

    return "\n".join(thinking_trace)

# ... (rest of the file)


@optimizer_tool_manager.register
async def critique_simulated_thinking(simulated_thinking_trace: str, original_instruction: str) -> str:
    """
    Critiques the simulated LLM thinking trace and provides feedback for instruction improvement.

    :param simulated_thinking_trace: The textual trace of the LLM's simulated Thought-Action-Observation process.
    :param original_instruction: The instruction string that was used to generate the simulated thinking.
    """
    global ollama_llm_client, GLOBAL_MAIN_TOPIC, GLOBAL_SUB_TOPICS_LIST_JSON
    if ollama_llm_client is None:
        raise ValueError("Ollama LLM client not initialized.")
    if not GLOBAL_MAIN_TOPIC or not GLOBAL_SUB_TOPICS_LIST_JSON:
        raise ValueError("Global topic information not set.")

    logger.info("TOOL: Critiquing simulated thinking trace...")

    sub_topics_list = json.loads(GLOBAL_SUB_TOPICS_LIST_JSON)

    critique_llm_agent = LLMAgent(
        agent_name="CritiqueThinkingAgent",
        llm_client=ollama_llm_client,
        tools=[],
        instruction=(
            "You are an expert prompt engineer. You have been given a simulated Thought-Action-Observation "
            "trace of an LLM trying to follow an instruction to generate an HTML newsletter. "
            "Your task is to critically evaluate this simulated thinking process based on the following criteria:\n"
            f"1. **Adherence to ReAct Pattern:** Did the LLM consistently follow Thought, Action, Observation?\n"
            f"2. **Logical Flow:** Is the thinking process logical and progressive towards the goal of generating a newsletter covering {sub_topics_list}?\n"
            f"3. **Tool Usage Strategy:** Does the LLM demonstrate an effective strategy for using `search_the_web` and `generate_html_newsletter`?\n"
            f"4. **Completeness of Plan:** Does the thinking process indicate it would cover all sub-topics and lead to a complete newsletter?\n"
            "Provide specific, actionable feedback on how the *original instruction* could be improved "
            "to guide the LLM's thinking process more effectively. If the simulated thinking is excellent, "
            "state that and suggest no further instruction improvements. Focus solely on instruction improvement suggestions. "
            "The original instruction was: '''" + original_instruction + "'''\n\n"
            "Here is the simulated thinking trace:\n'''" + simulated_thinking_trace + "'''"
        )
    )

    session_state = SessionState()
    session_state.add_message(role="user", content=simulated_thinking_trace)

    response = await critique_llm_agent.execute(session_state)

    if response.status == "success" and response.final_content:
        return str(response.final_content)
    else:
        return f"Error: CritiqueThinkingAgent failed to provide feedback. Status: {response.status}, Content: {response.final_content}"

# ==============================================================================
# 5. MAIN OPTIMIZATION WORKFLOW
# ==============================================================================
async def main():
    global ollama_llm_client, GLOBAL_MAIN_TOPIC, GLOBAL_SUB_TOPICS_LIST_JSON
    logger.info("=============================================")
    logger.info("     STARTING PROMPT OPTIMIZATION WORKFLOW     ")
    logger.info("=============================================")

    # --- 1. Initialize LLM Client ---
    ollama_llm_client = LLMClientFactory.create_client(client_type="ollama", model="qwen3:latest")

    # --- 2. Load topics from JSON ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    topics_file_path = os.path.join(script_dir, '..', '..',
                                    'astra_framework', 'topics_cancer.json')
    with open(topics_file_path, 'r') as f:
        topics_data = json.load(f)
    main_topic = topics_data['main_topic']
    sub_topics_list = [t['name'] for t in topics_data['sub_topics']]
    sub_topics_list_json = json.dumps(sub_topics_list)

    # Set global topic information for tools
    GLOBAL_MAIN_TOPIC = main_topic
    GLOBAL_SUB_TOPICS_LIST_JSON = sub_topics_list_json

    # --- 3. Define initial instruction for the ReAct Agent (from run_workflow_parallel_research_react.py) ---
    initial_react_instruction = (
        """
    You are an autonomous, expert medical researcher and editor.
    Your goal is to produce a comprehensive HTML newsletter about {main_topic}.

    You MUST follow the ReAct pattern: Thought, Action, Observation.
    In EACH turn, you MUST first output your 'Thought:', then an 'Action:' 
    (tool call in JSON), and then observe the 'Observation:' (tool output).
    You MUST continue this cycle until the final HTML newsletter is generated.
    DO NOT provide any other text or final answer until the 
    `generate_html_newsletter` tool has been successfully called. You MUST 
    call a tool in every Action step.

    **Current State Tracking (Internal):**
    - `processed_sub_topics`: Keep track of which sub-topics 
      ({sub_topics_list}) have been fully researched, summarized into 
      `Article` objects and critiqued.
    - `collected_articles`: A list of all structured `Article` objects 
      gathered so far.
    - `main_editorial_content`: Stores the generated main editorial content.

    **Your Process (Thought -> Action -> Observation):**

    1.  **For each sub-topic in {sub_topics_list} (sequentially, one by one):**
        a.  **Thought**: Determine if the current sub-topic needs research. 
            If so, formulate a query for `search_the_web`.
        b.  **Action**: Call `search_the_web` with your query.
        c.  **Observation**: Process the search results. Based on these, 
            generate a detailed summary, structure it as an `Article` object 
            (with 'topic', 'title', 'summary', 'url', 'published_date'), 
            and add it to `collected_articles`.
        d.  **Thought**: Review the created `Article` object for quality, 
            accuracy, and completeness. If needed, perform more research or 
            refinement.
        e.  **Action**: (Implicit, internal refinement or another 
            `search_the_web` call if needed).
        f.  **Observation**: (Implicit, updated internal state).
        g.  Mark the sub-topic as `processed_sub_topics`.

    2.  **After all sub-topics are processed:**
        a.  **Thought**: Now that all sub-topics are covered and articles 
            collected, synthesize a single, cohesive `main_editorial_content` 
            that integrates findings from `collected_articles`.
        b.  **Action**: (Implicit, internal generation of editorial).
        c.  **Observation**: (Implicit, updated internal state).

    3.  **Final Step:**
        a.  **Thought**: All research is done, articles are collected, and the 
            main editorial is written. Time to finalize the newsletter.
        b.  **Action**: Call `generate_html_newsletter` with a 
            `NewsletterPayload` object. The `main_editorial` will be 
            `main_editorial_content`, and `articles` will be 
            `collected_articles`.
        c.  **Observation**: This will be the final HTML newsletter. Emit this 
            content.
        
    Your ULTIMATE final answer MUST be the HTML content returned by the 
    `generate_html_newsletter` tool. Do NOT provide any other text as your 
    final answer. Ensure you call `generate_html_newsletter` with the fully 
    constructed `NewsletterPayload`.
    """
    )

    # --- 4. Define the ReAct Agent for Prompt Optimization ---
    prompt_optimizer_agent = ReActAgent(
        agent_name="PromptOptimizerAgent",
        llm_client=ollama_llm_client,
        tools=list(optimizer_tool_manager.tools.values()), # Use the optimizer's tools
        instruction=(
            "You are an expert prompt optimization agent. Your goal is to refine the instruction "
            "for an 'AutonomousResearcher' ReActAgent by analyzing its simulated thinking process. "
            "You will be given an initial instruction and the main topic and sub-topics. "
            "Your task is to iteratively improve the instruction by "
            "using the 'simulate_react_agent_thinking' tool to get the LLM's simulated Thought-Action-Observation trace, "
            "and then using the 'critique_simulated_thinking' tool to get feedback on that trace. "
            "Based on the feedback, you will suggest changes to the instruction. "
            "Continue this cycle until the 'critique_simulated_thinking' indicates the simulated thinking is excellent "
            "or you have reached a satisfactory instruction. "
            "Your final answer MUST be a JSON object with the 'optimized_prompt' and 'feedback' fields, "
            "using the PromptOptimizationResult Pydantic model. "
            "Start by simulating the initial instruction."
        ),
        max_iterations=5, # Allow for a few rounds of optimization
        output_structure=PromptOptimizationResult
    )

    # --- 5. Run the Prompt Optimization ---
    session_id = WorkflowManager().create_session() 
    
    # The initial prompt for the optimizer agent will be the current react agent instruction
    optimizer_initial_message = (
        f"Optimize the following ReActAgent instruction:\n\n'''{initial_react_instruction}'''\n\n"
        f"Main Topic: {main_topic}\n"
        f"Sub-topics: {sub_topics_list_json}"
    )

    final_optimization_response = await prompt_optimizer_agent.execute(
        SessionState(session_id=session_id, history=[ChatMessage(role="user", content=optimizer_initial_message)])
    )

    logger.info("=============================================")
    logger.info("          PROMPT OPTIMIZATION COMPLETE         ")
    logger.info("=============================================")

    if final_optimization_response.status == "success" and final_optimization_response.final_content:
        print("\n--- Optimized Instruction Result ---")
        print(final_optimization_response.final_content)
    else:
        print(f"\n--- Instruction Optimization Failed ---")
        print(f"Status: {final_optimization_response.status}")
        print(f"Content: {final_optimization_response.final_content}")

if __name__ == "__main__":
    asyncio.run(main())