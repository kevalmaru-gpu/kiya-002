from pydantic import BaseModel, ValidationError, Field
from typing import Any, Dict, Optional
import json
import logging

# Configure logger for routes module
logger = logging.getLogger(__name__)


class SchemaData(BaseModel):
    """
    Schema validation model for the data structure:
    { type: "", data: {} }
    """
    type: str = Field(..., min_length=1, description="Type field must be a non-empty string")
    data: Dict[str, Any] = Field(default_factory=dict, description="Data field must be a dictionary")


def validate_schema(json_data: str) -> tuple[bool, Optional[SchemaData], Optional[str]]:
    """
    Validate JSON data against the schema.
    
    Args:
        json_data (str): JSON string to validate
        
    Returns:
        tuple: (is_valid, validated_data, error_message)
    """
    logger.debug(f"Validating JSON schema: {json_data}")
    
    try:
        # Parse JSON string
        parsed_data = json.loads(json_data)
        logger.debug(f"JSON parsed successfully: {parsed_data}")
        
        # Validate against Pydantic model
        validated_data = SchemaData(**parsed_data)
        logger.info(f"Schema validation successful - Type: {validated_data.type}")
        
        return True, validated_data, None
        
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error: {str(e)}")
        return False, None, f"Invalid JSON format: {str(e)}"
        
    except ValidationError as e:
        logger.warning(f"Schema validation error: {str(e)}")
        return False, None, f"Schema validation error: {str(e)}"
        
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}", exc_info=True)
        return False, None, f"Unexpected error: {str(e)}"


def validate_schema_dict(data: Dict[str, Any]) -> tuple[bool, Optional[SchemaData], Optional[str]]:
    """
    Validate dictionary data against the schema.
    
    Args:
        data (Dict[str, Any]): Dictionary to validate
        
    Returns:
        tuple: (is_valid, validated_data, error_message)
    """
    logger.debug(f"Validating dictionary schema: {data}")
    
    try:
        # Validate against Pydantic model
        validated_data = SchemaData(**data)
        logger.info(f"Dictionary schema validation successful - Type: {validated_data.type}")
        
        return True, validated_data, None
        
    except ValidationError as e:
        logger.warning(f"Dictionary schema validation error: {str(e)}")
        return False, None, f"Schema validation error: {str(e)}"
        
    except Exception as e:
        logger.error(f"Unexpected error during dictionary validation: {str(e)}", exc_info=True)
        return False, None, f"Unexpected error: {str(e)}"


def validate_websocket_message(message: Dict[str, Any]) -> tuple[bool, Optional[SchemaData], Optional[str]]:
    """
    Validate WebSocket message against the schema.
    This is a convenience function for WebSocket message validation.
    
    Args:
        message (Dict[str, Any]): WebSocket message to validate
        
    Returns:
        tuple: (is_valid, validated_data, error_message)
    """
    logger.debug(f"Validating WebSocket message: {message}")
    return validate_schema_dict(message)


