"""Configuration settings for AgentToast."""

import os
import logging
from typing import Optional, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Agent configuration
DEFAULT_MODEL = "gpt-4o"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Model configuration
MODEL_CONFIG: Dict[str, Dict[str, any]] = {
    "gpt-3.5-turbo": {
        "name": "GPT-3.5 Turbo",
        "max_tokens": 4096,
        "temperature": 0.1,
        "timeout": 30
    },
    "gpt-4-turbo-preview": {
        "name": "GPT-4 Turbo",
        "max_tokens": 4096,
        "temperature": 0.1,
        "timeout": 45
    },
    "gpt-4o": {
        "name": "GPT-4o",
        "max_tokens": 4096,
        "temperature": 0.1,
        "timeout": 60
    }
}

# Allow model override from environment
MODEL_NAME = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
MODEL = MODEL_CONFIG.get(MODEL_NAME, MODEL_CONFIG[DEFAULT_MODEL])

# Tracing configuration
ENABLE_TRACING = os.getenv("ENABLE_TRACING", "False").lower() == "true"
TRACING_API_URL = os.getenv("TRACING_API_URL", "https://api.openai.com/v1")

# Verbosity settings
VERBOSITY_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

VERBOSITY = os.getenv("VERBOSITY", "info").lower()
LOG_LEVEL = VERBOSITY_LEVELS.get(VERBOSITY, logging.INFO)

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name and configured log level."""
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    return logger 
