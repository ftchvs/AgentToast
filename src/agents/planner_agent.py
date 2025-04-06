"""Agent responsible for planning news processing strategy."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.agents.base_agent import BaseAgent
from src.utils.tracing import tracing
from src.config import get_logger

logger = get_logger(__name__)

class PlannerInput(BaseModel):
    """Input model for the planner agent."""
    
    count: int = Field(
        default=5,
        description="Number of articles to process"
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="List of news categories to process"
    )
    voice: str = Field(
        default="alloy",
        description="Voice to use for audio generation"
    )

class PlanStep(BaseModel):
    """A step in the processing plan."""
    
    step: int
    action: str
    params: Dict[str, Any]

class ProcessingPlan(BaseModel):
    """The processing plan for news articles."""
    
    steps: List[PlanStep]
    estimated_time: int  # in seconds

class PlannerOutput(BaseModel):
    """Output model for the planner agent."""
    
    success: bool
    plan: Optional[ProcessingPlan] = None
    error: Optional[str] = None
    trace_id: Optional[str] = None

class PlannerAgent(BaseAgent[PlannerInput, PlannerOutput]):
    """Agent responsible for planning news processing strategy."""
    
    def __init__(self, verbose: bool = False, model: str = None, temperature: float = None):
        """Initialize the PlannerAgent."""
        super().__init__(
            name="NewsPlannerAgent",
            instructions="""
            I am a planning agent that creates strategies for processing news articles.
            I consider factors like article relevance, content quality, and audience engagement.
            
            My responsibilities include:
            1. Creating a step-by-step processing plan for news articles
            2. Determining the optimal parameters for each processing step
            3. Adapting the plan based on article count and categories
            
            I return a structured processing plan with well-defined steps in JSON format like:
            
            {
                "steps": [
                    {
                        "step": 1,
                        "action": "fetch_news",
                        "params": {"category": "top-headlines", "count": 5}
                    },
                    {
                        "step": 2,
                        "action": "analyze",
                        "params": {"depth": "moderate"}
                    }
                ],
                "estimated_time": 60
            }
            
            The steps array must contain step, action, and params fields. Ensure all output is valid JSON.
            """,
            tools=[],  # No specific tools needed for planning
            verbose=verbose,
            model=model,
            temperature=temperature
        )
        
        logger.info("PlannerAgent initialized")
    
    async def create_plan(self, input_data: PlannerInput) -> PlannerOutput:
        """
        Create a processing plan for news articles.
        
        Args:
            input_data: The input data for planning
            
        Returns:
            The planning result
        """
        try:
            # Run the agent
            result = await self.run(input_data)
            return result
        except Exception as e:
            # Handle any errors
            logger.error(f"Error creating plan: {str(e)}")
            return PlannerOutput(
                success=False,
                error=str(e),
                trace_id=None
            )
    
    def _process_output(self, output: str) -> PlannerOutput:
        """
        Process the agent's output into a structured plan.
        
        Args:
            output: The raw output from the agent
            
        Returns:
            A structured planning result
        """
        # Check for empty or whitespace-only output
        if not output or output.strip() == "":
            logger.error("Empty output received from agent")
            return PlannerOutput(
                success=False,
                error="Empty output received from agent",
                trace_id=None
            )
        
        # Try to extract JSON if output contains JSON within other text
        import json
        import re
        
        # Look for JSON-like patterns
        json_pattern = r'({[\s\S]*})'
        json_match = re.search(json_pattern, output)
        
        if json_match:
            try:
                # Try to parse the extracted JSON
                potential_json = json_match.group(1)
                data = json.loads(potential_json)
                
                # Extract the steps
                steps_data = data.get("steps", [])
                steps = []
                
                for step_data in steps_data:
                    step = PlanStep(
                        step=step_data.get("step", 0),
                        action=step_data.get("action", ""),
                        params=step_data.get("params", {})
                    )
                    steps.append(step)
                
                # Create the plan
                plan = ProcessingPlan(
                    steps=steps,
                    estimated_time=data.get("estimated_time", 60)
                )
                
                # Get the trace ID from the tracing manager
                traces = tracing.get_traces()
                trace_id = traces[0].get("trace_id") if traces else None
                
                # Return the result
                return PlannerOutput(
                    success=True,
                    plan=plan,
                    trace_id=trace_id
                )
            except json.JSONDecodeError:
                pass  # Continue to next method if JSON extraction fails
        
        try:
            # Try to parse the whole output as JSON
            data = json.loads(output)
            
            # Extract the steps
            steps_data = data.get("steps", [])
            steps = []
            
            for step_data in steps_data:
                step = PlanStep(
                    step=step_data.get("step", 0),
                    action=step_data.get("action", ""),
                    params=step_data.get("params", {})
                )
                steps.append(step)
            
            # Create the plan
            plan = ProcessingPlan(
                steps=steps,
                estimated_time=data.get("estimated_time", 60)
            )
            
            # Get the trace ID from the tracing manager
            traces = tracing.get_traces()
            trace_id = traces[0].get("trace_id") if traces else None
            
            # Return the result
            return PlannerOutput(
                success=True,
                plan=plan,
                trace_id=trace_id
            )
        
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            # Handle parsing errors
            logger.error(f"Error processing agent output: {str(e)}")
            
            # Try to extract basic steps using regex
            steps = []
            step_pattern = r"Step (\d+):?\s*([a-zA-Z]+)(.*?)(?=Step \d+:|$)"
            
            matches = re.finditer(step_pattern, output, re.DOTALL)
            for i, match in enumerate(matches):
                try:
                    step_num = int(match.group(1))
                    action = match.group(2).strip().lower()
                    details = match.group(3).strip()
                    
                    # Try to extract parameters
                    params = {}
                    param_pattern = r"(\w+):\s*([^,\n]+)"
                    param_matches = re.finditer(param_pattern, details)
                    
                    for param_match in param_matches:
                        param_name = param_match.group(1).strip().lower()
                        param_value = param_match.group(2).strip()
                        
                        # Try to convert numeric values
                        try:
                            if param_value.isdigit():
                                param_value = int(param_value)
                            elif param_value.replace('.', '', 1).isdigit():
                                param_value = float(param_value)
                        except:
                            pass
                            
                        params[param_name] = param_value
                    
                    step = PlanStep(
                        step=step_num,
                        action=action,
                        params=params
                    )
                    steps.append(step)
                except Exception as e:
                    logger.warning(f"Error parsing step {i+1}: {str(e)}")
            
            if steps:
                plan = ProcessingPlan(
                    steps=steps,
                    estimated_time=60  # Default value
                )
                
                return PlannerOutput(
                    success=True,
                    plan=plan,
                    trace_id=None
                )
            
            # If no steps could be parsed, create a basic default plan
            if not steps:
                logger.warning("Generating default plan as fallback")
                
                # Create a minimal default plan based on input context
                default_steps = [
                    PlanStep(
                        step=1,
                        action="fetch_news",
                        params={"category": "top-headlines", "count": 5}
                    ),
                    PlanStep(
                        step=2,
                        action="analyze",
                        params={"depth": "moderate"}
                    ),
                    PlanStep(
                        step=3,
                        action="summarize",
                        params={"format": "audio", "voice": "alloy"}
                    )
                ]
                
                plan = ProcessingPlan(
                    steps=default_steps,
                    estimated_time=120
                )
                
                return PlannerOutput(
                    success=True,
                    plan=plan,
                    trace_id=None
                )
            
            return PlannerOutput(
                success=False,
                error=f"Failed to parse output: {str(e)}",
                trace_id=None
            ) 