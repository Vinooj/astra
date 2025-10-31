in run_workflow_parallel_research_react.pyimport sys
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
    format="{time:HH:mm:ss.SSS} | {level: <8} | {name: <15}:"
           "{function: <15}:{line: >3} - {message}",
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
    :param payload: A payload object containing the main editorial and a 
    list of articles.
    """
    logger.info("TOOL: Generating HTML newsletter from structured payload...")
    
    article_html = ""
    for a in payload.articles:
        article_html += f"""
        <div style="border-bottom: 1px solid #eee; padding: 10px; "
                 "margin-bottom: 10px;">
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
    # Construct an absolute path to the topics file relative to this script's 
    # location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    topics_file_path = os.path.join(script_dir, '..', '..', 
                                    'astra_framework', 'topics_cancer.json')
    with open(topics_file_path, 'r') as f:
        topics_data = json.load(f)
    main_topic = topics_data['main_topic']
    sub_topics_list = [t['name'] for t in topics_data['sub_topics']]

    # --- 2. Define the high-level goal for the ReAct Agent ---
    instruction = f"""
    You are an autonomous, expert medical researcher and editor.
    Your goal is to produce a comprehensive HTML newsletter about '{main_topic}'.

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

    # --- 3. Use the WorkflowBuilder to construct the workflow ---
    builder = WorkflowBuilder("AutonomousResearchWorkflow")
    
    react_workflow = builder.start_with_react_agent(
        agent_name="AutonomousResearcher",
        llm_client=LLMClientFactory.create_client(client_type="ollama", 
                                                model="qwen3:latest"),
        tools=list(tool_manager.tools.values()),
        instruction=instruction
    ).build()

    # --- 4. Register and run the workflow ---
    manager = WorkflowManager()
    manager.register_workflow(name="react_research_workflow", 
                              agent=react_workflow)
    
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
        logger.error(f"Workflow failed: Status={final_response.status}, "
                    f"Content={final_response.final_content}")

if __name__ == "__main__":
    asyncio.run(main())
