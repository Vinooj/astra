import inspect
import json
from loguru import logger
from typing import Callable, Dict, Any, List, get_type_hints
from pydantic import BaseModel

class ToolManager:
    """
    Manages tool registration, definition generation, and execution.
    """
    def __init__(self, tools: List[Callable] = None):
        """Initializes the ToolManager. Can be initialized with a list of 
        tools.
        """
        self.tools: Dict[str, Callable] = {}
        if tools:
            for tool in tools:
                self.register(tool)
        logger.debug("ToolManager initialized.")

    def register(self, func: Callable) -> Callable:
        """
        Decorator or method to register a function as a tool.
        """
        tool_name = func.__name__
        logger.debug(f"Registering tool: {tool_name}")
        self.tools[tool_name] = func
        return func

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Generates JSON Schema definitions for all registered tools."""
        definitions = []
        for name, func in self.tools.items():
            definitions.append(self._generate_tool_definition(func))
        return definitions

    def _generate_tool_definition(self, func: Callable) -> Dict[str, Any]:
        """Generates the JSON schema for a single function."""
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        docstring = inspect.getdoc(func) or ""
        
        # Parse the docstring for a main description and param descriptions
        lines = docstring.strip().split('\n')
        main_description = lines[0] if lines else ""
        param_descriptions = {}
        for line in lines:
            if line.strip().startswith(":param"):
                parts = line.strip().split(":", 2)
                param_name = parts[1].replace("param", "").strip()
                param_desc = parts[2].strip()
                param_descriptions[param_name] = param_desc

        parameters = {"type": "object", "properties": {}, "required": []}
        
        for name, param in sig.parameters.items():
            param_type = type_hints.get(name, Any)
            
            # Handle Pydantic models
            if isinstance(param_type, type) and issubclass(param_type, BaseModel):
                schema = param_type.model_json_schema()
                parameters["properties"][name] = schema
            else: # Handle basic types
                schema_type = self._map_type_to_json_schema(param_type)
                parameters["properties"][name] = {
                    "type": schema_type,
                    "description": param_descriptions.get(name, "")
                }

            if param.default is inspect.Parameter.empty:
                parameters["required"].append(name)

        return {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": main_description,
                "parameters": parameters
            }
        }

    def _map_type_to_json_schema(self, py_type: Any) -> str:
        """Maps Python types to JSON schema types."""
        if py_type is str: return "string"
        if py_type is int: return "integer"
        if py_type is float: return "number"
        if py_type is bool: return "boolean"
        if py_type is list: return "array"
        if py_type is dict: return "object"
        return "string" # Default for Any or unknown

    async def execute_tool(self, name: str, args: Dict[str, Any]) -> Any:
        """
        Executes a tool by name with a dictionary of arguments.
        """
        if name not in self.tools:
            logger.error(f"Attempted to call unknown tool: {name}")
            return f"Error: Tool '{name}' not found."
        
        logger.info(f"Executing tool '{name}' with args: {args}")
        func = self.tools[name]
        
        # Unpack the dictionary of arguments into keyword arguments
        return await self._execute_function(func, **args)

    async def _execute_function(self, func: Callable, **kwargs) -> Any:
        """
        Executes a function, handling both sync and async functions.
        """
        try:
            # Here we need to handle Pydantic model hydration if needed
            sig = inspect.signature(func)
            type_hints = get_type_hints(func)
            hydrated_kwargs = {}
            for name, arg_val in kwargs.items():
                param_type = type_hints.get(name)
                if (isinstance(param_type, type) and 
                        issubclass(param_type, BaseModel) and 
                        isinstance(arg_val, dict)):
                    hydrated_kwargs[name] = param_type.model_validate(arg_val)
                else:
                    hydrated_kwargs[name] = arg_val

            if inspect.iscoroutinefunction(func):
                result = await func(**hydrated_kwargs)
            else:
                result = func(**hydrated_kwargs)
            
            logger.success(f"Tool '{func.__name__}' executed successfully.")
            # If the result is a Pydantic model, serialize it for the LLM
            if isinstance(result, BaseModel):
                return result.model_dump_json()
            return result
        except Exception as e:
            logger.error(f"Tool '{func.__name__}' failed: {e}")
            return f"Error executing tool: {e}"