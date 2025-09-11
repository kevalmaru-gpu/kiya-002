from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseLLM(ABC):
    """
    Base class for all LLM implementations.
    Provides a common interface for different LLM providers.
    """
    
    def __init__(self, instruction: str, llm_type: str):
        """
        Initialize the base LLM with instruction and type.
        
        Args:
            instruction (str): The system instruction for the LLM
            llm_type (str): The type of LLM (e.g., 'gemini', 'openai', etc.)
        """
        self.instruction = instruction
        self.llm_type = llm_type
    
    def _initialize_llm(self):
        """
        Initialize the specific LLM based on the type.
        This method can be overridden by child classes for specific initialization.
        """
        pass
    
    @abstractmethod
    def query(self, prompt: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Query the LLM with a prompt and optional conversation history.
        
        Args:
            prompt (str): The user's prompt/query
            history (Optional[List[Dict[str, str]]]): Conversation history in format:
                [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        
        Returns:
            str: The LLM's response
        """
        pass
    
    def get_instruction(self) -> str:
        """Get the current instruction."""
        return self.instruction
    
    def set_instruction(self, instruction: str):
        """Update the instruction."""
        self.instruction = instruction
    
    def get_llm_type(self) -> str:
        """Get the LLM type."""
        return self.llm_type
