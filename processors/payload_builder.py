import logging
from typing import Dict, Any
from pydantic import ValidationError
from .schemas import SocialProfileSchema

# Configure logger
logger = logging.getLogger(__name__)

def build_ai_payload(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes raw dictionary data from the scrapers, validates and sanitizes it 
    through the SocialProfileSchema, and returns a finalized JSON dictionary.
    """
    try:
        # Pass the raw data into the Pydantic model for automatic 
        # type coercion, validation, and sanitization (via field_validators)
        profile = SocialProfileSchema(**raw_data)
        
        # Return the clean dictionary representation including computed fields
        # This payload is now ready to be piped to the LLM pipeline
        return profile.model_dump()
        
    except ValidationError as e:
        # Catch strict typing or validation errors
        logger.error(f"Data validation failed for payload. Errors: {e.errors()}")
        # Return a structured error response so the pipeline doesn't crash entirely
        return {
            "error": "validation_failed", 
            "details": e.errors(),
            "original_handle": raw_data.get("target_handle", "unknown")
        }
    except Exception as e:
        # Catch unexpected structural errors
        logger.error(f"Unexpected error during payload building: {e}")
        return {
            "error": "unexpected_error", 
            "details": str(e)
        }
