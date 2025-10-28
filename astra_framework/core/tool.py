import inspect
from loguru import logger
from typing import Callable, Dict, Any

class ToolManager:
    """Manages tool registration and execution."""
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        logger.debug("ToolManager initialized.")

    def register(self, func: Callable):
        """Decorator to register a function as a tool."""
        tool_name = func.__name__
        logger.debug(f"Registering tool: {tool_name}")
        self.tools[tool_name] = func
        return func

    def get_definitions(self) -> list:
        # In a real system, this would return JSON Schema for the LLM
        return [name for name in self.tools.keys()]

    async def execute_tool(self, name: str, **kwargs) -> Any:
        if name not in self.tools:
            logger.error(f"Attempted to call unknown tool: {name}")
            return f"Error: Tool '{name}' not found."
        
        logger.info(f"Executing tool '{name}' with args: {kwargs}")
        func = self.tools[name]
        
        try:
            if inspect.iscoroutinefunction(func):
                result = await func(**kwargs)
            else:
                result = func(**kwargs)
            logger.success(f"Tool '{name}' executed. Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Tool '{name}' failed: {e}")
            return f"Error executing tool: {e}"