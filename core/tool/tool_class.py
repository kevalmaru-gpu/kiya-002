from abc import ABC, abstractmethod
from typing import Any, Dict, Union


class Tool(ABC):
    """
    Abstract base class for tools that can be used by agents.
    Each tool must implement the required methods for input validation and execution.
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    @abstractmethod
    def get_input_schema_prompt(self) -> str:
        """
        Returns a string prompt describing the expected input schema for this tool.
        This should explain what parameters the tool expects and their types.
        
        Returns:
            str: A description of the input schema
        """
    
    @abstractmethod
    def validate_input_schema(self, input_data: Any) -> Union[bool, str]:
        """
        Validates the input data against the tool's expected schema.
        
        Args:
            input_data: The input data to validate
            
        Returns:
            Union[bool, str]: True if validation passes, or a string error message
                            describing the current input schema and what's wrong
        """
    
    @abstractmethod
    def run(self, input_data: Any) -> Any:
        """
        Executes the tool with the provided input data.
        
        Args:
            input_data: The input data to process
            
        Returns:
            Any: The result of the tool execution
        """
    
    def get_tool_info(self) -> Dict[str, str]:
        """
        Returns basic information about the tool.
        
        Returns:
            Dict[str, str]: Dictionary containing tool name and description
        """
        return {
            "name": self.name,
            "description": self.description
        }
