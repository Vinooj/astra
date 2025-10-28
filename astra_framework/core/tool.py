import inspect
from loguru import logger
from typing import Callable, Dict, Any

class ToolManager:
    """
    Manages tool registration and execution.

    The ToolManager is responsible for maintaining a registry of available tools
    and for executing them by name.
    """
    def __init__(self):
        """Initializes the ToolManager with an empty tool registry."""
        self.tools: Dict[str, Callable] = {}
        logger.debug("ToolManager initialized.")

    def register(self, func: Callable):
        """
        Decorator to register a function as a tool.

        Args:
            func: The function to register as a tool.
        """
        tool_name = func.__name__
        logger.debug(f"Registering tool: {tool_name}")
        self.tools[tool_name] = func
        return func

    def get_definitions(self) -> list:
        """
        Returns a list of tool names.

        In a more advanced implementation, this would return a list of
        JSON Schema definitions for the tools, which can be used by an LLM
        to understand how to use the tools.
        """
        # In a real system, this would return JSON Schema for the LLM
        return [name for name in self.tools.keys()]

    async def execute_tool(self, name: str, **kwargs) -> Any:
        """
        Executes a tool by name with the given arguments.

        Args:
            name: The name of the tool to execute.
            **kwargs: The arguments to pass to the tool.

        Returns:
            The result of the tool execution, or an error message if the
            tool is not found or fails.
        """
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