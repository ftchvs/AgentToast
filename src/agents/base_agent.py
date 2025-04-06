"""Base agent class that implements OpenAI Agents SDK properly."""

from typing import Dict, Any, Optional, List, TypeVar, Generic
from pydantic import BaseModel
import logging
from abc import ABC, abstractmethod

from agents import Agent as OpenAIAgent
from agents import Tool as OpenAITool
from agents import Runner
from agents import ModelSettings

from src.config import DEFAULT_MODEL, MODEL, MODEL_NAME, get_logger
from src.utils.tracing import tracing

# Type variable for input and output types
InputT = TypeVar('InputT', bound=BaseModel)
OutputT = TypeVar('OutputT', bound=BaseModel)

class BaseAgent(Generic[InputT, OutputT], ABC):
    """Base agent class with tracing and logging capabilities."""
    
    def __init__(
        self,
        name: str,
        instructions: str,
        tools: Optional[List[OpenAITool]] = None,
        model: str = MODEL_NAME,
        temperature: Optional[float] = None,
        verbose: bool = False
    ):
        """
        Initialize a base agent.
        
        Args:
            name: The name of the agent
            instructions: The instructions for the agent
            tools: Optional list of tools for the agent to use
            model: The model to use for the agent
            temperature: Optional temperature setting for the model (0.0-1.0)
            verbose: Whether to enable verbose logging
        """
        self.name = name
        self.instructions = instructions
        self.model = model
        self.temperature = temperature if temperature is not None else MODEL.get("temperature", 0.7)
        self.verbose = verbose
        self.logger = get_logger(f"agent.{name.lower()}")
        
        # Create model settings with temperature
        model_settings = ModelSettings(temperature=self.temperature)
        
        # Set up the OpenAI Agent
        self.agent = OpenAIAgent(
            name=name,
            instructions=instructions,
            tools=tools or [],
            model=model,
            model_settings=model_settings
        )
        
        if verbose:
            self.logger.setLevel(logging.DEBUG)
            self.logger.debug(f"Initialized {name} agent with model {model} (temp: {self.temperature}) and {len(tools or [])} tools")
    
    def add_tool(self, tool: OpenAITool) -> None:
        """
        Add a tool to the agent.
        
        Args:
            tool: The tool to add
        """
        self.agent.tools.append(tool)
        self.logger.debug(f"Added tool: {tool.name}")
    
    async def run(self, input_data: InputT) -> OutputT:
        """
        Run the agent asynchronously.
        
        Args:
            input_data: The input data for the agent
            
        Returns:
            The agent's output
        """
        if self.verbose:
            self.logger.debug(f"Running agent with input: {input_data}")
        
        # Use the tracing manager to create a trace
        with tracing.trace(f"{self.name}_execution", {"input": input_data.model_dump()}) as trace:
            try:
                # Use a span to track the actual execution
                with tracing.span(f"{self.name}_processing") as span:
                    # Convert input to string if needed
                    input_str = self._prepare_input(input_data)
                    
                    # Log model being used
                    self.logger.debug(f"Using model: {self.model} (temperature: {self.temperature})")
                    
                    # Run the agent
                    result = await Runner.run(
                        self.agent, 
                        input=input_str
                    )
                    
                    # Process the result
                    output = self._process_output(result.final_output)
                    
                    # Record the result in the span
                    if span:
                        span.set_data({
                            "status": "success",
                            "model": self.model,
                            "output": output.model_dump() if hasattr(output, "model_dump") else output
                        })
                    
                    # Log the result
                    if self.verbose:
                        self.logger.debug(f"Agent execution succeeded with result: {output}")
                    
                    # Return the result
                    return output
                    
            except Exception as e:
                # Record the error in the span
                if 'span' in locals() and span:
                    span.set_error({"message": str(e), "model": self.model})
                
                # Log the error
                self.logger.error(f"Error running agent with model {self.model}: {str(e)}")
                
                # Re-raise the exception
                raise
    
    def run_sync(self, input_data: InputT) -> OutputT:
        """
        Run the agent synchronously.
        
        Args:
            input_data: The input data for the agent
            
        Returns:
            The agent's output
        """
        if self.verbose:
            self.logger.debug(f"Running agent synchronously with input: {input_data}")
        
        # Use the tracing manager to create a trace
        with tracing.trace(f"{self.name}_execution", {"input": input_data.model_dump()}) as trace:
            try:
                # Use a span to track the actual execution
                with tracing.span(f"{self.name}_processing") as span:
                    # Convert input to string if needed
                    input_str = self._prepare_input(input_data)
                    
                    # Log model being used
                    self.logger.debug(f"Using model: {self.model} (temperature: {self.temperature})")
                    
                    # Run the agent
                    result = Runner.run_sync(
                        self.agent, 
                        input=input_str
                    )
                    
                    # Process the result
                    output = self._process_output(result.final_output)
                    
                    # Record the result in the span
                    if span:
                        span.set_data({
                            "status": "success",
                            "model": self.model,
                            "output": output.model_dump() if hasattr(output, "model_dump") else output
                        })
                    
                    # Log the result
                    if self.verbose:
                        self.logger.debug(f"Agent execution succeeded with result: {output}")
                    
                    # Return the result
                    return output
                    
            except Exception as e:
                # Record the error in the span
                if 'span' in locals() and span:
                    span.set_error({"message": str(e), "model": self.model})
                
                # Log the error
                self.logger.error(f"Error running agent with model {self.model}: {str(e)}")
                
                # Re-raise the exception
                raise
    
    def _prepare_input(self, input_data: InputT) -> str:
        """
        Prepare the input data for the agent.
        
        Args:
            input_data: The input data
            
        Returns:
            The prepared input as a string
        """
        if hasattr(input_data, "model_dump"):
            return str(input_data.model_dump())
        return str(input_data)
    
    @abstractmethod
    def _process_output(self, output: str) -> OutputT:
        """
        Process the output from the agent.
        
        Args:
            output: The raw output from the agent
            
        Returns:
            The processed output
        """
        pass
    
    def get_traces(self) -> List[Dict[str, Any]]:
        """
        Get all traces from the agent's execution history.
        
        Returns:
            A list of trace dictionaries
        """
        return tracing.get_traces() 
