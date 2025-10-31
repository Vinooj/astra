## `class ReActAgent`

ReAct agent with support for extended thinking.

### `def __init__`

### `def _extract_thinking`

Extract thinking/reasoning from content and return (thinking, cleaned_content).

Returns:
    Tuple of (thinking_content, user_facing_content)

### `def _log_thinking`

Log thinking content separately for debugging.

### `def execute`

Executes the ReAct loop with thinking support.

### `def _execute_single_tool`

Execute a single tool and add result to history.

### `def _is_final_answer`

Check if content is a final answer.

