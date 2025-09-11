import os
import re
from typing import List, Dict, Optional
import aiohttp
from .base_llm import BaseLLM
import logging
import json
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class GeminiLLM(BaseLLM):
    """
    Gemini LLM implementation that inherits from BaseLLM.
    Handles Google's Gemini API integration with optional web search capabilities.
    
    Features:
    - Real-time web search using Google Search tool
    - Configurable web search enable/disable
    - JSON response formatting
    - Conversation history support
    """
    
    def __init__(self, instruction: str, model: str, enable_web_search: bool = True):
        """
        Initialize the Gemini LLM with instruction and API key.
        
        Args:
            instruction (str): The system instruction for the LLM
            model (str): The model to use
            enable_web_search (bool): Whether to enable web search functionality
        """
        super().__init__(instruction, "gemini")
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        self.enable_web_search = enable_web_search
        
        if not self.api_key:
            logger.error("GEMINI_API_KEY environment variable is not set!")
            raise ValueError("GEMINI_API_KEY environment variable is required")
    
    async def query(self, instruction: str, prompt: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Query the Gemini LLM with a prompt and optional conversation history.
        
        Args:
            prompt (str): The user's prompt/query
            history (Optional[List[Dict[str, str]]]): Conversation history in format:
                [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        
        Returns:
            str: The Gemini LLM's response
        """
        try:
            # Prepare the full prompt with instruction and history
            full_prompt = self._prepare_prompt(instruction, prompt, history)

            logger.info("Full prompt: %s", full_prompt)
            
            # Prepare the request payload
            payload = {
                "contents": [{
                    "parts": [{
                        "text": full_prompt
                    }]
                }]
            }
            
            # Add web search tool if enabled
            if self.enable_web_search:
                payload["tools"] = [{
                    "google_search": {}
                }]
            
            logger.info("Payload: %s", payload)
            
            # Make API request
            headers = {
                "Content-Type": "application/json"
            }
            
            params = {
                "key": self.api_key
            }
            
            logger.info("API Key present: %s", bool(self.api_key))
            logger.info("API Key length: %s", len(self.api_key) if self.api_key else 0)
            logger.info("Request URL: %s", self.base_url)
            logger.info("Request params: %s", params)
            
            logger.info("Starting API request...")
            async with aiohttp.ClientSession() as session:
                logger.info("Client session created, making POST request...")
                async with session.post(
                    self.base_url,
                    headers=headers,
                    params=params,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    logger.info("Response received, processing...")
                    logger.info("Response status: %s", response.status)
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info("API response structure: %s", list(result.keys()))
                        
                        if "candidates" in result and len(result["candidates"]) > 0:
                            candidate = result["candidates"][0]
                            logger.info("Candidate structure: %s", list(candidate.keys()))
                            
                            if "content" in candidate and "parts" in candidate["content"]:
                                response_text = candidate["content"]["parts"][0].get("text", "No response generated")
                                logger.info("Response text length: %s", len(response_text))
                                return self._ensure_json_response(response_text)
                            else:
                                logger.error(f"No content/parts in candidate: {candidate}")
                        else:
                            logger.error(f"No candidates in response: {result}")
                        return self._ensure_json_response("No response generated")
                    else:
                        response_text = await response.text()
                        logger.error(f"Gemini API returned error status {response.status}")
                        logger.error(f"Response headers: {dict(response.headers)}")
                        logger.error(f"Response body: {response_text}")
                        raise Exception(f"API Error {response.status}: {response_text}")

        except Exception as e:
            logger.error(f"Error in Gemini LLM query: {type(e).__name__}: {str(e)}")
            logger.error(f"Full exception details: {repr(e)}")
            logger.error(f"Exception args: {e.args}")
            logger.error(f"Exception dir: {[attr for attr in dir(e) if not attr.startswith('_')]}")
            raise Exception(f"Error generating response: {type(e).__name__}: {str(e)}") from e
    
    def _ensure_json_response(self, response_text: str) -> str:
        """
        Ensure the response is in valid JSON format.
        If the response is not valid JSON, wrap it in a JSON object.
        
        Args:
            response_text (str): The raw response text from the LLM
        
        Returns:
            str: Valid JSON string
        """
        try:
            # Try to parse the response as JSON directly
            parsed_json = json.loads(response_text)
            return parsed_json
        except (json.JSONDecodeError, TypeError):
            # If not valid JSON, try to extract JSON from markdown code blocks
            try:
                # Look for JSON wrapped in ```json ... ``` or ``` ... ```
                json_patterns = [
                    r'```json\s*\n(.*?)\n```',  # ```json ... ```
                    r'```\s*\n(.*?)\n```',      # ``` ... ```
                    r'```json\s*(.*?)```',      # ```json ... ``` (no newlines)
                    r'```\s*(.*?)```'           # ``` ... ``` (no newlines)
                ]
                
                for pattern in json_patterns:
                    json_match = re.search(pattern, response_text, re.DOTALL)
                    if json_match:
                        json_text = json_match.group(1).strip()
                        parsed_json = json.loads(json_text)
                        logger.info("Successfully extracted JSON from markdown: %s", type(parsed_json))
                        return parsed_json
                
                # Try to extract JSON array or object from the text
                array_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
                if array_match:
                    json_text = array_match.group()
                    parsed_json = json.loads(json_text)
                    logger.info("Successfully extracted JSON array: %s", type(parsed_json))
                    return parsed_json
                    
                object_match = re.search(r'\{.*?\}', response_text, re.DOTALL)
                if object_match:
                    json_text = object_match.group()
                    parsed_json = json.loads(json_text)
                    logger.info("Successfully extracted JSON object: %s", type(parsed_json))
                    return parsed_json
                    
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning("Failed to extract JSON from response: %s", e)
            
            # If all else fails, wrap the response in a JSON object
            logger.warning("Could not parse JSON from response, wrapping: %s...", response_text[:100])
            return json.dumps({
                "response": response_text,
                "status": "success",
                "format": "wrapped"
            })
    
    def _prepare_prompt(self, instruction: str, prompt: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Prepare the full prompt including instruction and conversation history.
        
        Args:
            prompt (str): The current user prompt
            history (Optional[List[Dict[str, str]]]): Conversation history
        
        Returns:
            str: The formatted prompt ready for the LLM
        """
        # Start with the system instruction and JSON format requirement
        full_prompt = f"System Instruction: {instruction}\n\n"
        full_prompt += "IMPORTANT: You must ALWAYS respond with valid JSON format. No matter what the question or request is, your response must be a valid JSON object. Do not include any text outside of the JSON structure.\n\n"
        
        # Add web search capability information if enabled
        if self.enable_web_search:
            full_prompt += "WEB SEARCH ENABLED: You have access to real-time web search capabilities. Use this to find current, up-to-date information when needed. Always search for the most recent information when the user asks about current events, recent developments, or anything that might require current data.\n\n"
        
        # Add conversation history if provided
        if history:
            full_prompt += "Conversation History:\n"
            for message in history:
                role = message.get("role", "user")
                content = message.get("content", "")
                full_prompt += f"{role.title()}: {content}\n"
            full_prompt += "\n"
        
        # Add the current prompt
        full_prompt += f"User: {prompt}\nAssistant:"
        
        return full_prompt
    
    def set_web_search(self, enabled: bool) -> None:
        """
        Enable or disable web search functionality.
        
        Args:
            enabled (bool): Whether to enable web search
        """
        self.enable_web_search = enabled
        logger.info("Web search %s", 'enabled' if enabled else 'disabled')
