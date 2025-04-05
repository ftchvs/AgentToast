"""Base agent class for AgentToast."""
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

from pydantic import BaseModel

from .config import get_settings
from .logger import logger

settings = get_settings()


class Agent(ABC):
    """Base class for all agents in AgentToast.
    
    This class provides the foundation for building specialized agents that can
    perform various tasks in the system. Each agent has access to configuration
    settings and logging capabilities.
    
    Attributes:
        settings: Application configuration settings
        logger: Configured logger instance
        name: Agent identifier name
        metadata: Optional metadata about the agent
    """

    def __init__(self, name: str = None, metadata: Dict = None):
        """Initialize the agent.
        
        Args:
            name: Optional name for the agent. Defaults to class name.
            metadata: Optional metadata about the agent.
        """
        self.settings = settings
        self.logger = logger
        self.name = name or self.__class__.__name__
        self.metadata = metadata or {}
        
        self.logger.info(
            f"Initializing agent",
            extra={
                "agent_name": self.name,
                "agent_type": self.__class__.__name__
            }
        )

    @abstractmethod
    async def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the agent's main functionality.
        
        This method must be implemented by all agent subclasses to define
        their specific behavior and processing logic.
        
        Args:
            *args: Positional arguments specific to the agent implementation
            **kwargs: Keyword arguments specific to the agent implementation
            
        Returns:
            Any: Agent-specific output
            
        Raises:
            NotImplementedError: If the subclass does not implement this method
        """
        pass
    
    async def initialize(self) -> None:
        """Optional initialization hook.
        
        Subclasses can override this method to perform any necessary
        setup before the agent starts running.
        """
        pass
    
    async def cleanup(self) -> None:
        """Optional cleanup hook.
        
        Subclasses can override this method to perform any necessary
        cleanup after the agent finishes running.
        """
        pass
    
    def __str__(self) -> str:
        """Return string representation of the agent."""
        return f"{self.name} ({self.__class__.__name__})" 