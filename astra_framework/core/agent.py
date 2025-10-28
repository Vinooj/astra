from abc import ABC, abstractmethod
from typing import Optional, Type
from pydantic import BaseModel
from astra_framework.core.state import SessionState
from astra_framework.core.models import AgentResponse

class BaseAgent(ABC):
    """The abstract base class for all agents."""
    def __init__(self, agent_name: str, output_structure: Optional[Type[BaseModel]] = None, keep_alive_state: bool = False):
        self.agent_name = agent_name
        self.output_structure = output_structure
        self.keep_alive_state = keep_alive_state

    @abstractmethod
    async def execute(self, state: SessionState) -> AgentResponse:
        pass