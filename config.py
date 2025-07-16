# config.py
import os
from typing import Dict, Any
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def get_env(key: str, default: str = None) -> str:
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