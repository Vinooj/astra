============================= test session starts ==============================
platform darwin -- Python 3.12.10, pytest-8.4.2, pluggy-1.6.0
rootdir: /Users/vinoo/Projects/ML/supportVectors/Projects/astra
configfile: pyproject.toml
plugins: asyncio-1.2.0, anyio-4.11.0, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 44 items

tests/test_agent.py .                                                    [  2%]
tests/test_base_client.py ..                                             [  6%]
tests/test_dynamic_workflow_agent.py ...                                 [ 13%]
tests/test_gemini_client.py ..                                           [ 18%]
tests/test_html_generator_agent.py ...                                   [ 25%]
tests/test_llm_agent.py .....                                            [ 36%]
tests/test_loop_agent.py ..                                              [ 40%]
tests/test_manager.py ....                                               [ 50%]
tests/test_models.py ..                                                  [ 54%]
tests/test_ollama_client.py ....                                         [ 63%]
tests/test_parallel_agent.py ..                                          [ 68%]
tests/test_sequential_agent.py ..                                        [ 72%]
tests/test_state.py ...                                                  [ 79%]
tests/test_tavily_client.py .....                                        [ 90%]
tests/test_tool.py ....                                                  [100%]

================================ tests coverage ================================
______________ coverage: platform darwin, python 3.12.10-final-0 _______________

Name                                               Stmts   Miss  Cover
----------------------------------------------------------------------
astra_framework/__init__.py                            3      0   100%
astra_framework/agents/__init__.py                     0      0   100%
astra_framework/agents/dynamic_workflow_agent.py      86     18    79%
astra_framework/agents/llm_agent.py                  105      6    94%
astra_framework/agents/loop_agent.py                  44      4    91%
astra_framework/agents/parallel_agent.py              27      0   100%
astra_framework/agents/sequential_agent.py            34      0   100%
astra_framework/core/__init__.py                       0      0   100%
astra_framework/core/agent.py                         13      1    92%
astra_framework/core/models.py                        10      0   100%
astra_framework/core/state.py                         17      0   100%
astra_framework/core/tool.py                          31      4    87%
astra_framework/core/workflow_models.py               18      0   100%
astra_framework/manager.py                            37      3    92%
astra_framework/services/__init__.py                   5      0   100%
astra_framework/services/base_client.py                7      1    86%
astra_framework/services/client_factory.py            11      1    91%
astra_framework/services/gemini_client.py              8      0   100%
astra_framework/services/ollama_client.py             33      0   100%
astra_framework/services/tavily_client.py             17      0   100%
----------------------------------------------------------------------
TOTAL                                                506     38    92%
============================== 44 passed in 0.86s ==============================
