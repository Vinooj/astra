import os
import json
from google import genai
from google.genai import types  
from typing import List, Dict, Any, Union, Optional
from .base_client import BaseLLMClient
from astra_framework.core.state import ChatMessage
from loguru import logger

class GeminiClient(BaseLLMClient):
    """
    A client for interacting with the Google Gemini API using the
    new 'google-genai' package.
    """

    def __init__(self, model: str = "gemini-2.0-flash"):
        """
        Initializes the GeminiClient.

        Args:
            model: The name of the Gemini model to use.
        """
        self.model_name = model
        
        try:
            # New client finds GOOGLE_API_KEY from env automatically
            self.client = genai.Client()
        except Exception as e:
            raise ValueError(
                "Failed to initialize Gemini client. "
                "Ensure GOOGLE_API_KEY is set in your environment. "
                f"Error: {e}"
            )


    async def generate(
        self, 
        history: List[ChatMessage], 
        tools: List[Dict[str, Any]] = None, 
        json_response: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """
        Generates a response from the Gemini API.
        
        Args:
            history: List of ChatMessage objects representing conversation history
            tools: Optional list of tool definitions in OpenAI format
            json_response: Whether to request JSON response format
            
        Returns:
            Either a string response or a dict with tool_calls
        """
        
        system_instruction = None
        gemini_contents = []
        
        # 1. Convert history to Gemini format
        for msg in history:
            role = self._convert_role(msg.role)
            
            if role == "system":
                # Extract system instruction (will be added to config)
                system_instruction = msg.content
                continue

            if msg.tool_calls:
                # Handle tool call requests from the model
                parts = []
                for tc in msg.tool_calls:
                    # Extract function call info
                    func_name = tc.get("function", {}).get("name")
                    func_args_str = tc.get("function", {}).get("arguments", "{}")
                    
                    # Parse arguments if they're a string
                    if isinstance(func_args_str, str):
                        try:
                            func_args = json.loads(func_args_str)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse function args: {func_args_str}")
                            func_args = {}
                    else:
                        func_args = func_args_str
                    
                    parts.append(types.Part(
                        function_call=types.FunctionCall(
                            name=func_name,
                            args=func_args
                        )
                    ))
                
                gemini_contents.append(
                    types.Content(role=role, parts=parts)
                )
                
            elif msg.role == "tool":
                # Handle tool responses
                # Gemini expects tool responses with the function name and response
                tool_name = getattr(msg, 'name', msg.tool_call_id or 'unknown_tool')
                
                part = types.Part(
                    function_response=types.FunctionResponse(
                        name=tool_name,
                        response={"content": msg.content}
                    )
                )
                
                gemini_contents.append(
                    types.Content(role="user", parts=[part])  # Tool responses go as 'user'
                )
                
            else:
                # Handle regular text content
                if msg.content:  # Only add non-empty messages
                    gemini_contents.append(
                        types.Content(
                            role=role,
                            parts=[types.Part(text=msg.content)]
                        )
                    )

        # 2. Configure generation settings
        config_params = {
            "temperature": 0.7,
            "max_output_tokens": 8192,  # INCREASED: Use max available tokens
            "top_p": 0.95,
            "top_k": 40
        }
        
        # Add system instruction to config (CORRECT WAY)
        if system_instruction:
            config_params["system_instruction"] = system_instruction
        
        # Add JSON response mode if requested
        if json_response:
            config_params["response_mime_type"] = "application/json"
        
        # Add safety settings to config
        config_params["safety_settings"] = [
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_NONE"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_NONE"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_NONE"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_NONE"
            ),
        ]
        
        # Add tools to config if provided
        if tools:
            try:
                gemini_tools = self._convert_tools_to_gemini(tools)
                if gemini_tools:
                    config_params["tools"] = gemini_tools
            except Exception as e:
                logger.error(f"Error converting tools: {e}")
                raise

        # Create the config object
        generation_config = types.GenerateContentConfig(**config_params)

        # 3. Build the API call parameters (CORRECT: only model, contents, config)
        api_params = {
            "model": self.model_name,
            "contents": gemini_contents,
            "config": generation_config,
        }

        try:
            # 4. Generate content using the async client
            logger.debug(f"Calling Gemini API with {len(gemini_contents)} content items")
            
            response = await self.client.aio.models.generate_content(**api_params)

            # 5. Parse the response
            if not response.candidates:
                logger.error("Gemini returned no candidates")
                return "Error: No response candidates from Gemini"
            
            candidate = response.candidates[0]
            
            # Check finish reason - IMPORTANT for detecting truncation
            if candidate.finish_reason != types.FinishReason.STOP:
                logger.warning(f"Generation stopped: {candidate.finish_reason.name}")
                
                if candidate.finish_reason == types.FinishReason.SAFETY:
                    safety_info = candidate.safety_ratings if hasattr(candidate, 'safety_ratings') else "Unknown"
                    logger.warning(f"Safety ratings: {safety_info}")
                    return f"Error: Generation blocked by safety filters. Ratings: {safety_info}"
                    
                if candidate.finish_reason == types.FinishReason.MAX_TOKENS:
                    logger.error("Response truncated due to max tokens - response may be incomplete!")
                    # For JSON responses, this is critical - we should return an error
                    if json_response:
                        return "Error: Response truncated due to token limit. The JSON output is incomplete. Please simplify the request or increase max_output_tokens."
                    # For non-JSON, we can still return the partial response with a warning
                    logger.warning("Continuing with partial response...")
                        
                if candidate.finish_reason == types.FinishReason.RECITATION:
                    logger.warning("Response blocked due to recitation")
                    return "Error: Response blocked due to recitation detection"
            
            if not candidate.content or not candidate.content.parts:
                logger.error("Gemini returned empty content")
                return ""

            # Check if response contains function calls
            has_function_call = any(hasattr(part, 'function_call') and part.function_call for part in candidate.content.parts)
            
            if has_function_call:
                # Extract all function calls
                tool_calls = []
                reasoning_parts = []
                
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        tool_calls.append(self._parse_function_call(part.function_call))
                    elif hasattr(part, 'text') and part.text:
                        reasoning_parts.append(part.text)
                
                reasoning_text = " ".join(reasoning_parts) if reasoning_parts else None
                
                return {
                    "content": reasoning_text or "",
                    "tool_calls": tool_calls
                }
            else:
                # Extract text response
                text_parts = []
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                
                response_text = "".join(text_parts) if text_parts else ""
                
                # ADDED: Validate JSON if expected
                if json_response and response_text:
                    try:
                        # Try to parse the JSON to ensure it's valid
                        json.loads(response_text)
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON response: {e}")
                        logger.error(f"Response text: {response_text[:500]}...")
                        return f"Error: Invalid JSON response from model. Response may have been truncated. Error: {e}"
                
                return response_text

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            logger.error(f"Contents count: {len(gemini_contents)}")
            logger.error(f"Model: {self.model_name}")
            
            # More detailed error logging
            if hasattr(e, '__dict__'):
                logger.error(f"Error details: {e.__dict__}")
            
            # Include full traceback for debugging
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            return f"Error: Gemini API call failed: {str(e)}"
        
    def _convert_role(self, role: str) -> str:
        """Converts standard roles to Gemini roles."""
        role_mapping = {
            "user": "user",
            "assistant": "model",
            "agent": "model",  # Treat agent as model
            "system": "system",
            "tool": "user"  # Tool responses are sent as 'user' role in Gemini
        }
        return role_mapping.get(role, "user")

    def _convert_tools_to_gemini(self, tools: List[Dict[str, Any]]) -> List[types.Tool]:
        """
        Converts OpenAI-style tool definitions to Gemini format.
        
        Args:
            tools: List of tool definitions in OpenAI format
            
        Returns:
            List of Gemini Tool objects
        """
        gemini_declarations = []
        
        for tool in tools:
            if tool.get("type") == "function":
                func_def = tool.get("function", {})
                
                # Convert parameters schema
                params_schema = func_def.get("parameters", {})
                
                # Build Gemini FunctionDeclaration
                declaration = types.FunctionDeclaration(
                    name=func_def.get("name"),
                    description=func_def.get("description", ""),
                    parameters=params_schema  # Gemini accepts OpenAPI-style schema
                )
                
                gemini_declarations.append(declaration)
        
        # Wrap declarations in a Tool object
        return [types.Tool(function_declarations=gemini_declarations)] if gemini_declarations else None

    def _parse_function_call(self, fc: types.FunctionCall) -> Dict[str, Any]:
        """
        Converts a Gemini FunctionCall object to OpenAI-style dict.
        
        Args:
            fc: Gemini FunctionCall object
            
        Returns:
            OpenAI-style tool call dictionary
        """
        # Generate a unique ID for the tool call
        import uuid
        tool_call_id = f"call_{uuid.uuid4().hex[:24]}"
        
        return {
            "id": tool_call_id,
            "type": "function",
            "function": {
                "name": fc.name,
                "arguments": json.dumps(dict(fc.args))
            }
        }