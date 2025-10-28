import sys
import asyncio
from loguru import logger
from pydantic import BaseModel
from typing import List, Callable, Optional

# --- Import our framework classes ---
from astra_framework.manager import WorkflowManager
from astra_framework.agents.llm_agent import LLMAgent
from astra_framework.agents.loop_agent import LoopAgent
from astra_framework.agents.sequential_agent import SequentialAgent
from astra_framework.services.ollama_client import OllamaClient
from astra_framework.services.tavily_client import TavilyClient
from astra_framework.core.state import SessionState

# ==============================================================================
# 1. CONFIGURE LOGGER
# ==============================================================================
logger.remove()
logger.add(
    sys.stderr,
    level="DEBUG",
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

# ==============================================================================
# 3. DEFINE THE WORKFLOW
# ==============================================================================
async def main():
    logger.info("============================================")
    logger.info("     STARTING ASTRA ONCOLOGY RESEARCH WORKFLOW       ")
    logger.info("============================================")
    
    # --- 1. Create services ---
    manager = WorkflowManager()
    ollama_llm = OllamaClient(model="qwen3:latest")
    tavily_client = TavilyClient()

    # --- 2. Define tools ---
    def search_the_web(query: str) -> List[dict]:
        """Searches the web for a given query using the Tavily API."""
        return tavily_client.search(query)

    # --- 3. Define Specialist Agents ---
    research_agent = LLMAgent(
        agent_name="ResearchAgent",
        llm_client=ollama_llm,
        tools=[search_the_web],
        instruction="You are an expert medical research agent. Your target audience is oncologists. Find 5 recent, highly-qualified scientific papers or clinical trial results on the given subject. You must return a list of these articles in the structured_output format.",
        output_structure=ArticleList
    )

    writer_agent = LLMAgent(
        agent_name="WriterAgent",
        llm_client=ollama_llm,
        tools=[],
        instruction="You are a medical writer specializing in oncology. The user will provide a JSON object with a list of articles. Your job is to write a comprehensive editorial synthesizing the findings for an oncologist audience. Then, for each article, create a new summary. Your final answer must be in the structured_output format, including the editorial and the list of articles, ensuring you carry over the original 'content', 'url', 'title', and 'published_date' for each article along with your new summary.",
        output_structure=FinalReport
    )

    critique_agent = LLMAgent(
        agent_name="CritiqueAgent",
        llm_client=ollama_llm,
        tools=[],
        instruction="You are a senior oncologist and editor for a medical journal. The user will provide a JSON object containing a final report. Your job is to meticulously review the report for quality, accuracy, and relevance to a practicing oncologist. If the report is perfect and ready for publication, set 'approved' to true. Otherwise, set 'approved' to false and provide specific, constructive feedback on how to improve it. Your response MUST be in the structured_output format.",
        output_structure=CritiqueResult
    )

    # --- 4. Define the Loop Exit Condition ---
    def critique_is_approved(state: SessionState) -> bool:
        last_message = state.history[-1]
        # The critique agent's structured output is now the last message in the state
        if last_message.role == "user":
            try:
                critique = CritiqueResult.model_validate_json(last_message.content)
                if critique.approved:
                    logger.success("Critique approved. Exiting loop.")
                    return True
                else:
                    logger.warning(f"Critique not approved. Feedback: {critique.feedback}")
                    return False
            except Exception as e:
                logger.error(f"Could not parse critique result: {e}")
                return False
        return False

    # --- 5. Compose the Workflow ---
    # The sequence of operations is now its own agent
    research_sequence = SequentialAgent(
        agent_name="ResearchSequence",
        children=[research_agent, writer_agent, critique_agent],
        keep_alive_state=True
    )

    # The LoopAgent now contains the entire sequence as its single child
    research_loop = LoopAgent(
        agent_name="ResearchAndWriteLoop",
        child=research_sequence,
        max_loops=2, # Allow for one round of feedback
        exit_condition=critique_is_approved
    )

    # --- 6. Register Workflow(s) with the Manager ---
    manager.register_workflow(name="research_workflow", agent=research_loop)
    
    # --- 7. Execute ---
    session_id = manager.create_session()
    prompt = "The latest advancements in immunotherapy for non-small cell lung cancer."
    
    final_response = await manager.run(
        workflow_name="research_workflow",
        session_id=session_id,
        prompt=prompt
    )
    
    logger.info("============================================")
    logger.info("            WORKFLOW COMPLETE             ")
    logger.info("============================================")
    
    print(f"\nWorkflow finished.\nInitial Prompt: {prompt}\n")
    
    # Retrieve the final state to get the latest FinalReport
    final_state = manager.get_session_state(session_id)
    final_report = None
    for msg in reversed(final_state.history):
        if msg.role == "user":
            try:
                report = FinalReport.model_validate_json(msg.content)
                final_report = report
                break
            except Exception:
                continue
    
    if final_report:
        print("--- Editorial ---")
        print(final_report.editorial)
        print("\n--- Sourced Articles ---")
        for i, article in enumerate(final_report.articles):
            print(f"  {i+1}. {article.title}")
            print(f"     URL: {article.url}")
            print(f"     Summary: {article.summary}")
        print("\n--- Full Report (JSON) (from Session State) ---")
        print(final_report.model_dump_json(indent=2))
    elif "last_agent_response" in final_state.data:
        last_agent_output = final_state.data["last_agent_response"]
        if isinstance(last_agent_output, BaseModel):
            print("--- Final Output (JSON) (from Session State) ---")
            print(last_agent_output.model_dump_json(indent=2))
    
    # Also print the final_response from the LoopAgent (which might be a CritiqueResult)
    if isinstance(final_response.final_content, BaseModel):
        print("\n--- LoopAgent's Final Response (JSON) ---")
        print(final_response.final_content.model_dump_json(indent=2))
    else:
        print(f"\n--- LoopAgent's Final Answer ---\n{final_response.final_content}")

if __name__ == "__main__":
    # Note: You need to have the TAVILY_API_KEY environment variable set for this to work.
    asyncio.run(main())