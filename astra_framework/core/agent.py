from abc import ABC, abstractmethod
from typing import Optional, Type
from pydantic import BaseModel
from astra_framework.core.state import SessionState
from astra_framework.core.models import AgentResponse

class BaseAgent(ABC):
    """(Strategy Pattern) The abstract interface for all agents."""
    
    def __init__(self, agent_name: str, output_structure: Optional[Type[BaseModel]] = None):
        self.agent_name = agent_name
        self.output_structure = output_structure

    @abstractmethod
    async def execute(self, state: SessionState) -> AgentResponse:
        """Executes the agent's logic on the shared session state."""
        pass