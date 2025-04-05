"""Logging configuration for AgentToast."""
import logging
import sys
from typing import Any, Dict

from pythonjsonlogger import jsonlogger

from .config import get_settings

settings = get_settings()


def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with JSON formatting."""
    logger = logging.getLogger(name)
    
    # Set log level based on environment
    log_level = logging.DEBUG if settings.app_debug else logging.INFO
    logger.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create JSON formatter
    class CustomJsonFormatter(jsonlogger.JsonFormatter):
        def add_fields(
            self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]
        ) -> None:
            """Add custom fields to the log record."""
            super().add_fields(log_record, record, message_dict)
            log_record["app"] = "agenttoast"
            log_record["environment"] = settings.app_env
            if not log_record.get("time"):
                log_record["time"] = self.formatTime(record)
    
    formatter = CustomJsonFormatter(
        "%(time)s %(name)s %(levelname)s %(message)s"
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger


# Create default logger
logger = setup_logger("agenttoast") 