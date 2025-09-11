from controller.agent_tool_controller import test_agent_tool
from controller.llm_controller import test_llm
from controller.agent_controller import test_agent
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

async def handle_websocket_message(requestData: Dict[str, Any]):
    logger.info(f"Data: {requestData}")

    type = requestData.type
    data = requestData.data
    
    logger.info(f"Handling WebSocket message: {type} with data: {data}")
    

    if type == "llm_request":
        return await test_llm()
    elif type == "agent_request":
        return await test_agent()
    elif type == "agent_tool_request":
        return await test_agent_tool(data['message'])
    else:
        return "Invalid type"