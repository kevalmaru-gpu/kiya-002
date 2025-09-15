from core.llm.perplexity_llm import PerplexityLLM
from ..llm.gemini_llm import GeminiLLM
from ..llm.base_llm import BaseLLM
import logging
from typing import Any
from ..tool.tool_class import Tool

logger = logging.getLogger(__name__)

class StatelessAgent:
    """
    A simple stateless agent that processes requests without tracking history.
    
    This agent is designed to be simple and lightweight, focusing on
    processing individual requests based on provided instructions.
    """
    
    def __init__(self, name: str, instructions: str, llm_type: str, next_node: Any = None, enable_web_search: bool = False, process_as_array: bool = False, include_fields: list = None):
        """
        Initialize the stateless agent with instructions and LLM type.
        
        Args:
            name (str): The name of the agent
            instructions (str): The instructions that define how the agent should behave
            llm_type (str): The type of LLM to use (e.g., 'gemini')
            next_node (Any, optional): The next node in the workflow, if any. Defaults to None.
            enable_web_search (bool): Whether to enable web search functionality
            process_as_array (bool): Whether to process input as array
            include_fields (list, optional): List of specific field names to include in readable output. If None, includes all fields.
        """
        self.name = name
        self.instructions = f"You are {name}. {instructions}"
        self.llm_type = llm_type
        self.llm = self._initialize_llm(enable_web_search)
        self.next_node = next_node
        self.process_as_array = process_as_array
        self.include_fields = include_fields
        
        if self.next_node is not None:
            tool_schema = self.next_node._generate_dynamic_schema_prompt()
            self.instructions = f"{self.instructions}\n\n{tool_schema}"
            self.is_in_workflow = True
            self.next_node_name = self.next_node.name if self.next_node else 'Tool'
        else:
            self.is_in_workflow = False

        logger.info(f"Stateless Agent {self.name} initialized with LLM type: {self.llm_type}")
    
    def _initialize_llm(self, enable_web_search: bool = False) -> BaseLLM:
        """
        Initialize the appropriate LLM based on the llm_type.
        
        Returns:
            BaseLLM: The initialized LLM instance
        """
        if self.llm_type.lower() == "gemini":
            return GeminiLLM(self.instructions, "gemini-2.5-flash", enable_web_search=enable_web_search)
        elif self.llm_type.lower() == "perplexity":
            return PerplexityLLM(self.instructions, "sonar-pro", enable_web_search=enable_web_search)
        else:
            raise ValueError(f"Unsupported LLM type: {self.llm_type}")
    
    def _convert_json_to_readable_string(self, data: Any, indent_level: int = 0, current_path: str = "") -> str:
        """
        Convert JSON data (dict, list, or nested structures) to a readable string format.
        Only includes fields specified in self.include_fields if provided.
        
        Args:
            data: Input data that can be a dict, list, or other types
            indent_level: Current indentation level for nested structures
            current_path: Current path in the data structure for field filtering
            
        Returns:
            str: Readable string format of the data
        """
        indent = "  " * indent_level
        
        if isinstance(data, dict):
            # Convert dictionary to readable format with proper indentation
            readable_lines = []
            for key, value in data.items():
                # Build current field path for filtering
                field_path = f"{current_path}.{key}" if current_path else key
                
                # Filter fields if include_fields is specified
                if self.include_fields is not None:
                    # Check if this field or any of its subfields should be included
                    should_include = any(
                        field == field_path or field.startswith(field_path + ".") or
                        # Also check if this field is directly in the include_fields list (for nested fields)
                        key in self.include_fields
                        for field in self.include_fields
                    )
                    if not should_include:
                        continue
                    
                if isinstance(value, (str, int, float, bool, type(None))):
                    readable_lines.append(f"{indent}{key}: {value}")
                elif isinstance(value, list):
                    if not value:  # Empty list
                        readable_lines.append(f"{indent}{key}: []")
                    elif all(isinstance(item, (str, int, float, bool, type(None))) for item in value):
                        # List of primitive values
                        readable_lines.append(f"{indent}{key}: {', '.join(map(str, value))}")
                    else:
                        # List of complex objects
                        readable_lines.append(f"{indent}{key}:")
                        for i, item in enumerate(value, 1):
                            readable_lines.append(f"{indent}  [{i}]: {self._convert_json_to_readable_string(item, indent_level + 2, field_path + f'[{i}]')}")
                elif isinstance(value, dict):
                    readable_lines.append(f"{indent}{key}:")
                    readable_lines.append(self._convert_json_to_readable_string(value, indent_level + 1, field_path))
                else:
                    readable_lines.append(f"{indent}{key}: {str(value)}")
            return '\n'.join(readable_lines)
        
        elif isinstance(data, list):
            if not data:  # Empty list
                return "[]"
            elif all(isinstance(item, (str, int, float, bool, type(None))) for item in data):
                # List of primitive values
                return f"[{', '.join(map(str, data))}]"
            else:
                # List of complex objects
                readable_sections = []
                for i, item in enumerate(data, 1):
                    readable_sections.append(f"{indent}[{i}]: {self._convert_json_to_readable_string(item, indent_level + 1, current_path + f'[{i}]')}")
                return '\n'.join(readable_sections)
        
        else:
            # Return as-is if not a dict or list
            return str(data)

    def before_call(self, input_data: Any) -> Any:
        """
        Process input data before calling the agent.
        Converts JSON format input to readable string format.
        
        Args:
            input_data: The input data to process
            
        Returns:
            Processed input data in readable string format
        """
        # Process any dict or list structure, including mixed arrays and nested objects
        if isinstance(input_data, (dict, list)):
            altered_input_data = self._convert_json_to_readable_string(input_data)
        else:
            altered_input_data = input_data
        
        return altered_input_data

    async def call(self, message: str) -> str:
        """
        Process a message and return a response.
        
        This method processes the input message based on the agent's instructions
        without maintaining any conversation history.
        
        Args:
            message (str): The input message to process
            
        Returns:
            str: The agent's response to the message
        """
        logger.info(f"{self.name} is processing message: {message}")
        
        # Process input data using before_call method
        processed_message = self.before_call(message)

        print(message, 'log1')
        print(processed_message, 'log2')

        # Use the initialized LLM to process the message
        # Since this is stateless, we don't pass any history
        try:
            if self.is_in_workflow:
                run_count = 0
                run_count += 1

                logger.info(f"{run_count} {self.name} is in workflow and next node is a {self.next_node_name}")

                response = await self.llm.query(self.instructions, processed_message)

                print(response, 'log3')

                if response.get('status') != 'success':
                    raise Exception(f"{self.name} error: {response.get('error', 'Unknown error')}")

                response = response.get('response')

                logger.info(f"{run_count} {self.name} generated response: {response} for {self.next_node_name}")
                tool_response = self.next_node.run(response)
                logger.info(f"{run_count} {self.name} tool response: {tool_response} from {self.next_node_name}")

                while type(tool_response) != dict or (tool_response.get("success", True) is False and tool_response.get("server_error", False) is False):
                    # error_msg = tool_response.get('error', 'Unknown error') if isinstance(tool_response, dict) else str(tool_response)
                    response = await self.llm.query(self.instructions, f"User instructions: {processed_message} \n\nResponse generated by LLM in last cycle {response} got error: {tool_response}. Now generate new response without these errors or new errors..")

                    if response is None or (response is not None and isinstance(response, dict) and response.get("status") == "success" and response.get("format") == "wrapped"):
                        logger.info(f"{run_count} {self.name} Tool call failed, generated response: {response}")
                        response_text = response.get('response', str(response)) if isinstance(response, dict) else str(response)
                        return {
                            "success": False,
                            "error": f"{self.name} says tool call failed, generated response: {response_text}"
                        }

                    tool_response = self.next_node.run(response)
 
                logger.info(f"{run_count} {self.name} generated response: {response}")
                return {
                    "success": True,
                    "data": tool_response.get("response", {}) if isinstance(tool_response, dict) else tool_response
                }
            else:
                # Handle case when not in workflow or next_node is not a Tool
                response = await self.llm.query(self.instructions, processed_message)
                logger.info(f"{self.name} generated response: {response}")
                return {
                    "success": True,
                    "data": response
                }
        except Exception as e:
            logger.error(f"{self.name} error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
