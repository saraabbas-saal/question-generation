import os
from typing import Dict, Any
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Helper function to get environment variables with defaults
def get_env(key: str, default: str = None) -> str:
    """
    Get environment variable with fallback to default value.
    Logs a warning if using default for important settings.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        
    Returns:
        Value of environment variable or default
    """
    value = os.environ.get(key, default)
    if value is None:
        logger.error(f"Required environment variable {key} is not set!")
    elif value == default and default is not None:
        logger.warning(f"Using default value for {key}: {default}")
    return value

# LLM Configuration
MODEL_HOST = get_env("MODEL_HOST", "http://192.168.71.70:8000")
MODEL_OPEN_AI_KEY = get_env("MODEL_OPEN_AI_KEY", "123")
DEFAULT_MODEL = get_env("DEFAULT_MODEL", "sayed0am/Adept-14B-AWQ")

# BAML Configuration
os.environ["OPENAI_API_URL"] = MODEL_HOST
os.environ["OPENAI_API_KEY"] = MODEL_OPEN_AI_KEY
os.environ["OPENAI_MODEL"] = DEFAULT_MODEL
