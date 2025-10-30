import sys
import os
import asyncio
import json
from loguru import logger
from typing import List
from pydantic import BaseModel

# --- Import our NEW and existing framework classes ---
from astra_framework.manager import WorkflowManager
from astra_framework.builders.workflow_builder import WorkflowBuilder # New Builder
from astra_framework.services.client_factory import LLMClientFactory
from astra_framework.services.tavily_client import TavilyClient
from astra_framework.core.tool import ToolManager

# ==============================================================================
# 1. CONFIGURE LOGGER
# ==============================================================================
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="{time:HH:mm:ss.SSS} | {level: <8} | {name: <15}:{function: <15}:{line: >3} - {message}",
    colorize=True
)

# ==============================================================================
# 2. DEFINE DATA MODELS FOR THE AGENT
# ==============================================================================
# These models define the data structure the agent must gather and use.

class Article(BaseModel):
    topic: str
    title: str
    summary: str
    url: str
    published_date: str

class NewsletterPayload(BaseModel):
    main_editorial: str
    articles: List[Article]

# ==============================================================================
# 3. DEFINE TOOLS FOR THE AUTONOMOUS AGENT
# ==============================================================================
# The agent will decide when and how to use these tools to achieve its goal.
tool_manager = ToolManager()
tavily_client = TavilyClient()

@tool_manager.register
def search_the_web(query: str) -> str:
    """
    Searches the web for a given query using the Tavily API.
    :param query: The search query.
    """
    logger.info(f"TOOL: Searching the web for '{query}'")
    # The ReAct agent will observe this string output
    return json.dumps(tavily_client.search(query))

@tool_manager.register
def generate_html_newsletter(payload: NewsletterPayload) -> str:
    """
    Generates a final HTML newsletter from a structured payload object.
    This should be the LAST step once all research and writing is complete.
    :param payload: A payload object containing the main editorial and a list of articles.
    """
    logger.info("TOOL: Generating HTML newsletter from structured payload...")
    
    article_html = ""
    for a in payload.articles:
        article_html += f"""
        <div style="border-bottom: 1px solid #eee; padding: 10px; margin-bottom: 10px;">
            <h3>{a.title} (Topic: {a.topic})</h3>
            <p>{a.summary}</p>
            <p><em>Published: {a.published_date}</em></p>
            <a href="{a.url}" target="_blank">Read more</a>
        </div>
        """
    
    html = f"""
    <html>
        <body style="font-family: sans-serif;">
            <h1>Oncology Research Newsletter</h1>
            <h2>Editor's Note</h2>
            <p>{payload.main_editorial}</p>
            <hr/>
            <h2>Featured Research</h2>
            {article_html}
        </body>
    </html>
    """
    return html

# ==============================================================================
# 4. THE NEW MAIN FUNCTION
# ==============================================================================
async def main():
    logger.info("=============================================")
    logger.info("     STARTING AUTONOMOUS REACT WORKFLOW      ")
    logger.info("=============================================")
    
    # --- 1. Load topics from JSON ---
    # Construct an absolute path to the topics file relative to this script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    topics_file_path = os.path.join(script_dir, '..', '..', 'astra_framework', 'topics_cancer.json')
    with open(topics_file_path, 'r') as f:
        topics_data = json.load(f)
    main_topic = topics_data['main_topic']
    sub_topics_list = [t['name'] for t in topics_data['sub_topics']]

    # --- 2. Define the high-level goal for the ReAct Agent ---
    instruction = f"""
    You are an autonomous, expert medical researcher and editor.
    Your goal is to produce a comprehensive HTML newsletter about '{main_topic}'.

    You MUST follow the ReAct pattern: Thought, Action, Observation.
    In EACH turn, you MUST first output your 'Thought', then an 'Action' (tool call), and then observe the 'Observation' (tool output).
    You MUST continue this cycle until the final HTML newsletter is generated.
    DO NOT provide any other text or final answer until the `generate_html_newsletter` tool has been successfully called.

    Here is your process:
    1.  **Thought**: Carefully consider the current state and what needs to be done next to achieve the overall goal. Reflect on previous observations.
        *   Have all sub-topics ({sub_topics_list}) been thoroughly researched, written into `Article` objects, and critiqued for quality?
        *   Collect atleast 5 high-quality `Article` objects for EACH sub-topic.
        *   Is the main editorial written, synthesizing all `Article` objects?
        *   Is it time to call the `generate_html_newsletter` tool with a fully constructed `NewsletterPayload`?
    2.  **Action**: Based on your thought, decide which tool to call and with what arguments. You MUST call a tool in every action step.
        *   Use `search_the_web` to gather information for sub-topics.
        *   Internally, you will process search results to write and critique summaries, storing them as `Article` objects.
        *   Once all `Article` objects are ready and the main editorial is written, call `generate_html_newsletter`.
    3.  **Observation**: The result of your action (tool output) will be provided to you. Use this to inform your next Thought.

    **Detailed Steps for your Thought Process:**
    *   **Data Collection Phase**: For EACH of the sub-topics ({sub_topics_list}), you must perform a full research-write-critique cycle. Your goal during this phase is to create a structured `Article` object for each sub-topic.
        a.  **Research**: Use the `search_the_web` tool. The search results will contain a URL and publication date.
        b.  **Write**: Based on the research, write a detailed summary.
        c.  **Structure**: You MUST create and internally store an `Article` object for the sub-topic, populating the `topic`, `title`, `summary`, `url`, and `published_date` fields.
        d.  **Critique**: Review your summary for quality. If it's not good enough, repeat the process.

    *   **Synthesis Phase**: Once you have a complete list of structured `Article` objects (one for each sub-topic), write a single, cohesive main editorial that synthesizes the key findings.

    *   **Finalization Phase**: Your final step is to call the `generate_html_newsletter` tool.
        a.  To do this, you MUST construct a `NewsletterPayload` object.
        b.  The `main_editorial` field of the payload should be the editorial you just wrote.
        c.  The `articles` field of the payload MUST be the list of structured `Article` objects you created during the data collection phase.

    Your ULTIMATE final answer MUST be the HTML content returned by the `generate_html_newsletter` tool. Do NOT provide any other text as your final answer. Ensure you call `generate_html_newsletter` with the fully constructed `NewsletterPayload`.
    """

    # --- 3. Use the WorkflowBuilder to construct the workflow ---
    builder = WorkflowBuilder("AutonomousResearchWorkflow")
    
    react_workflow = builder.start_with_react_agent(
        agent_name="AutonomousResearcher",
        llm_client=LLMClientFactory.create_client(client_type="ollama", model="qwen3:latest"),
        tools=list(tool_manager.tools.values()),
        instruction=instruction
    ).build()

    # --- 4. Register and run the workflow ---
    manager = WorkflowManager()
    manager.register_workflow(name="react_research_workflow", agent=react_workflow)
    
    session_id = manager.create_session()
    prompt = f"Please begin your research on {main_topic}."
    
    final_response = await manager.run(
        workflow_name="react_research_workflow",
        session_id=session_id,
        prompt=prompt
    )
    
    logger.info("=============================================")
    logger.info("            WORKFLOW COMPLETE             ")
    logger.info("=============================================")
    
    if final_response.status == "success" and isinstance(final_response.final_content, str):
        print("--- Generated HTML Newsletter ---")
        print(final_response.final_content)
        with open("newsletter.html", "w") as f:
            f.write(final_response.final_content)
        print("\nNewsletter saved to newsletter.html")
    else:
        logger.error(f"Workflow failed: Status={final_response.status}, Content={final_response.final_content}")

if __name__ == "__main__":
    asyncio.run(main())
