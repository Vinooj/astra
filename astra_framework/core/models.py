from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ToolCall:
    """(Command Pattern) Encapsulates a request to call a tool."""
    name: str
    args: Dict[str, Any]

@dataclass
class AgentResponse:
    """Standard response from any agent execution."""
    status: str
    final_content: str