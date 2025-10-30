from typing import List, Callable, Optional, Type
from pydantic import BaseModel

from astra_framework.core.agent import BaseAgent
from astra_framework.agents.react_agent import ReActAgent
from astra_framework.agents.sequential_agent import SequentialAgent
from astra_framework.agents.parallel_agent import ParallelAgent
from astra_framework.agents.loop_agent import LoopAgent
from astra_framework.services.base_client import BaseLLMClient

class WorkflowBuilder:
    """
    Provides a fluent API to construct complex agent workflows.
    """
    def __init__(self, workflow_name: str):
        self.workflow_name = workflow_name
        self.root_agent: Optional[BaseAgent] = None
        self.current_composite: Optional[BaseAgent] = None

    def start_with_react_agent(self, 
                               agent_name: str, 
                               llm_client: BaseLLMClient,
                               tools: List[Callable],
                               instruction: str,
                               max_iterations: int = 10,
                               output_structure: Optional[Type[BaseModel]] = None) -> 'WorkflowBuilder':
        """Starts the workflow with a ReActAgent as the root."""
        self.root_agent = ReActAgent(
            agent_name=agent_name,
            llm_client=llm_client,
            tools=tools,
            instruction=instruction,
            max_iterations=max_iterations,
            output_structure=output_structure
        )
        return self

    def start_with_sequential(self, agent_name: str, children: List[BaseAgent] = None) -> 'WorkflowBuilder':
        """Starts the workflow with a SequentialAgent as the root."""
        agent = SequentialAgent(agent_name, children or [])
        self.root_agent = agent
        self.current_composite = agent
        return self

    def add_agent(self, agent: BaseAgent) -> 'WorkflowBuilder':
        """Adds an agent to the current composite agent (e.g., a SequentialAgent)."""
        if not self.current_composite or not hasattr(self.current_composite, 'children'):
            raise ValueError("No composite agent (like Sequential or Parallel) to add to.")
        self.current_composite.children.append(agent)
        return self

    def build(self) -> BaseAgent:
        """Returns the constructed root agent of the workflow."""
        if not self.root_agent:
            raise ValueError("Workflow is empty. Start with an agent before building.")
        return self.root_agent
