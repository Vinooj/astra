import asyncio
import json
from loguru import logger
from typing import List, Callable, Optional, Type, Union, Dict, Any
from pydantic import BaseModel

from astra_framework.core.agent import BaseAgent
from astra_framework.core.state import SessionState, ChatMessage
from astra_framework.core.models import AgentResponse
from astra_framework.services.base_client import BaseLLMClient
from astra_framework.core.tool import ToolManager

import re
from typing import Tuple

class ReActAgent(BaseAgent):
    """ReAct agent with support for extended thinking."""
    
    def __init__(self, 
                 agent_name: str, 
                 llm_client: BaseLLMClient,
                 tools: List[Callable],
                 instruction: str,
                 max_iterations: int = 10,
                 output_structure: Optional[Type[BaseModel]] = None,
                 strip_thinking: bool = True,  # NEW
                 thinking_tags: List[str] = None):  # NEW
        super().__init__(agent_name, output_structure)
        self.llm = llm_client
        self.tool_manager = ToolManager(tools)
        self.instruction = instruction
        self.max_iterations = max_iterations
        self.strip_thinking = strip_thinking
        # Support multiple thinking tag formats
        self.thinking_tags = thinking_tags or [
            ('think', 'think'),
            ('thinking', 'thinking'),
            ('reasoning', 'reasoning'),
            ('internal', 'internal')
        ]
    
    def _extract_thinking(self, content: str) -> Tuple[Optional[str], str]:
        """
        Extract thinking/reasoning from content and return (thinking, cleaned_content).
        
        Returns:
            Tuple of (thinking_content, user_facing_content)
        """
        if not self.strip_thinking or not content:
            return None, content
        
        thinking_content = None
        cleaned_content = content
        
        # Try each thinking tag format
        for open_tag, close_tag in self.thinking_tags:
            # Match tags (case-insensitive, handle variations)
            pattern = rf'<{open_tag}>(.*?)</{close_tag}>'
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            
            if matches:
                # Extract all thinking blocks
                thinking_content = '\n'.join(matches)
                # Remove thinking tags from content
                cleaned_content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
                break
        
        # Clean up extra whitespace
        cleaned_content = cleaned_content.strip()
        
        return thinking_content, cleaned_content
    
    def _log_thinking(self, thinking: str):
        """Log thinking content separately for debugging."""
        if thinking:
            logger.debug(f"[{self.agent_name}] 🧠 Internal Thinking:\n{thinking}")
    
    async def execute(self, state: SessionState) -> AgentResponse:
        """Executes the ReAct loop with thinking support."""
        logger.info(f"--- Executing ReActAgent: {self.agent_name} ---")

        system_message = ChatMessage(role="system", content=self.instruction)
        initial_history_len = len(state.history)
        execution_history = [system_message] + state.history.copy()

        for iteration in range(self.max_iterations):
            logger.info(f"[{self.agent_name}] Iteration {iteration+1}/{self.max_iterations}")

            # 1. REASON: Get LLM decision
            llm_response = await self.llm.generate(
                execution_history,
                tools=self.tool_manager.get_tool_definitions()
            )

            # Parse response
            tool_calls = None
            raw_content = None
            thinking = None
            user_content = None
            final_content = None

            if isinstance(llm_response, dict):
                tool_calls = llm_response.get("tool_calls")
                raw_content = llm_response.get("content", "")
                
                # Extract thinking from content
                thinking, user_content = self._extract_thinking(raw_content)
                self._log_thinking(thinking)
                
                # If no tool calls, this might be final answer
                if not tool_calls:
                    final_content = user_content
                    
            elif isinstance(llm_response, str):
                # Extract thinking from string response
                thinking, user_content = self._extract_thinking(llm_response)
                self._log_thinking(thinking)
                final_content = user_content

            # Check for final answer
            if final_content is not None:
                if self._is_final_answer(final_content):
                    # Validate structured output if required
                    if self.output_structure:
                        final_content = self._validate_structured_output(final_content)
                    
                    # Sync history (WITHOUT thinking tags)
                    self._sync_history_to_state(state, execution_history, initial_history_len)
                    state.add_message(role="assistant", content=final_content)
                    
                    logger.success(f"[{self.agent_name}] Task completed")
                    return AgentResponse(
                        status="success", 
                        final_content=final_content,
                        metadata={"thinking": thinking} if thinking else None  # Optional
                    )
                else:
                    # Ambiguous response - prompt for clarification
                    logger.warning(f"[{self.agent_name}] Ambiguous response, requesting clarification")
                    execution_history.append(ChatMessage(
                        role="user",
                        content="Please either use a tool or provide your final answer."
                    ))
                    continue

            # 2. ACT: Execute tools
            if tool_calls:
                # Add assistant message (with user-facing content only, no thinking)
                execution_history.append(ChatMessage(
                    role="assistant",
                    content=user_content or "",  # Cleaned content
                    tool_calls=tool_calls
                ))

                # Execute each tool
                for tool_call in tool_calls:
                    await self._execute_single_tool(tool_call, execution_history)

        # Max iterations reached
        logger.warning(f"[{self.agent_name}] Max iterations reached")
        final_content = await self._get_summary(execution_history)
        
        # Extract thinking from summary too
        thinking, cleaned_final = self._extract_thinking(final_content)
        self._log_thinking(thinking)
        
        self._sync_history_to_state(state, execution_history, initial_history_len)
        state.add_message(role="assistant", content=cleaned_final)
        
        return AgentResponse(
            status="max_iterations_reached",
            final_content=cleaned_final,
            metadata={"thinking": thinking} if thinking else None
        )
    
    async def _execute_single_tool(self, tool_call: Dict, history: List[ChatMessage]):
        """Execute a single tool and add result to history."""
        function_name = tool_call.get("function", {}).get("name")
        function_args = tool_call.get("function", {}).get("arguments", {})
        tool_call_id = tool_call.get("id", f"call_{function_name}")
        
        logger.info(f"[{self.agent_name}] Calling: {function_name}({function_args})")
        
        try:
            result = await self.tool_manager.execute_tool(function_name, function_args)
            content = json.dumps(result) if not isinstance(result, str) else result
            logger.info(f"[{self.agent_name}] Tool succeeded: {function_name}")
        except Exception as e:
            content = f"Error: {str(e)}"
            logger.error(f"[{self.agent_name}] Tool failed: {function_name} - {e}")
        
        history.append(ChatMessage(
            role="tool",
            tool_call_id=tool_call_id,
            name=function_name,
            content=content
        ))
    
    def _is_final_answer(self, content: str) -> bool:
        """Check if content is a final answer."""
        if not content or len(content.strip()) < 10:
            return False
        
        # Heuristics for final answer detection
        final_indicators = [
            "final answer",
            "in conclusion",
            "to summarize",
            "here is the",
            "here's the"
        ]
        
        needs_tool_indicators = [
            "i need to",
            "let me check",
            "i should call",
            "i'll use the"
        ]
        
        content_lower = content.lower()
        
        # Likely needs more tools
        if any(indicator in content_lower for indicator in needs_tool_indicators):
            return False
        
        # Strong final answer indicators
        if any(indicator in content_lower for indicator in final_indicators):
            return True
        
        # Default: if it's substantial content without tool indicators
        return len(content.strip()) > 50


