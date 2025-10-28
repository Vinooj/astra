import sys
import asyncio
import re
from loguru import logger
from typing import List, Callable, Dict, Any, Optional

# --- Web Server Imports ---
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# --- Observability Imports ---
import phoenix as px
from openinference.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

# --- Astra Framework Imports ---
from astra_framework.manager import WorkflowManager
from astra_framework.agents.llm_agent import LLMAgent
from astra_framework.agents.sequential_agent import SequentialAgent
from astra_framework.services.llm_client import BaseLLMClient
from astra_framework.core.models import AgentResponse
from astra_framework.core.state import ChatMessage

# ==============================================================================
# 1. CONFIGURE PHOENIX OBSERVABILITY
# ==============================================================================
# Launch Phoenix in the background
px.launch_app()

# Set up an OTLP endpoint and a tracer provider
endpoint = "http://127.0.0.1:6006/v1/traces"
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint)))

# ==============================================================================
# 2. CONFIGURE LOGGER
# ==============================================================================
logger.remove()
logger.add(
    sys.stderr,
    level="DEBUG",
    format="{time:HH:mm:ss.SSS} | {level: <8} | {name: <15}:{function: <15}:{line: >3} - {message}",
    colorize=True
)

# ==============================================================================
# 3. DEFINE A2A PROTOCOL MODELS (for FastAPI)
# ==============================================================================
# Pydantic models define the expected JSON request and response shapes
class A2AInvokeRequest(BaseModel):
    workflow_name: str
    session_id: Optional[str] = None  # Session is optional; we create one if not provided
    prompt: str

class A2AInvokeResponse(BaseModel):
    session_id: str
    content: str
    status: str

# ==============================================================================
# 4. SET UP THE MOCK LLM AND TOOLS (Copied from run_workflow.py)
# ==============================================================================
# This server needs its own LLM client and tools
# In a real app, this would be imported, not re-defined.

class MockLLMClient(BaseLLMClient):
    """A mock LLM that returns the 'dict' structure for tool calls."""
    def __init__(self):
        logger.debug("MockLLMClient initialized.")

    async def generate(self, history: List[ChatMessage], tools: list) -> str | dict:
        await asyncio.sleep(0.1)
        instruction = history[0].content
        last_message = history[-1]

        if last_message.role == "tool":
            return f"Operation complete. The result is {last_message.content}."

        if "add" in instruction:
            user_prompt = history[1].content
            nums = re.findall(r"(\d+)", user_prompt)
            a, b = int(nums[0]), int(nums[1])
            return {"tool_calls": [{"function": {"name": "add", "arguments": {"a": a, "b": b}}}]}

        if "multiply" in instruction:
            last_tool_result = None
            for msg in reversed(history):
                if msg.role == "tool":
                    last_tool_result = int(msg.content)
                    break
            if not last_tool_result:
                return "Error: I am the multiplier, but no previous tool result was found."
            user_prompt = history[1].content
            c = int(re.findall(r"(\d+)", user_prompt)[-1])
            return {"tool_calls": [{"function": {"name": "multiply", "arguments": {"a": last_tool_result, "b": c}}}]}
        
        return "I am not sure what to do."

def add(a: int, b: int) -> int:
    """Adds two integers."""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiplies two integers."""
    return a * b

# ==============================================================================
# 5. INITIALIZE THE ASTRA FRAMEWORK AND WEB SERVER
# ==============================================================================
logger.info("Initializing Astra Framework for A2A Server...")

# --- Create the Facade ---
manager = WorkflowManager()

# --- Create the LLM service ---
mock_llm = MockLLMClient()

# --- Define Specialist Agents ---
adder_agent = LLMAgent(
    agent_name="AdderAgent",
    llm_client=mock_llm,
    tools=[add],
    instruction="You are an adder agent. Your job is to add the two numbers in the user's prompt."
)

multiplier_agent = LLMAgent(
    agent_name="MultiplierAgent",
    llm_client=mock_llm,
    tools=[multiply],
    instruction="You are a multiplier agent. Your job is to multiply the last tool result by the last number in the user's prompt."
)

# --- Compose Workflow ---
math_workflow = SequentialAgent(
    agent_name="MathWorkflow",
    children=[adder_agent, multiplier_agent]
)

# --- Register Workflow(s) with the Manager ---
manager.register_workflow(name="math_workflow", agent=math_workflow)

logger.info("Astra Framework initialized. Starting FastAPI server...")

# --- Create the FastAPI app ---
app = FastAPI(
    title="Astra Agentic Framework Server",
    description="Exposes Astra workflows via the A2A protocol."
)

# Instrument the FastAPI app
FastAPIInstrumentor().instrument_app(app, tracer_provider=tracer_provider)

# ==============================================================================
# 6. DEFINE THE A2A SERVER ENDPOINTS
# ==============================================================================

@app.get("/", summary="Get Agent Card")
async def get_agent_card():
    """
    Returns the 'Agent Card', a specification of all workflows
    this server provides.
    """
    logger.info("GET / (Agent Card) requested.")
    return {
        "server_name": "Astra A2A Server",
        "available_workflows": [
            {
                "name": wf_name,
                "description": f"Entry point for the '{wf_name}' agent."
            } for wf_name in manager.workflows.keys()
        ]
    }

@app.post("/invoke", summary="Invoke an Agent Workflow", response_model=A2AInvokeResponse)
async def handle_a2a_invoke(request: A2AInvokeRequest):
    """
    This is the main A2A endpoint. It receives a request,
    translates it for the WorkflowManager, runs the agent,
    and translates the response back to JSON.
    """
    logger.info(f"POST /invoke requested for workflow: {request.workflow_name}")
    logger.debug(f"Request: {request}")
    
    try:
        # 1. Get or create the session
        session_id = request.session_id or manager.create_session()
        
        # 2. Translate A2A request -> manager.run() call
        response: AgentResponse = await manager.run(
            workflow_name=request.workflow_name,
            session_id=session_id,
            prompt=request.prompt
        )
        
        if response.status == "error":
            # Pass framework-level errors (like 'workflow not found')
            raise HTTPException(status_code=404, detail=response.final_content)

        # 3. Translate AgentResponse -> A2AInvokeResponse
        invoke_response = A2AInvokeResponse(
            session_id=session_id,
            content=response.final_content,
            status=response.status
        )
        logger.debug(f"Response: {invoke_response}")
        return invoke_response
        
    except Exception as e:
        logger.error(f"Unhandled error in /invoke: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# 7. RUN THE SERVER
# ==============================================================================
if __name__ == "__main__":
    logger.info("Starting Uvicorn server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)