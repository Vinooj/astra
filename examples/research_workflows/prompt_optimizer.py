# =============================================================================
#  Filename: prompt_optimizer.py
#
#  Short Description: Optimizes the ReAct agent instruction by analyzing LLM's simulated thinking process.
#
#  Creation date: 2025-10-29
#  Author: Asif Qamar
# =============================================================================

import asyncio
import json
import uuid
import sys
from pathlib import Path
from loguru import logger
from typing import Dict, Any, List
import yaml

from astra_framework.services.client_factory import LLMClientFactory
from astra_framework.core.state import SessionState, ChatMessage
from astra_framework.services.base_client import BaseLLMClient
from astra_framework.utils.prompt_loader import PromptLoader

from .models.models import PromptOptimizationResult

# =============================================================================
# 1. CONFIGURE LOGGER
# =============================================================================
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="{time:HH:mm:ss.SSS} | {level: <8} | {name: <15}:{function: <15}:{line: >3} - {message}",
    colorize=True
)
# Add file logging for optimization process
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
logger.add(
    log_dir / "optimization.log",
    level="INFO",
    rotation="10 MB", # Rotate file every 10 MB
    compression="zip", # Compress old log files
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name: <15}:{function: <15}:{line: >3} - {message}"
)

def to_serializable(val: Any) -> Any:
    """Helper to convert objects to a JSON-serializable format."""
    if hasattr(val, 'model_dump'):
        return val.model_dump()
    if hasattr(val, 'dict'):
        return val.dict()
    try:
        return val.__dict__
    except AttributeError:
        return str(val)

# ==============================================================================
# CONFIGURATION
# ==============================================================================
class Config:
    """Centralized configuration"""
    PROMPTS_FILE = Path(__file__).parent / "prompts" / "react_newsletter_prompts.yaml"
    TOPICS_FILE = Path(__file__).parent.parent.parent / "astra_framework" / "topics_cancer.json"
    
    # --- MODIFIED ---
    # Point to a powerful Foundation Model capable of complex critique and refinement.
    # This model will act as the "Optimizer."
    OPTIMIZER_LLM_MODEL = "gemini-2.5-pro" # Or any other powerful model
    
    # The model used for the *simulation* (the agent we are testing)
    SIMULATION_LLM_MODEL = "qwen3:latest" 
    
    # We might need fewer iterations as each refinement step is much more powerful
    MAX_OPTIMIZATION_ITERATIONS = 3
    SIMULATION_DEPTH = 5 # How many steps to simulate the agent for


# ==============================================================================
# NEW "ALL-IN-ONE" OPTIMIZATION PROMPT
# ==============================================================================

# This prompt replaces the 'optimizer_agent' and 'critique_thinking' prompts.
# It's a single, powerful instruction for the Foundation Model.
OPTIMIZER_SYSTEM_PROMPT = """
You are a world-class Prompt Engineering expert, specializing in optimizing ReAct-style agent instructions.

Your goal is to analyze a simulation trace from an agent and systematically improve its instructional prompt.

You will be given:
1.  **The Original Prompt**: The instruction given to the agent.
2.  **The Task Context**: The specific data used to test the prompt.
3.  **The Simulation Trace**: A step-by-step log of the agent's simulated 'Thought', 'Action', and 'Observation' process when it tried to execute the task with the original prompt.

Your task is to:
1.  **Analyze the Trace**: Carefully critique the agent's performance. Identify all logical flaws, inefficiencies, missed steps, or incorrect tool usage.
2.  **Provide Feedback**: Write a concise, actionable critique explaining *what* was wrong with the agent's thinking and *how* it relates to flaws in the original prompt.
3.  **Optimize the Prompt**: Rewrite and improve the **Original Prompt**. Your new prompt should be a complete, standalone instruction that directly fixes the flaws you identified.

**CRITICAL RULES**:
* Do not just give suggestions. You MUST provide the full, rewritten `optimized_prompt`.
* Focus on improving the prompt's clarity, structure, and strategic guidance to lead the agent to a better outcome.
* The `optimized_prompt` should still be a template that can accept the `{main_topic}` and `{sub_topics_list}` variables.
* You MUST return your response as a valid JSON object matching this schema:
    {
      "feedback": "Your detailed analysis and critique...",
      "optimized_prompt": "The full, new, improved prompt text..."
    }
* **Consider Target LLM Limitations**: When optimizing, explicitly consider that the `optimized_prompt` will be executed by a less capable LLM (`qwen3:latest`). Therefore, the optimized prompt must be extremely explicit, highly structured, and potentially more verbose, with clear state-tracking instructions, to leave no room for misinterpretation by the target LLM.
"""


# ==============================================================================
# MAIN OPTIMIZATION WORKFLOW
# ==============================================================================
class PromptOptimizer:
    """Orchestrates the prompt optimization process using a direct refinement loop."""
    
    def __init__(self):
        # The FM that performs the optimization (e.g., Gemini)
        self.optimizer_llm_client: BaseLLMClient = None
        # The client for simulating the target agent (e.g., qwen3)
        self.simulation_llm_client: BaseLLMClient = None 
        
        self.prompt_loader: PromptLoader = None
        self.topics_data: Dict[str, Any] = None
        self.tool_definitions: List[Dict[str, Any]] = None
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("🚀 Initializing Prompt Optimizer...")
        
        # --- MODIFIED ---
        # Create the powerful LLM client for optimization
        self.optimizer_llm_client = LLMClientFactory.create_client(
            client_type="gemini", # Assuming a 'google' client type for Gemini
            model=Config.OPTIMIZER_LLM_MODEL
        )
        
        # Create the LLM client for simulation
        self.simulation_llm_client = LLMClientFactory.create_client(
            client_type="ollama",
            model=Config.SIMULATION_LLM_MODEL
        )
        
        # Load prompts (still needed for the *initial* prompt)
        self.prompt_loader = PromptLoader(Config.PROMPTS_FILE)
        
        # Load topics
        with open(Config.TOPICS_FILE) as f:
            self.topics_data = json.load(f)
        
        # Load tool definitions for the agent being simulated
        self.tool_definitions = self._load_tool_definitions()
        
        logger.success("✅ Initialization complete")

    async def _simulate_react_agent_thinking(
        self,
        instruction_to_simulate: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Simulates ReAct agent's thinking process.
        (This is the same logic as before, just moved into this class)
        """
        logger.info("🧪 Simulating ReAct agent thinking...")
        
        # Format instruction with context
        try:
            full_instruction = instruction_to_simulate.format(**context)
        except KeyError as e:
            return f"Error: Missing template variable: {e}"
        
        # Create simulation state
        session_state = SessionState(session_id=str(uuid.uuid4()))
        session_state.add_message(
            role="user",
            content=f"Please begin research on {context['main_topic']}."
        )
        
        # Run simulation
        thinking_trace = []
        execution_history = [
            ChatMessage(role="system", content=full_instruction)
        ] + session_state.history
        
        for iteration in range(Config.SIMULATION_DEPTH):
            logger.debug(f"Simulation iteration {iteration + 1}/{Config.SIMULATION_DEPTH}")
            
            # Use the *simulation* client
            llm_response = await self.simulation_llm_client.generate(
                execution_history,
                tools=self.tool_definitions
            )
            
            # (Rest of the simulation logic is identical to your original code)
            if isinstance(llm_response, dict) and "tool_calls" in llm_response:
                tool_calls = llm_response["tool_calls"]
                reasoning = llm_response.get("content", "")
                
                thinking_trace.append(f"**Iteration {iteration + 1}")
                thinking_trace.append(f"Thought: {reasoning}")
                thinking_trace.append(f"Action: {json.dumps(tool_calls, indent=2, default=to_serializable)}")
                thinking_trace.append("Observation: [Simulated - tool not executed]")
                
                execution_history.append(
                    ChatMessage(role="assistant", content=reasoning, tool_calls=tool_calls)
                )
                execution_history.append(
                    ChatMessage(role="tool", content="Simulated tool result")
                )
                
            elif isinstance(llm_response, str):
                thinking_trace.append(f"**Iteration {iteration + 1}")
                thinking_trace.append(f"Response: {llm_response}")
                
                if "final answer" in llm_response.lower():
                    thinking_trace.append("[Agent believes task is complete]")
                    break
                    
                execution_history.append(
                    ChatMessage(role="assistant", content=llm_response)
                )
        
        return "\n\n".join(thinking_trace)

    async def _get_refinement(
        self,
        original_prompt: str,
        context: Dict[str, Any],
        simulation_trace: str
    ) -> PromptOptimizationResult:
        """
        Calls the Foundation Model to get a critique and a new, optimized prompt.
        """
        logger.info("🧠 Asking Optimizer FM for critique and refinement...")

        # Create the "All-in-One" prompt for the Optimizer FM
        user_content = f"""
        **Original Prompt:**
        ```
        {original_prompt}
        ```

        **Task Context:**
        ```json
        {json.dumps(context, indent=2)}
        ```

        **Simulation Trace:**
        ```
        {simulation_trace}
        ```
        
        Please provide your analysis and the new prompt in the required JSON format.
        """
        
        messages = [
            ChatMessage(role="system", content=OPTIMIZER_SYSTEM_PROMPT),
            ChatMessage(role="user", content=user_content)
        ]
        
        # Call the Optimizer FM (e.g., Gemini)
        response_str = await self.optimizer_llm_client.generate(
            messages,
            json_response=True # Request JSON output if the client supports it
        )
        
        try:
            # Parse the JSON response
            response_data = json.loads(str(response_str))
            result = PromptOptimizationResult(
                feedback=response_data.get("feedback", "No feedback provided."),
                optimized_prompt=response_data.get("optimized_prompt", original_prompt)
            )
            
            if result.optimized_prompt == original_prompt:
                logger.warning("Optimizer did not provide a new prompt.")

            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from optimizer: {e}")
            logger.error(f"Raw response: {response_str}")
            # Return the original prompt to avoid crashing
            return PromptOptimizationResult(
                feedback=f"Error: Failed to get refinement. Raw response: {response_str}",
                optimized_prompt=original_prompt
            )

    def _load_tool_definitions(self) -> list:
        """Load tool schemas for the research agent"""
        # (This is identical to your original code)
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_the_web",
                    "description": "Search for information using Tavily API",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_html_newsletter",
                    "description": "Generate final HTML newsletter",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "payload": {
                                "type": "object",
                                "description": "Newsletter content",
                                "properties": {
                                    "main_editorial": {"type": "string"},
                                    "articles": {"type": "array"}
                                }
                            }
                        },
                        "required": ["payload"]
                    }
                }
            }
        ]
    
    def _get_context(self) -> Dict[str, Any]:
        """Extract context from topics data"""
        # (This is identical to your original code)
        return {
            "main_topic": self.topics_data["main_topic"],
            "sub_topics_list": [t["name"] for t in self.topics_data["sub_topics"]]
        }
    
    async def optimize(self, prompt_version: str = "react_researcher_v1") -> PromptOptimizationResult:
        """
        Run the new optimization workflow.
        """
        logger.info(f"🎯 Starting optimization for: {prompt_version}")
        
        context = self._get_context()
        
        # Get initial UNFORMATTED prompt template
        current_prompt_template = self.prompt_loader.get_prompt(prompt_version)
        
        all_feedback = []
        final_result = None

        for i in range(Config.MAX_OPTIMIZATION_ITERATIONS):
            logger.info(f"--- Iteration {i + 1}/{Config.MAX_OPTIMIZATION_ITERATIONS} ---")
            
            # 1. SIMULATE
            # The simulation function will format the template with the context
            simulation_trace = await self._simulate_react_agent_thinking(
                current_prompt_template,
                context
            )
            
            # 2. REFINE
            refinement_result = await self._get_refinement(
                current_prompt_template,
                context,
                simulation_trace
            )
            
            # 3. ITERATE
            # The new optimized prompt becomes the template for the next iteration
            current_prompt_template = refinement_result.optimized_prompt
            all_feedback.append(f"**Iteration {i + 1} Feedback:**\n{refinement_result.feedback}")
            
            logger.success(f"Iteration {i + 1} refinement complete.")
            final_result = refinement_result # Store the latest result

        logger.success("✨ Optimization complete!")
        
        # Combine all feedback for the final report
        if final_result:
            final_result.feedback = "\n\n".join(all_feedback)
        
        return final_result


# ==============================================================================
# ENTRY POINT
# ==============================================================================
async def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("PROMPT OPTIMIZATION WORKFLOW (Refactored)")
    logger.info("=" * 60)
    
    try:
        # Create and initialize optimizer
        optimizer = PromptOptimizer()
        await optimizer.initialize()
        
        # Run optimization
        result = await optimizer.optimize(prompt_version="react_researcher_v1")
        
        # Display results
        print("\n" + "=" * 60)
        print("OPTIMIZATION RESULTS")
        print("=" * 60)
        print("\n--- Final Optimized Prompt ---")
        print(result.optimized_prompt)
        print("\n--- Full Optimization Feedback ---")
        print(result.feedback)
        
        # Optionally save to file
        output_file = Path(__file__).parent / "prompts" / "optimized_prompts" / f"optimized_{Config.OPTIMIZER_LLM_MODEL}.yaml"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            yaml.dump({
                "version": f"optimized_by_{Config.OPTIMIZER_LLM_MODEL}",
                "model": Config.SIMULATION_LLM_MODEL, # Note which model this prompt is for
                "prompt": result.optimized_prompt,
                "feedback": result.feedback
            }, f)
        
        logger.success(f"💾 Saved to: {output_file}")
        
    except Exception as e:
        logger.exception(f"❌ Optimization failed: {e}")
        raise


if __name__ == "__main__":
    # You'll need to define the 'models.py' file with the pydantic model
    # Example models.py:
    # from pydantic import BaseModel
    # class PromptOptimizationResult(BaseModel):
    #   feedback: str
    #   optimized_prompt: str
    
    asyncio.run(main())
