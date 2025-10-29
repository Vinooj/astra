from astra_framework.core.state import SessionState, ChatMessage

def test_chat_message_creation():
    msg = ChatMessage(role="user", content="hello")
    assert msg.role == "user"
    assert msg.content == "hello"

def test_session_state_creation():
    state = SessionState(session_id="test_session")
    assert state.session_id == "test_session"
    assert state.history == []
    assert state.data == {}

def test_add_message():
    state = SessionState(session_id="test_session")
    state.add_message(role="user", content="hello")
    assert len(state.history) == 1
    assert state.history[0].role == "user"
    assert state.history[0].content == "hello"
