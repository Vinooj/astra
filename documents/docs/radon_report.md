# Radon Report

## Cyclomatic Complexity (CC)

```
astra_framework/manager.py
    C 8:0 WorkflowManager - A (2)
    M 23:4 WorkflowManager.register_workflow - A (2)
    M 49:4 WorkflowManager.get_session_state - A (2)
    M 67:4 WorkflowManager.run - A (2)
    M 16:4 WorkflowManager.__init__ - A (1)
    M 37:4 WorkflowManager.create_session - A (1)
astra_framework/core/models.py
    C 5:0 ToolCall - A (1)
    C 11:0 AgentResponse - A (1)
astra_framework/core/agent.py
    C 7:0 BaseAgent - A (2)
    M 9:4 BaseAgent.__init__ - A (1)
    M 15:4 BaseAgent.execute - A (1)
astra_framework/core/tool.py
    M 40:4 ToolManager.execute_tool - A (4)
    C 5:0 ToolManager - A (3)
    M 29:4 ToolManager.get_definitions - A (2)
    M 12:4 ToolManager.__init__ - A (1)
    M 17:4 ToolManager.register - A (1)
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
    M 88:4 LLMAgent.execute - B (8)
    C 12:0 LLMAgent - A (4)
    M 78:4 LLMAgent._get_param_type - A (4)
    M 15:4 LLMAgent.__init__ - A (3)
    M 58:4 LLMAgent._create_tool_parameters - A (3)
    M 28:4 LLMAgent._get_tool_definitions - A (2)
    M 38:4 LLMAgent._create_tool_definition - A (2)
astra_framework/agents/loop_agent.py
    M 27:4 LoopAgent.execute - B (6)
    C 8:0 LoopAgent - A (4)
    M 58:4 LoopAgent._prepare_for_next_loop - A (3)
    M 15:4 LoopAgent.__init__ - A (1)
astra_framework/services/ollama_client.py
    M 17:4 OllamaClient.generate - A (5)
    C 10:0 OllamaClient - A (4)
    M 50:4 OllamaClient._handle_ollama_response - A (2)
    M 13:4 OllamaClient.__init__ - A (1)
astra_framework/services/base_client.py
    C 5:0 BaseLLMClient - A (2)
    M 15:4 BaseLLMClient.generate - A (1)
astra_framework/services/tavily_client.py
    C 5:0 TavilyClient - A (4)
    M 13:4 TavilyClient.__init__ - A (3)
    M 29:4 TavilyClient.search - A (2)
astra_framework/services/gemini_client.py
    C 5:0 GeminiClient - A (2)
    M 13:4 GeminiClient.__init__ - A (1)
    M 22:4 GeminiClient.generate - A (1)

49 blocks (classes, functions, methods) analyzed.
Average complexity: A (2.4081632653061225)
```
## Raw Metrics

```
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
astra_framework/manager.py
    LOC: 95
    LLOC: 45
    SLOC: 37
    Comments: 4
    Single comments: 5
    Multi: 36
    Blank: 17
    - Comment Stats
        (C % L): 4%
        (C % S): 11%
        (C + M % L): 42%
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
    LOC: 68
    LLOC: 36
    SLOC: 30
    Comments: 1
    Single comments: 2
    Multi: 25
    Blank: 11
    - Comment Stats
        (C % L): 1%
        (C % S): 3%
        (C + M % L): 38%
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
    LOC: 152
    LLOC: 98
    SLOC: 115
    Comments: 1
    Single comments: 4
    Multi: 4
    Blank: 29
    - Comment Stats
        (C % L): 1%
        (C % S): 1%
        (C + M % L): 3%
astra_framework/agents/loop_agent.py
    LOC: 74
    LLOC: 49
    SLOC: 51
    Comments: 4
    Single comments: 5
    Multi: 6
    Blank: 12
    - Comment Stats
        (C % L): 5%
        (C % S): 8%
        (C + M % L): 14%
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
    LOC: 62
    LLOC: 37
    SLOC: 37
    Comments: 0
    Single comments: 2
    Multi: 9
    Blank: 14
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 15%
astra_framework/services/base_client.py
    LOC: 27
    LLOC: 9
    SLOC: 7
    Comments: 0
    Single comments: 0
    Multi: 15
    Blank: 5
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 56%
astra_framework/services/tavily_client.py
    LOC: 46
    LLOC: 20
    SLOC: 17
    Comments: 0
    Single comments: 0
    Multi: 21
    Blank: 8
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 46%
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
    LOC: 35
    LLOC: 11
    SLOC: 8
    Comments: 1
    Single comments: 1
    Multi: 19
    Blank: 7
    - Comment Stats
        (C % L): 3%
        (C % S): 12%
        (C + M % L): 57%
** Total **
    LOC: 696
    LLOC: 416
    SLOC: 398
    Comments: 20
    Single comments: 30
    Multi: 145
    Blank: 123
    - Comment Stats
        (C % L): 3%
        (C % S): 5%
        (C + M % L): 24%
```
