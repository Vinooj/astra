from dataclasses import dataclass
from typing import Dict, Any, Optional

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
    metadata: Optional[Dict[str, Any]] = None