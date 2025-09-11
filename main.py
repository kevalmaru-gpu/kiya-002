from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import os
import logging
from dotenv import load_dotenv
from controller.simple_lead_generation import generate_leads_controller
from utils.websocket_validator import validate_websocket_message
from routes import handle_websocket_message

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s\n',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/generate-leads")
async def generate_leads(data: dict):
    response = await generate_leads_controller(data['prompt'])
    return response

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            data = await websocket.receive_json()
            logger.debug(f"Received WebSocket message: {data}")
            
            # Validate the incoming message against our schema
            is_valid, validated_data, error = validate_websocket_message(data)
            
            if is_valid:
                logger.info(f"Valid message received - Type: {validated_data.type}, Data: {validated_data.data}")
                response = await handle_websocket_message(validated_data)
                await websocket.send_json({
                    "status": "success", 
                    "message": response
                })
            else:
                logger.warning(f"Invalid message received: {error}")
                await websocket.send_json({
                    "status": "error", 
                    "message": "Invalid message format",
                    "error": error
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "status": "error", 
                "message": "Internal server error",
                "error": str(e)
            })
        except:
            logger.error("Failed to send error response to WebSocket")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
