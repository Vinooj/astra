import sys
import asyncio
import json
from loguru import logger
from pydantic import BaseModel
from typing import List, Callable, Optional, Type

# --- Import our framework classes ---
from astra_framework.manager import WorkflowManager
from astra_framework.agents.llm_agent import LLMAgent
from astra_framework.agents.loop_agent import LoopAgent
from astra_framework.agents.sequential_agent import SequentialAgent
from astra_framework.agents.parallel_agent import ParallelAgent
from astra_framework.agents.dynamic_workflow_agent import DynamicWorkflowAgent
from astra_framework.services.ollama_client import OllamaClient
from astra_framework.services.tavily_client import TavilyClient
from astra_framework.core.state import SessionState
from astra_framework.core.workflow_models import WorkflowPlan, AgentConfig

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
# 2. DEFINE PYDANTIC MODELS FOR STRUCTURED OUTPUT (used by LLMAgents)
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
# 3. DEFINE TOOLS (used by LLMAgents)
# ==============================================================================
def search_the_web(query: str) -> List[dict]:
    """Searches the web for a given query using the Tavily API."""
    # This will be mocked in the DynamicWorkflowAgent's tool registry for planning
    # In a real scenario, the DWA would pass this tool to the LLMAgent it creates
    return TavilyClient().search(query)

# ==============================================================================
# 4. DEFINE THE DYNAMIC WORKFLOW AGENT
# ==============================================================================
async def main():
    logger.info("============================================")
    logger.info("     STARTING DYNAMIC WORKFLOW DEMO         ")
    logger.info("============================================")
    
    # --- 1. Create services ---
    manager = WorkflowManager()
    ollama_llm = OllamaClient(model="qwen3:latest")
    tavily_client = TavilyClient() # Used by the actual search tool

    # --- 2. Instantiate the DynamicWorkflowAgent ---
    # This agent's LLM will generate the workflow plan
    dynamic_agent = DynamicWorkflowAgent(
        agent_name="DynamicPlanner",
        llm_client=ollama_llm,
        tools=[search_the_web], # Tools the DWA's LLM can suggest for other agents
        instruction="You are an expert workflow designer. Your goal is to create an efficient and effective multi-agent workflow to achieve the user's request. You have access to LLMAgent, SequentialAgent, ParallelAgent, and LoopAgent. You can also use the 'search_the_web' tool. Your output MUST be a WorkflowPlan.",
        output_structure=WorkflowPlan,
        keep_alive_state=True # Keep state for the DWA's own planning process
    )
    # Register output structures that the DWA's LLM can reference in its plan
    dynamic_agent.register_output_structure("ArticleList", ArticleList)
    dynamic_agent.register_output_structure("FinalReport", FinalReport)
    dynamic_agent.register_output_structure("CritiqueResult", CritiqueResult)
    dynamic_agent.register_output_structure("Editorial", Editorial)
    dynamic_agent.register_output_structure("Newsletter", Newsletter)

    # --- 3. Register the DynamicWorkflowAgent as a workflow ---
    manager.register_workflow(name="dynamic_workflow_planner", agent=dynamic_agent)
    
    # --- 4. Define the user's high-level goal ---
    user_prompt = "Research the main topic: Artificial Intelligence in Cancer Care, focusing on 5 sub-topics: Cancer Research, Cancer Prevention, Early Detection and Diagnosis, Treatment Planning, and Clinical Trials. For each sub-topic, research, write a report, and critique it. Then, create an overall editorial summarizing all reports, and finally generate an HTML newsletter combining the editorial and all reports."

    # --- 5. Execute the DynamicWorkflowAgent ---
    session_id = manager.create_session()
    logger.info(f"--- Running DynamicWorkflowAgent for session {session_id} ---")
    
    final_response = await manager.run(
        workflow_name="dynamic_workflow_planner",
        session_id=session_id,
        prompt=user_prompt
    )
    
    logger.info("============================================")
    logger.info("            DYNAMIC WORKFLOW COMPLETE       ")
    logger.info("============================================")
    
    print(f"\nWorkflow finished.\nInitial Prompt: {user_prompt}\n")
    
    if isinstance(final_response.final_content, Newsletter):
        print("--- Generated HTML Newsletter ---")
        print(final_response.final_content.html_content)
        with open("dynamic_newsletter.html", "w") as f:
            f.write(final_response.final_content.html_content)
        print("\nNewsletter saved to dynamic_newsletter.html")
    elif isinstance(final_response.final_content, BaseModel):
        print("--- Final Structured Output (JSON) ---")
        print(final_response.final_content.model_dump_json(indent=2))
    else:
        print(f"--- Final Output ---\n{final_response.final_content}")

if __name__ == "__main__":
    # Note: You need to have the TAVILY_API_KEY environment variable set for this to work.
    asyncio.run(main())
