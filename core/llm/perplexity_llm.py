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

class PerplexityLLM(BaseLLM):
    """
    Perplexity LLM implementation that inherits from BaseLLM.
    Handles Perplexity API integration with real-time web search capabilities.
    
    Features:
    - Real-time web search using Perplexity's built-in capabilities
    - Configurable web search enable/disable
    - JSON response formatting
    - Conversation history support
    - Multiple model support (llama-3.1-sonar, llama-3.1-sonar-128k, etc.)
    """
    
    def __init__(self, instruction: str, model: str = "sonar", enable_web_search: bool = True):
        """
        Initialize the Perplexity LLM with instruction and API key.
        
        Args:
            instruction (str): The system instruction for the LLM
            model (str): The model to use (default: llama-3.1-sonar)
            enable_web_search (bool): Whether to enable web search functionality
        """
        super().__init__(instruction, "perplexity")
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.model = model
        self.enable_web_search = enable_web_search
        
        if not self.api_key:
            logger.error("PERPLEXITY_API_KEY environment variable is not set!")
            raise ValueError("PERPLEXITY_API_KEY environment variable is required")
    
    async def query(self, instruction: str, prompt: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Query the Perplexity LLM with a prompt and optional conversation history.
        
        Args:
            instruction (str): The system instruction for the LLM
            prompt (str): The user's prompt/query
            history (Optional[List[Dict[str, str]]]): Conversation history in format:
                [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        
        Returns:
            str: The Perplexity LLM's response
        """
        try:
            # Prepare the full prompt with instruction and history
            full_prompt = self._prepare_prompt(instruction, prompt, history)

            logger.info("Full prompt: %s", full_prompt)
            
            # Prepare the request payload
            messages = []
            
            # Add system instruction
            messages.append({
                "role": "system",
                "content": instruction
            })
            
            # Add conversation history if provided
            if history:
                for message in history:
                    messages.append({
                        "role": message.get("role", "user"),
                        "content": message.get("content", "")
                    })
            
            # Add current prompt
            messages.append({
                "role": "user",
                "content": prompt,
                "response_format": {
                    "type": "json_schema"
                }
            })
            
            payload = {
                "model": self.model,
                "messages": messages,
                # "max_tokens": 1000,
                # "temperature": 0.2,
                "stream": False
            }
            
            logger.info("Payload: %s", payload)
            
            # Make API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            logger.info("API Key present: %s", bool(self.api_key))
            logger.info("API Key length: %s", len(self.api_key) if self.api_key else 0)
            logger.info("Request URL: %s", self.base_url)
            
            logger.info("Starting API request...")
            async with aiohttp.ClientSession() as session:
                logger.info("Client session created, making POST request...")
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    logger.info("Response received, processing...")
                    logger.info("Response status: %s", response.status)
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info("API response structure: %s", list(result.keys()))
                        
                        if "choices" in result and len(result["choices"]) > 0:
                            choice = result["choices"][0]
                            logger.info("Choice structure: %s", list(choice.keys()))
                            
                            if "message" in choice and "content" in choice["message"]:
                                response_text = choice["message"]["content"]
                                logger.info("Response text length: %s", len(response_text))
                                return self._ensure_json_response(response_text)
                            else:
                                logger.error(f"No message/content in choice: {choice}")
                        else:
                            logger.error(f"No choices in response: {result}")
                        return self._ensure_json_response("No response generated")
                    else:
                        response_text = await response.text()
                        logger.error(f"Perplexity API returned error status {response.status}")
                        logger.error(f"Response headers: {dict(response.headers)}")
                        logger.error(f"Response body: {response_text}")
                        raise Exception(f"API Error {response.status}: {response_text}")

        except Exception as e:
            logger.error(f"Error in Perplexity LLM query: {type(e).__name__}: {str(e)}")
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
            return {
                "response": parsed_json,
                "status": "success",
            }
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
                        return {
                            "response": parsed_json,
                            "status": "success",
                        }
                
                # Try to extract JSON array or object from the text
                array_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
                if array_match:
                    json_text = array_match.group()
                    parsed_json = json.loads(json_text)
                    logger.info("Successfully extracted JSON array: %s", type(parsed_json))
                    return {
                        "response": parsed_json,
                        "status": "success",
                    }
                    
                object_match = re.search(r'\{.*?\}', response_text, re.DOTALL)
                if object_match:
                    json_text = object_match.group()
                    parsed_json = json.loads(json_text)
                    logger.info("Successfully extracted JSON object: %s", type(parsed_json))
                    return {
                        "response": parsed_json,
                        "status": "success",
                    }
                    
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning("Failed to extract JSON from response: %s", e)
            
            # If all else fails, wrap the response in a JSON object
            logger.warning("Could not parse JSON from response, wrapping: %s...", response_text[:100])
            return {
                "response": response_text,
                "status": "success",
                "format": "wrapped"
            }
    
    def _prepare_prompt(self, instruction: str, prompt: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Prepare the full prompt including instruction and conversation history.
        
        Args:
            instruction (str): The system instruction
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
            full_prompt += "WEB SEARCH ENABLED: You have access to real-time web search capabilities through Perplexity. Use this to find current, up-to-date information when needed. Always search for the most recent information when the user asks about current events, recent developments, or anything that might require current data.\n\n"
        
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
    
    def set_model(self, model: str) -> None:
        """
        Set the Perplexity model to use.
        
        Args:
            model (str): The model name (e.g., 'llama-3.1-sonar', 'llama-3.1-sonar-128k')
        """
        self.model = model
        logger.info("Model set to: %s", model)
    
    def get_model(self) -> str:
        """
        Get the current model being used.
        
        Returns:
            str: The current model name
        """
        return self.model
