"""Tracing utilities for OpenAI Agents SDK."""

import os
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from agents.tracing.spans import Span
from agents.tracing.traces import Trace
from agents.agent import Agent
from src.config import ENABLE_TRACING, OPENAI_API_KEY, get_logger

logger = get_logger(__name__)

class TracingManager:
    """Manages tracing for agent operations."""
    
    def __init__(self):
        """Initialize the tracing manager."""
        self.enabled = ENABLE_TRACING
        self.traces: List[Dict[str, Any]] = []
        
        if self.enabled and OPENAI_API_KEY:
            try:
                from agents.tracing.setup import set_tracing_export_api_key
                set_tracing_export_api_key(OPENAI_API_KEY)
                logger.info("Tracing enabled with OpenAI API key")
            except ImportError:
                logger.warning("Could not import tracing export functionality")
                self.enabled = False
        else:
            if not ENABLE_TRACING:
                logger.info("Tracing is disabled by configuration")
            elif not OPENAI_API_KEY:
                logger.warning("Tracing disabled: No OpenAI API key found")
    
    @contextmanager
    def trace(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for tracing an operation."""
        if not self.enabled:
            yield None
            return
            
        from agents.tracing.create import trace
        with trace(name=name, metadata=metadata or {}) as current_trace:
            logger.debug(f"Started trace: {name} (ID: {current_trace.trace_id})")
            yield current_trace
            self.traces.append({
                "trace_id": current_trace.trace_id,
                "name": name,
                "metadata": metadata or {}
            })
            logger.debug(f"Completed trace: {name} (ID: {current_trace.trace_id})")
    
    @contextmanager
    def span(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for creating a span within a trace."""
        if not self.enabled:
            yield None
            return
            
        from agents.tracing.create import agent_span
        with agent_span(name=name, metadata=metadata or {}) as span:
            logger.debug(f"Started span: {name}")
            yield span
            logger.debug(f"Completed span: {name}")
    
    def get_traces(self) -> List[Dict[str, Any]]:
        """Get all recorded traces."""
        return self.traces

# Create a singleton instance
tracing = TracingManager() 
