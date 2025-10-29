from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Any, Optional

class AgentConfig(BaseModel):
    agent_type: Literal["LLMAgent", "SequentialAgent", "ParallelAgent", "LoopAgent"]
    agent_name: str
    # Common parameters for LLMAgent
    instruction: Optional[str] = None
    output_structure: Optional[str] = None # String representation of Pydantic model name
    tools: Optional[List[str]] = None # List of tool function names
    keep_alive_state: Optional[bool] = False

    # Parameters for composite agents (Sequential, Parallel, Loop)
    children: Optional[List["AgentConfig"]] = None
    child: Optional["AgentConfig"] = None
    max_loops: Optional[int] = None
    exit_condition: Optional[str] = None # String representation of a callable name

class WorkflowPlan(BaseModel):
    main_topic: str
    workflow_description: str
    root_agent: AgentConfig

# Forward references for recursive models
AgentConfig.model_rebuild()
