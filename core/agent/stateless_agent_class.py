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
    
    def __init__(self, name: str, instructions: str, llm_type: str, next_node: Any = None, enable_web_search: bool = False):
        """
        Initialize the stateless agent with instructions and LLM type.
        
        Args:
            name (str): The name of the agent
            instructions (str): The instructions that define how the agent should behave
            llm_type (str): The type of LLM to use (e.g., 'gemini')
            next_node (Any, optional): The next node in the workflow, if any. Defaults to None.
        """
        self.name = name
        self.instructions = f"You are {name}. {instructions}"
        self.llm_type = llm_type
        self.llm = self._initialize_llm(enable_web_search)
        self.next_node = next_node

        if self.next_node is not None:
            tool_instructions = self.next_node.get_tool_info()
            tool_schema = self.next_node.get_input_schema_prompt()
            self.instructions = f"{self.instructions}\n\n{tool_instructions}\n\n{tool_schema}"
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
        else:
            raise ValueError(f"Unsupported LLM type: {self.llm_type}")
    
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
        
        # Use the initialized LLM to process the message
        # Since this is stateless, we don't pass any history
        try:
            if self.is_in_workflow:
                run_count = 0
                run_count += 1

                logger.info(f"{run_count} {self.name} is in workflow and next node is a {self.next_node_name}")

                response = await self.llm.query(self.instructions, message)
                logger.info(f"{run_count} {self.name} generated response: {response} for {self.next_node_name}")
                tool_response = self.next_node.run(response)
                logger.info(f"{run_count} {self.name} tool response: {tool_response} from {self.next_node_name}")

                while type(tool_response) != dict or (tool_response["success"] is False and tool_response["server_error"] is False):
                    response = await self.llm.query(self.instructions, f"User instructions: {message} \n\nRun {self.next_node_name} with input data: {response} and got error: {tool_response['error']}")

                    if response is None or (response is not None and response["status"] == "success" and response["format"] == "wrapped"):
                        logger.info(f"{run_count} {self.name} Tool call failed, generated response: {response}")
                        return f"{self.name} says tool call failed, generated response: {response['response']}"

                    tool_response = self.next_node.run(response)

                logger.info(f"{run_count} {self.name} generated response: {response}")
                return tool_response
            else:
                # Handle case when not in workflow or next_node is not a Tool
                response = await self.llm.query(self.instructions, message)
                logger.info(f"{self.name} generated response: {response}")
                return response
        except Exception as e:
            logger.error(f"{self.name} error: {e}")
            return f"Error: {e}"
