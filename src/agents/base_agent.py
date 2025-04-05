from typing import Dict, Any, Optional, List
from agents import Agent, Runner, Tool
from abc import ABC, abstractmethod
import logging
import os

class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(
        self,
        name: str,
        instructions: str,
        tools: Optional[List[Tool]] = None,
        model: str = "gpt-4-turbo-preview",
    ):
        """Initialize the base agent with name, instructions, and optional tools."""
        self.agent = Agent(
            name=name,
            instructions=instructions,
            tools=tools or [],
        )
        self.model = model

    def add_tool(self, tool: Tool):
        """Add a tool to the agent."""
        self.agent.tools.append(tool)

    async def run(self, task: str) -> Dict[Any, Any]:
        """Run the agent asynchronously with the given task."""
        try:
            result = await Runner.run(self.agent, input=task)
            return {"success": True, "result": result.final_output}
        except Exception as e:
            logging.error(f"Error running agent: {str(e)}")
            return {"success": False, "error": str(e)}

    def run_sync(self, task: str) -> Dict[Any, Any]:
        """Run the agent synchronously with the given task."""
        try:
            result = Runner.run_sync(self.agent, input=task)
            return {"success": True, "result": result.final_output}
        except Exception as e:
            logging.error(f"Error running agent: {str(e)}")
            return {"success": False, "error": str(e)}

    @abstractmethod
    def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task. Must be implemented by subclasses."""
        pass

    def plan_and_act(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Plan and execute a task with tracing."""
        try:
            result = self._execute_task(task)
            return {
                'success': True,
                'result': result,
                'error': None
            }
        except Exception as e:
            return {
                'success': False,
                'result': None,
                'error': str(e)
            }

    def get_traces(self) -> List[Dict[str, Any]]:
        """Get all traces from the agent's execution history."""
        return self.agent.traces 