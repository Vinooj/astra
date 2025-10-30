## `class ChatMessage`

## `class SessionState`

Implements the Blackboard and Observer patterns. It holds the shared 
state and notifies subscribed observers of any changes.

### `def __post_init__`

### `def subscribe`

Subscribes an observer to state changes.

### `def unsubscribe`

Unsubscribes an observer from state changes.

### `def _notify`

Notifies all subscribed observers of a state change.

### `def add_message`

Adds a message to the history and notifies observers.

### `def update_data`

Updates the data dictionary and notifies observers.

