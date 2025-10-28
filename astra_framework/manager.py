import uuid
from loguru import logger
from typing import Dict
from astra_framework.core.state import SessionState
from astra_framework.core.agent import BaseAgent
from astra_framework.core.models import AgentResponse

class WorkflowManager:
    """
    (Facade Pattern) Manages all workflows, sessions, and is the
    main entry point for the framework.
    """
    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}
        # Stores all registered agent workflows by name
        self.workflows: Dict[str, BaseAgent] = {} 
        logger.debug("WorkflowManager initialized.")

    def register_workflow(self, name: str, agent: BaseAgent):
        """
        Registers a fully-composed agent (like a SequentialAgent)
        with a unique name.
        """
        if name in self.workflows:
            logger.warning(f"Overwriting existing workflow: {name}")
        logger.info(f"Registering workflow: '{name}'")
        self.workflows[name] = agent

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = SessionState(session_id=session_id)
        logger.info(f"Created new session: {session_id}")
        return session_id

    def get_session_state(self, session_id: str) -> SessionState:
        if session_id not in self.sessions:
            logger.error(f"Session not found: {session_id}")
            raise Exception("Session not found")
        return self.sessions[session_id]

    async def run(self, workflow_name: str, session_id: str, prompt: str) -> AgentResponse:
        """
        Main entry point to run a *named* workflow.
        """
        logger.info(f"--- Running workflow '{workflow_name}' for session {session_id} ---")
        
        # 1. Look up the agent (Strategy) by name
        agent = self.workflows.get(workflow_name)
        if not agent:
            logger.error(f"Workflow not found: {workflow_name}")
            return AgentResponse(status="error", final_content=f"Workflow '{workflow_name}' not found.")
            
        # 2. Get the session state (Blackboard)
        state = self.get_session_state(session_id)
        state.add_message(role="user", content=prompt)
        
        # 3. Delegate the execution
        response = await agent.execute(state)
        
        logger.success(f"--- Workflow '{workflow_name}' finished for session {session_id} ---")
        return response