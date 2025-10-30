from dataclasses import dataclass, field
from typing import Any, Dict, List, Callable
from loguru import logger

@dataclass
class ChatMessage:
    role: str  # "user", "agent", "tool"
    content: str

@dataclass
class SessionState:
    """
    Implements the Blackboard and Observer patterns. It holds the shared state 
    and notifies subscribed observers of any changes.
    """
    session_id: str
    history: List[ChatMessage] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    
    # For the Observer pattern
    _observers: List[Callable] = field(default_factory=list, repr=False)

    def __post_init__(self):
        logger.debug(f"SessionState {self.session_id} initialized.")

    def subscribe(self, observer: Callable):
        """Subscribes an observer to state changes."""
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(f"Observer {observer.__name__} subscribed to SessionState {self.session_id}")

    def unsubscribe(self, observer: Callable):
        """Unsubscribes an observer from state changes."""
        self._observers.remove(observer)
        logger.debug(f"Observer {observer.__name__} unsubscribed from SessionState {self.session_id}")

    def _notify(self):
        """Notifies all subscribed observers of a state change."""
        logger.debug(f"Notifying {len(self._observers)} observers of state change.")
        for observer in self._observers:
            observer(self)

    def add_message(self, role: str, content: str):
        """Adds a message to the history and notifies observers."""
        logger.info(f"Adding message to {self.session_id}: {role.upper()}: {content}")
        self.history.append(ChatMessage(role=role, content=content))
        self._notify()

    def update_data(self, key: str, value: Any):
        """Updates the data dictionary and notifies observers."""
        logger.info(f"Updating data in {self.session_id}: setting '{key}'")
        self.data[key] = value
        self._notify()