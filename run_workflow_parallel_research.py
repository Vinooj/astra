import sys
import asyncio
import json
from loguru import logger
from pydantic import BaseModel
from typing import List, Callable, Optional

# --- Import our framework classes ---
from astra_framework.manager import WorkflowManager
from astra_framework.agents.llm_agent import LLMAgent
from astra_framework.agents.loop_agent import LoopAgent
from astra_framework.agents.sequential_agent import SequentialAgent
from astra_framework.agents.parallel_agent import ParallelAgent
from astra_framework.services.ollama_client import OllamaClient
from astra_framework.services.tavily_client import TavilyClient
from astra_framework.core.state import SessionState

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
# 2. DEFINE PYDANTIC MODELS FOR STRUCTURED OUTPUT
# ==============================================================================
class Article(BaseModel):
    url: str
    title: str
    content: str
    published_date: Optional[str] = None
    summary: Optional[str] = None

class ArticleList(BaseModel):
    articles: List[Article]

class FinalReport(BaseModel):
    editorial: str
    articles: List[Article]

class CritiqueResult(BaseModel):
    approved: bool
    feedback: str

class Editorial(BaseModel):
    main_title: str
    editorial_content: str

class Newsletter(BaseModel):
    html_content: str

# ==============================================================================
# 3. DEFINE THE DYNAMIC WORKFLOW
# ==============================================================================
def create_research_loop(topic: dict, ollama_llm: OllamaClient, tavily_client: TavilyClient) -> LoopAgent:
    """Creates a research/write/critique loop for a single topic."""
    topic_name = topic['name']
    topic_query = topic['query']

    # --- 1. Define tools ---
    def search_the_web(query: str) -> List[dict]:
        """Searches the web for a given query using the Tavily API."""
        return tavily_client.search(query)

    # --- 2. Define Specialist Agents ---
    research_agent = LLMAgent(
        agent_name=f"ResearchAgent_{topic_name}",
        llm_client=ollama_llm,
        tools=[search_the_web],
        instruction=f"You are an expert medical research agent. Your target audience is oncologists. Find 5 recent, highly-qualified scientific papers or clinical trial results on the given subject: {topic_query}. You must return a list of these articles in the structured_output format.",
        output_structure=ArticleList
    )

    writer_agent = LLMAgent(
        agent_name=f"WriterAgent_{topic_name}",
        llm_client=ollama_llm,
        tools=[],
        instruction="You are a medical writer specializing in oncology. The user will provide a JSON object with a list of articles. Your job is to write a comprehensive editorial synthesizing the findings for an oncologist audience. Then, for each article, create a new summary. Your final answer must be in the structured_output format, including the editorial and the list of articles, ensuring you carry over the original 'content', 'url', 'title', and 'published_date' for each article along with your new summary.",
        output_structure=FinalReport
    )

    critique_agent = LLMAgent(
        agent_name=f"CritiqueAgent_{topic_name}",
        llm_client=ollama_llm,
        tools=[],
        instruction="You are a senior oncologist and editor for a medical journal. The user will provide a JSON object containing a final report. Your job is to meticulously review the report for quality, accuracy, and relevance to a practicing oncologist. If the report is perfect and ready for publication, set 'approved' to true. Otherwise, set 'approved' to false and provide specific, constructive feedback on how to improve it. Your response MUST be in the structured_output format.",
        output_structure=CritiqueResult
    )

    # --- 3. Define the Loop Exit Condition ---
    def critique_is_approved(state: SessionState) -> bool:
        last_message = state.history[-1]
        if last_message.role == "user":
            try:
                critique = CritiqueResult.model_validate_json(last_message.content)
                if critique.approved:
                    logger.success(f"Critique for '{topic_name}' approved. Exiting loop.")
                    return True
                else:
                    logger.warning(f"Critique for '{topic_name}' not approved. Feedback: {critique.feedback}")
                    return False
            except Exception as e:
                logger.error(f"Could not parse critique result for '{topic_name}': {e}")
                return False
        return False

    # --- 4. Compose the Workflow ---
    research_sequence = SequentialAgent(
        agent_name=f"ResearchSequence_{topic_name}",
        children=[research_agent, writer_agent, critique_agent],
        keep_alive_state=True
    )

    research_loop = LoopAgent(
        agent_name=f"ResearchLoop_{topic_name}",
        child=research_sequence,
        max_loops=2,
        exit_condition=critique_is_approved,
        keep_alive_state=True
    )

    return research_loop

async def main():
    logger.info("============================================")
    logger.info("     STARTING PARALLEL RESEARCH WORKFLOW      ")
    logger.info("============================================")
    
    # --- 1. Load topics from JSON ---
    with open('astra_framework/topics_cancer.json', 'r') as f:
        topics_data = json.load(f)
    sub_topics = topics_data['sub_topics']

    # --- 2. Create services ---
    manager = WorkflowManager()
    ollama_llm = OllamaClient(model="qwen3:latest")
    tavily_client = TavilyClient()

    # --- 3. Dynamically create a research loop for each sub-topic ---
    parallel_loops = []
    for topic in sub_topics:
        loop = create_research_loop(topic, ollama_llm, tavily_client)
        parallel_loops.append(loop)

    # --- 4. Create the main parallel agent ---
    parallel_research_agent = ParallelAgent(
        agent_name="ParallelResearchAgent",
        children=parallel_loops
    )

    # --- 5. Define Editor and Newsletter Agents ---
    editor_agent = LLMAgent(
        agent_name="EditorAgent",
        llm_client=ollama_llm,
        tools=[],
        instruction=f"You are a senior editor for a prestigious medical journal. You will be given a list of approved reports on various sub-topics related to '{topics_data['main_topic']}'. Your task is to write a single, cohesive editorial that synthesizes the key findings from all the reports into a compelling narrative for a broad audience of oncologists. Your final answer must be in the structured_output format.",
        output_structure=Editorial
    )

    newsletter_agent = LLMAgent(
        agent_name="NewsletterGeneratorAgent",
        llm_client=ollama_llm,
        tools=[],
        instruction="You are a web designer and content creator. You will be given an editorial and a list of reports. Your job is to generate a visually appealing HTML newsletter that includes the main editorial at the top, followed by sections for each of the sub-topic reports. Each section should be clearly titled and present the information in a clean, readable format. Your final answer must be a single HTML document in the structured_output format.",
        output_structure=Newsletter
    )

    # --- 6. Create the final sequential workflow ---
    final_workflow = SequentialAgent(
        agent_name="FinalWorkflow",
        children=[parallel_research_agent, editor_agent, newsletter_agent],
        keep_alive_state=True
    )

    # --- 7. Register Workflow(s) with the Manager ---
    manager.register_workflow(name="parallel_research_workflow", agent=final_workflow)
    
    # --- 8. Execute ---
    session_id = manager.create_session()
    prompt = f"Generate a newsletter on the main topic: {topics_data['main_topic']}"
    
    final_response = await manager.run(
        workflow_name="parallel_research_workflow",
        session_id=session_id,
        prompt=prompt
    )
    
    logger.info("============================================")
    logger.info("            WORKFLOW COMPLETE             ")
    logger.info("============================================")
    
    print(f"\nWorkflow finished.\nInitial Prompt: {prompt}\n")
    
    # The final_response.final_content will be the newsletter
    if isinstance(final_response.final_content, Newsletter):
        print("--- Generated HTML Newsletter ---")
        print(final_response.final_content.html_content)
        with open("newsletter.html", "w") as f:
            f.write(final_response.final_content.html_content)
        print("\nNewsletter saved to newsletter.html")
    else:
        print("--- Final Output ---")
        print(final_response.final_content)

if __name__ == "__main__":
    # Note: You need to have the TAVILY_API_KEY environment variable set for this to work.
    asyncio.run(main())
