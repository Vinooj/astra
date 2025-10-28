## `class A2AInvokeRequest`

## `class A2AInvokeResponse`

## `class MockLLMClient`

A mock LLM that returns the 'dict' structure for tool calls.

### `def __init__`

### `def generate`

## `def add`

Adds two integers.

## `def multiply`

Multiplies two integers.

## `def get_agent_card`

Returns the 'Agent Card', a specification of all workflows
this server provides.

## `def handle_a2a_invoke`

This is the main A2A endpoint. It receives a request,
translates it for the WorkflowManager, runs the agent,
and translates the response back to JSON.

