from loguru import logger
from typing import List, Callable
from pydantic import BaseModel
from astra_framework.core.agent import BaseAgent
from astra_framework.core.state import SessionState, ChatMessage
from astra_framework.core.models import AgentResponse

class LoopAgent(BaseAgent):
    """
    Executes a single child agent in a loop.
    The loop continues until a max number of iterations is reached or an exit condition is met.
    This agent manages a feedback loop by incorporating the output of the child agent
    as feedback for the next iteration.
    """
    def __init__(self, 
                 agent_name: str, 
                 child: BaseAgent, 
                 max_loops: int = 3,
                 exit_condition: Callable[[SessionState], bool] = None,
                 keep_alive_state: bool = False):
        super().__init__(agent_name, keep_alive_state=keep_alive_state)
        self.child = child
        self.max_loops = max_loops
        self.exit_condition = exit_condition
        logger.debug(f"LoopAgent '{agent_name}' initialized with child '{child.agent_name}' and max_loops={max_loops}.")

    async def execute(self, state: SessionState) -> AgentResponse:
        logger.info(f"--- Executing LoopAgent: {self.agent_name} ---")
        
        if not state.history:
            return AgentResponse(status="error", final_content="LoopAgent requires an initial prompt.")
        original_prompt = state.history[0].content
        
        final_response = None
        loop_state = state

        for i in range(self.max_loops):
            logger.info(f"[{self.agent_name}] Starting loop {i+1}/{self.max_loops}")

            # Execute the single child agent
            response = await self.child.execute(loop_state)
            final_response = response

            # The exit condition is checked on the state *after* the child has run
            if self.exit_condition and self.exit_condition(loop_state):
                logger.success(f"[{self.agent_name}] Exit condition met. Exiting loop.")
                return final_response # Return the successful response from the child
            
            # Prepare for the next loop if we haven't reached the max
            if i < self.max_loops - 1:
                last_agent_output = final_response.final_content
                feedback = str(last_agent_output)
                if isinstance(last_agent_output, BaseModel):
                    feedback = last_agent_output.model_dump_json()
                
                logger.warning(f"[{self.agent_name}] Loop did not exit. Incorporating feedback for next iteration.")
                
                if not self.keep_alive_state:
                    # Clear history and add new prompt for the next iteration
                    loop_state.history.clear()
                    new_prompt = f"Original request: {original_prompt}\n\nPlease revise your work based on the following feedback: {feedback}"
                    loop_state.add_message(role="user", content=new_prompt)
                else:
                    new_prompt = f"Original request: {original_prompt}\n\nPlease revise your work based on the following feedback: {feedback}"
                    loop_state.add_message(role="user", content=new_prompt)
            else:
                logger.warning(f"[{self.agent_name}] Max loops reached ({self.max_loops}). Exiting without approval.")

        logger.success(f"LoopAgent '{self.agent_name}' finished.")
        return final_response
