from abc import ABC, abstractmethod
from typing import Any, Dict, Union, Optional


class Tool(ABC):
    """
    Abstract base class for tools that can be used by agents.
    Each tool must implement the required methods for input validation and execution.
    """
    
    def __init__(self, name: str, description: str = "", input_schema: Optional[Dict] = None):
        self.name = name
        self.description = description
        self.input_schema = input_schema
    
    def get_input_schema_prompt(self) -> str:
        """
        Returns a string prompt describing the expected input schema for this tool.
        If input_schema is provided, generates dynamic schema description.
        Otherwise, calls the abstract method for custom implementation.
        
        Returns:
            str: A description of the input schema
        """
        if self.input_schema is not None:
            return self._generate_dynamic_schema_prompt()
        else:
            return self._get_custom_input_schema_prompt()
    
    def _get_custom_input_schema_prompt(self) -> str:
        """
        Override this method in subclasses for custom schema descriptions.
        This is called when no input_schema dictionary is provided.
        
        Returns:
            str: A description of the input schema
        """
        return f"{self.name} Input Schema: No schema defined. Override _get_custom_input_schema_prompt() for custom implementation."
    
    def _generate_dynamic_schema_prompt(self) -> str:
        """
        Dynamically generate input schema prompt based on self.input_schema dictionary.
        """
        if not isinstance(self.input_schema, dict):
            return "Invalid input schema: self.input_schema must be a dictionary"
        
        # Generate schema description
        schema_lines = [
            f"{self.name} Input Schema:",
            "The input should be a list of dictionaries with the following fields:",
            "["
        ]
        
        # Add field definitions from input_schema
        schema_lines.append("    {")
        for field_name, field_info in self.input_schema.items():
            if isinstance(field_info, dict):
                field_type = field_info.get('type', 'string')
                field_required = field_info.get('required', False)
                field_description = field_info.get('description', '')
                required_text = " (required)" if field_required else " (optional)"
                schema_lines.append(f'        "{field_name}": "{field_type}{required_text} - {field_description}"')
            else:
                schema_lines.append(f'        "{field_name}": "{field_info}"')
        
        schema_lines.append("    }")
        schema_lines.append("]")
        
        # Generate example based on schema
        schema_lines.append("")
        schema_lines.append("Example:")
        schema_lines.append("[")
        schema_lines.append("    {")
        
        for field_name, field_info in self.input_schema.items():
            if isinstance(field_info, dict):
                field_type = field_info.get('type', 'string')
                example_value = self._get_example_value(field_name, field_type)
                schema_lines.append(f'        "{field_name}": {example_value}')
            else:
                schema_lines.append(f'        "{field_name}": "example_value"')
        
        schema_lines.append("    }")
        schema_lines.append("]")
        
        return "\n".join(schema_lines)
    
    def _get_example_value(self, field_name: str, field_type: str) -> str:
        """
        Generate example values based on field name and type.
        """
        if field_type == "array" or field_type.startswith("array of"):
            if "phone" in field_name.lower():
                return '["+1-555-123-4567", "+1-555-987-6543"]'
            elif "email" in field_name.lower():
                return '["contact@example.com", "sales@example.com"]'
            else:
                return '["item1", "item2", "item3"]'
        elif field_type == "string":
            if "company" in field_name.lower():
                return '"Acme Corporation"'
            elif "website" in field_name.lower():
                return '"https://www.example.com"'
            elif "location" in field_name.lower():
                return '"123 Business St, City, State 12345"'
            else:
                return '"example_string"'
        elif field_type == "number" or field_type == "integer":
            return "123"
        elif field_type == "boolean":
            return "true"
        else:
            return '"example_value"'
    
    def validate_input_schema(self, input_data: Any) -> Union[bool, str]:
        """
        Validates the input data against the tool's expected schema.
        If input_schema is provided, performs dynamic validation.
        Otherwise, calls the custom validation method.
        
        Args:
            input_data: The input data to validate
            
        Returns:
            Union[bool, str]: True if validation passes, or a string error message
                            describing the current input schema and what's wrong
        """
        if self.input_schema is not None:
            return self._validate_dynamic_schema(input_data)
        else:
            return self._validate_custom_schema(input_data)
    
    def _validate_custom_schema(self, input_data: Any) -> Union[bool, str]:  # pylint: disable=unused-argument
        """
        Override this method in subclasses for custom validation logic.
        This is called when no input_schema dictionary is provided.
        
        Args:
            input_data: The input data to validate
            
        Returns:
            Union[bool, str]: True if validation passes, or error message
        """
        return True  # Default: always pass validation
    
    def _validate_dynamic_schema(self, input_data: Any) -> Union[bool, str]:
        """
        Validate that input_data matches the expected schema using self.input_schema dictionary.
        
        Args:
            input_data: The input data to validate
            
        Returns:
            Union[bool, str]: True if validation passes, or error message
        """
        try:
            # Check if input_data is a list
            if not isinstance(input_data, list):
                return "Input data must be a list of dictionaries"
            
            # Check if list is not empty
            if not input_data:
                return "Input data cannot be an empty list"
            
            # Get required fields from schema
            required_fields = []
            for field_name, field_info in self.input_schema.items():
                if isinstance(field_info, dict) and field_info.get('required', False):
                    required_fields.append(field_name)
                elif not isinstance(field_info, dict):
                    # If field_info is not a dict, assume it's required
                    required_fields.append(field_name)
            
            # Validate each item in the list
            for i, item in enumerate(input_data):
                if not isinstance(item, dict):
                    return f"Item at index {i} must be a dictionary"
                
                # Check required fields
                for field in required_fields:
                    if field not in item:
                        return f"Item at index {i} is missing required field: {field}"
                
                # Validate each field according to schema
                for field_name, field_info in self.input_schema.items():
                    if field_name not in item:
                        continue  # Skip optional fields that are not present
                    
                    field_value = item[field_name]
                    
                    if isinstance(field_info, dict):
                        field_type = field_info.get('type', 'string')
                        
                        # Validate based on type
                        validation_result = self._validate_field_type(
                            field_value, field_type, field_name, i
                        )
                        if validation_result != True:
                            return validation_result
                    else:
                        # If field_info is not a dict, do basic validation
                        if not field_value and field_info.get('required', False) is True:
                            return f"Item at index {i}: {field_name} cannot be empty"
            
            return True
            
        except (ValueError, TypeError, KeyError) as e:
            return f"Validation error: {str(e)}"
    
    def _validate_field_type(self, field_value: Any, field_type: str, field_name: str, item_index: int) -> Union[bool, str]:
        """
        Validate a field value based on its expected type.
        """
        if field_type == "string":
            if not isinstance(field_value, str) or not field_value.strip() and self.input_schema.get(field_name, {}).get('required', False) is True:
                return f"Item at index {item_index}: {field_name} must be a non-empty string"
        
        elif field_type == "array" or field_type.startswith("array of"):
            if not isinstance(field_value, list):
                return f"Item at index {item_index}: {field_name} must be a list"
            
            if not field_value and self.input_schema.get(field_name, {}).get('required', False) is True:  # Check if list is not empty
                return f"Item at index {item_index}: {field_name} list cannot be empty"
            
            # Validate array items
            for j, item in enumerate(field_value):
                if not isinstance(item, str) or not item.strip():
                    return f"Item at index {item_index}, {field_name} at index {j}: must be a non-empty string"
                
                # Basic email format validation for email fields
                if "email" in field_name.lower() and ("@" not in item or "." not in item.split("@")[-1]):
                    return f"Item at index {item_index}, {field_name} at index {j}: invalid email format"
        
        elif field_type == "number" or field_type == "integer":
            if not isinstance(field_value, (int, float)):
                return f"Item at index {item_index}: {field_name} must be a number"
        
        elif field_type == "boolean":
            if not isinstance(field_value, bool):
                return f"Item at index {item_index}: {field_name} must be a boolean"
        
        return True
    
    @abstractmethod
    def run(self, input_data: Any) -> Dict[str, Any]:
        f"""
        Executes the tool with the provided input data.
        
        Args:
            input_data: The input data to process
            
        Returns:
            {
                "success": True | False,
                "server_error": True | False,
                "response": The result of the tool execution
                "error": The error message if the tool execution fails
            }
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
