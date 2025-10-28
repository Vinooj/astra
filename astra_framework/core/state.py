from dataclasses import dataclass, field
from typing import Any, Dict, List
from loguru import logger

@dataclass
class ChatMessage:
    role: str  # "user", "agent", "tool"
    content: str

@dataclass
class SessionState:
    """Implements the Blackboard pattern as a pass-by-reference Context Object."""
    session_id: str
    history: List[ChatMessage] = field(default_factory=list)
    # The 'blackboard' itself. Agents read/write here.
    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        logger.debug(f"SessionState {self.session_id} initialized.")

    def add_message(self, role: str, content: str):
        logger.info(f"Adding message to {self.session_id}: {role.upper()}: {content}")
        self.history.append(ChatMessage(role=role, content=content))