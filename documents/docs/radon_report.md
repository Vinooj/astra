# Radon Report

## Cyclomatic Complexity (CC)

```
astra_framework/a2a_server.py
    M 56:4 MockLLMClient.generate - B (7)
    C 51:0 MockLLMClient - A (5)
    F 157:0 handle_a2a_invoke - A (4)
    F 140:0 get_agent_card - A (2)
    F 84:0 add - A (1)
    F 88:0 multiply - A (1)
    C 35:0 A2AInvokeRequest - A (1)
    C 40:0 A2AInvokeResponse - A (1)
    M 53:4 MockLLMClient.__init__ - A (1)
astra_framework/main.py
    F 1:0 main - A (1)
astra_framework/manager.py
    C 8:0 WorkflowManager - A (2)
    M 19:4 WorkflowManager.register_workflow - A (2)
    M 35:4 WorkflowManager.get_session_state - A (2)
    M 41:4 WorkflowManager.run - A (2)
    M 13:4 WorkflowManager.__init__ - A (1)
    M 29:4 WorkflowManager.create_session - A (1)
astra_framework/core/models.py
    C 5:0 ToolCall - A (1)
    C 11:0 AgentResponse - A (1)
astra_framework/core/agent.py
    C 7:0 BaseAgent - A (2)
    M 9:4 BaseAgent.__init__ - A (1)
    M 15:4 BaseAgent.execute - A (1)
astra_framework/core/tool.py
    M 22:4 ToolManager.execute_tool - A (4)
    C 5:0 ToolManager - A (3)
    M 18:4 ToolManager.get_definitions - A (2)
    M 7:4 ToolManager.__init__ - A (1)
    M 11:4 ToolManager.register - A (1)
astra_framework/core/state.py
    C 11:0 SessionState - A (2)
    C 6:0 ChatMessage - A (1)
    M 18:4 SessionState.__post_init__ - A (1)
    M 21:4 SessionState.add_message - A (1)
astra_framework/agents/sequential_agent.py
    C 8:0 SequentialAgent - A (4)
    M 18:4 SequentialAgent.execute - A (4)
    M 13:4 SequentialAgent.__init__ - A (1)
astra_framework/agents/parallel_agent.py
    C 9:0 ParallelAgent - A (4)
    M 21:4 ParallelAgent.execute - A (4)
    M 16:4 ParallelAgent.__init__ - A (1)
astra_framework/agents/llm_agent.py
    M 28:4 LLMAgent._get_tool_definitions - B (8)
    M 71:4 LLMAgent.execute - B (8)
    C 12:0 LLMAgent - B (7)
    M 15:4 LLMAgent.__init__ - A (3)
astra_framework/agents/loop_agent.py
    M 27:4 LoopAgent.execute - B (8)
    C 8:0 LoopAgent - B (6)
    M 15:4 LoopAgent.__init__ - A (1)
astra_framework/services/ollama_client.py
    M 17:4 OllamaClient.generate - B (6)
    C 10:0 OllamaClient - A (5)
    M 13:4 OllamaClient.__init__ - A (1)
astra_framework/services/base_client.py
    C 5:0 BaseLLMClient - A (2)
    M 9:4 BaseLLMClient.generate - A (1)
astra_framework/services/tavily_client.py
    C 5:0 TavilyClient - A (4)
    M 8:4 TavilyClient.__init__ - A (3)
    M 14:4 TavilyClient.search - A (2)
astra_framework/services/gemini_client.py
    C 5:0 GeminiClient - A (2)
    M 8:4 GeminiClient.__init__ - A (1)
    M 11:4 GeminiClient.generate - A (1)

54 blocks (classes, functions, methods) analyzed.
Average complexity: A (2.6481481481481484)
```
## Raw Metrics

```
astra_framework/a2a_server.py
    LOC: 196
    LLOC: 97
    SLOC: 119
    Comments: 34
    Single comments: 36
    Multi: 9
    Blank: 32
    - Comment Stats
        (C % L): 17%
        (C % S): 29%
        (C + M % L): 22%
astra_framework/__init__.py
    LOC: 0
    LLOC: 0
    SLOC: 0
    Comments: 0
    Single comments: 0
    Multi: 0
    Blank: 0
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 0%
astra_framework/main.py
    LOC: 6
    LLOC: 4
    SLOC: 4
    Comments: 0
    Single comments: 0
    Multi: 0
    Blank: 2
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 0%
astra_framework/manager.py
    LOC: 61
    LLOC: 42
    SLOC: 37
    Comments: 4
    Single comments: 4
    Multi: 11
    Blank: 9
    - Comment Stats
        (C % L): 7%
        (C % S): 11%
        (C + M % L): 25%
astra_framework/core/models.py
    LOC: 14
    LLOC: 16
    SLOC: 10
    Comments: 0
    Single comments: 2
    Multi: 0
    Blank: 2
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 0%
astra_framework/core/__init__.py
    LOC: 0
    LLOC: 0
    SLOC: 0
    Comments: 0
    Single comments: 0
    Multi: 0
    Blank: 0
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 0%
astra_framework/core/agent.py
    LOC: 16
    LLOC: 14
    SLOC: 13
    Comments: 0
    Single comments: 1
    Multi: 0
    Blank: 2
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 0%
astra_framework/core/tool.py
    LOC: 39
    LLOC: 33
    SLOC: 30
    Comments: 1
    Single comments: 3
    Multi: 0
    Blank: 6
    - Comment Stats
        (C % L): 3%
        (C % S): 3%
        (C + M % L): 3%
astra_framework/core/state.py
    LOC: 23
    LLOC: 23
    SLOC: 17
    Comments: 2
    Single comments: 2
    Multi: 0
    Blank: 4
    - Comment Stats
        (C % L): 9%
        (C % S): 12%
        (C + M % L): 9%
astra_framework/agents/sequential_agent.py
    LOC: 43
    LLOC: 32
    SLOC: 31
    Comments: 2
    Single comments: 2
    Multi: 4
    Blank: 6
    - Comment Stats
        (C % L): 5%
        (C % S): 6%
        (C + M % L): 14%
astra_framework/agents/__init__.py
    LOC: 0
    LLOC: 0
    SLOC: 0
    Comments: 0
    Single comments: 0
    Multi: 0
    Blank: 0
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 0%
astra_framework/agents/parallel_agent.py
    LOC: 41
    LLOC: 26
    SLOC: 25
    Comments: 5
    Single comments: 4
    Multi: 6
    Blank: 6
    - Comment Stats
        (C % L): 12%
        (C % S): 20%
        (C + M % L): 27%
astra_framework/agents/llm_agent.py
    LOC: 135
    LLOC: 88
    SLOC: 108
    Comments: 1
    Single comments: 2
    Multi: 0
    Blank: 25
    - Comment Stats
        (C % L): 1%
        (C % S): 1%
        (C + M % L): 1%
astra_framework/agents/loop_agent.py
    LOC: 70
    LLOC: 45
    SLOC: 49
    Comments: 5
    Single comments: 4
    Multi: 6
    Blank: 11
    - Comment Stats
        (C % L): 7%
        (C % S): 10%
        (C + M % L): 16%
astra_framework/examples/run_workflow.py
    LOC: 0
    LLOC: 0
    SLOC: 0
    Comments: 0
    Single comments: 0
    Multi: 0
    Blank: 0
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 0%
astra_framework/services/ollama_client.py
    LOC: 59
    LLOC: 34
    SLOC: 35
    Comments: 0
    Single comments: 1
    Multi: 9
    Blank: 14
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 15%
astra_framework/services/base_client.py
    LOC: 21
    LLOC: 9
    SLOC: 7
    Comments: 0
    Single comments: 1
    Multi: 9
    Blank: 4
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 43%
astra_framework/services/tavily_client.py
    LOC: 22
    LLOC: 19
    SLOC: 17
    Comments: 0
    Single comments: 2
    Multi: 0
    Blank: 3
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 0%
astra_framework/services/__init__.py
    LOC: 0
    LLOC: 0
    SLOC: 0
    Comments: 0
    Single comments: 0
    Multi: 0
    Blank: 0
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 0%
astra_framework/services/gemini_client.py
    LOC: 24
    LLOC: 10
    SLOC: 8
    Comments: 1
    Single comments: 2
    Multi: 9
    Blank: 5
    - Comment Stats
        (C % L): 4%
        (C % S): 12%
        (C + M % L): 42%
** Total **
    LOC: 770
    LLOC: 492
    SLOC: 510
    Comments: 55
    Single comments: 66
    Multi: 63
    Blank: 131
    - Comment Stats
        (C % L): 7%
        (C % S): 11%
        (C + M % L): 15%
```
