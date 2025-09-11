import logging
from typing import Any, List

logger = logging.getLogger(__name__)

class Workflow:
    def __init__(self, name: str, nodes: List[Any]):
        self.nodes = nodes
        self.name = name
        self.global_context = ''

        logger.info(f"Workflow {self.name} initialized with {len(self.nodes)} nodes")
    

    def run(self, prompt: str):
        next_node_input = {}

        try:
            for node in self.nodes:
                next_node_input = node.call(f"User instructions: {prompt} \n\nRun {node.name} with input data: {next_node_input}")
                if next_node_input['success'] is False:
                    logger.error(f"Workflow {self.name} node {node.name} failed with input data: {next_node_input}")
                    raise Exception(f"Workflow {self.name} node {node.name} failed with input data: {next_node_input}")
        except Exception as e:
            logger.error(f"Workflow {self.name} failed with input data: {input_data}")

        return next_node_input

    def add_node(self, node: Any):
        self.nodes.append(node)
        logger.info(f"Workflow {self.name} added node {node.name}")
    
    def remove_node(self, node: Any):
        self.nodes.remove(node)
        logger.info(f"Workflow {self.name} removed node {node.name}")
    
    def get_next_node(self, index: int) -> Any:
        return self.nodes[index + 1]
    
    def get_nodes(self) -> List[Any]:
        return self.nodes