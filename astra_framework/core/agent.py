from abc import ABC, abstractmethod
from typing import Optional, Type, List
from pydantic import BaseModel
from astra_framework.core.state import SessionState, ChatMessage
from astra_framework.core.models import AgentResponse
import json

class BaseAgent(ABC):
    """The abstract base class for all agents."""
    def __init__(self, agent_name: str, output_structure: Optional[Type[BaseModel]] = None, keep_alive_state: bool = False):
        self.agent_name = agent_name
        self.output_structure = output_structure
        self.keep_alive_state = keep_alive_state

    @abstractmethod
    async def execute(self, state: SessionState) -> AgentResponse:
        pass

    def _sync_history_to_state(self, state: SessionState, execution_history: List[ChatMessage], initial_history_len: int):
        """Synchronizes the agent's execution history back to the main session state."""
        for msg in execution_history[initial_history_len:]:
            state.add_message(role=msg.role, content=msg.content, tool_calls=msg.tool_calls, tool_call_id=msg.tool_call_id, name=msg.name)

    def _validate_structured_output(self, content: str) -> str:
        """Validates content against the agent's output_structure."""
        if not self.output_structure:
            return content # No validation needed if no structure defined
        try:
            validated_model = self.output_structure.model_validate_json(content)
            return validated_model.model_dump_json()
        except Exception as e:
            raise ValueError(f"Failed to validate structured output: {e}. Content: {content}")

    async def _get_summary(self, history: List[ChatMessage]) -> str:
        """Generates a summary of the agent's execution history."""
        # For now, a simple summary. A more advanced version would use an LLM.
        if not history:
            return "No history available."
        
        summary_content = []
        for msg in history[-5:]:
            summary_content.append(f"{msg.role.upper()}: {msg.content}")
        
        return "Summary of last 5 messages:\n" + "\n".join(summary_content)