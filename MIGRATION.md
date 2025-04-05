# Migration Guide: Upgrading to OpenAI Agents SDK

This guide explains how to migrate your existing agents to the new OpenAI Agents SDK implementation with improved tracing, verbosity features, and cost-efficient model selection.

## Overview of Changes

1. **New Agent Base Class**: Using the updated `BaseAgent` in `src/agents/updated_base_agent.py`
2. **Typed Inputs/Outputs**: Using Pydantic models for type-safe communication
3. **Tracing System**: Enhanced tracing with the `tracing` utility
4. **Tool Management**: Dedicated tools directory with standardized tool implementation
5. **Configuration**: Centralized configuration in `src/config.py`
6. **Verbosity Controls**: Configurable logging levels
7. **Cost-efficient Models**: Default to GPT-3.5 Turbo instead of GPT-4

## Migration Steps

### 1. Update Your Environment

Add these environment variables to your `.env` file:

```
ENABLE_TRACING=false  # Set to true to enable tracing
VERBOSITY=info        # Options: debug, info, warning, error, critical
OPENAI_MODEL=gpt-3.5-turbo  # Default model (cheaper than GPT-4)
```

### 2. Migrate an Agent

To migrate an existing agent like `MyAgent`:

1. Create a new file `updated_my_agent.py` with Pydantic models:

```python
from pydantic import BaseModel, Field
from src.agents.updated_base_agent import BaseAgent

# Define input model
class MyAgentInput(BaseModel):
    query: str = Field(description="The query to process")
    max_results: int = Field(default=5, description="Maximum results to return")

# Define output model
class MyAgentOutput(BaseModel):
    results: list
    success: bool
    message: str
```

2. Update the agent class to use the new base class:

```python
class MyAgent(BaseAgent[MyAgentInput, MyAgentOutput]):
    def __init__(self, verbose=False, model=None, temperature=None):
        super().__init__(
            name="MyAgent",
            instructions="Your detailed instructions here...",
            tools=[],  # Add your tools here
            verbose=verbose,
            model=model,  # Use model passed in or default from config
            temperature=temperature  # Use temperature passed in or default from config
        )
        
    def _process_output(self, output: str) -> MyAgentOutput:
        # Process the raw output from the agent
        # Return a properly structured MyAgentOutput
```

3. Add typed methods for your agent:

```python
async def process_query(self, input_data: MyAgentInput) -> MyAgentOutput:
    with tracing.trace("my_agent_query", {"input": input_data.model_dump()}) as trace:
        try:
            # Run the agent
            result = await self.run(input_data)
            
            # Add trace info if needed
            if hasattr(result, "trace_id") and not result.trace_id and trace:
                result.trace_id = trace.trace_id
                
            return result
        except Exception as e:
            # Handle errors
            return MyAgentOutput(
                results=[],
                success=False,
                message=f"Error: {str(e)}"
            )
```

### 3. Migrate Tools

1. For each custom tool, create a file in `src/tools/`:

```python
from pydantic import BaseModel, Field
from src.config import MODEL_NAME, MODEL  # Use for model configuration

class MyToolInput(BaseModel):
    parameter1: str = Field(description="Description of parameter 1")
    parameter2: int = Field(default=10, description="Description of parameter 2")

class MyTool:
    def run(self, input_data: MyToolInput) -> dict:
        # Use configured model settings if needed
        model = MODEL_NAME
        temperature = MODEL.get("temperature", 0)
        
        # Tool implementation here
        return {"result": "processed data"}

# Create instance
my_tool = MyTool()
```

2. Update `src/tools/__init__.py` to import your tool:

```python
from .my_tool import my_tool, MyToolInput, MyTool

__all__ = [
    # Existing tools
    'my_tool',
    'MyToolInput',
    'MyTool'
]
```

3. To use the tool in an agent:

```python
from agents import Tool
from src.tools.my_tool import my_tool, MyToolInput

# Create a Tool wrapper
tool = Tool.from_function(
    function=my_tool.run,
    name="my_tool",
    description="Description of what this tool does",
    input_schema=MyToolInput
)

# Add to agent
agent.add_tool(tool)
```

### 4. Update Runner Scripts

Replace calls to the old agents with the new ones:

```python
# Old way
agent = OldAgent()
result = agent.run_sync({"query": "some query"})

# New way
agent = NewAgent(
    verbose=True,
    model="gpt-3.5-turbo",  # Specify model for cost efficiency
    temperature=0.7  # Adjust as needed
)
input_data = NewAgentInput(query="some query")
result = await agent.run(input_data)
```

### 5. Testing

Run the test script to verify your migration:

```bash
./test_updated_agents.py
```

All tests use GPT-3.5 Turbo by default for cost efficiency.

### 6. Cost Efficiency

The migration uses GPT-3.5 Turbo by default to reduce costs. If you need the capabilities of GPT-4 for specific agents, you can specify it explicitly:

```python
agent = MyAgent(
    verbose=True,
    model="gpt-4-turbo-preview"  # Only use when the extra capability is needed
)
```

Command line tools support model selection:

```bash
./updated_run_agent.py --model gpt-4-turbo-preview  # Only when needed
```

## Cleanup

Once you've verified everything works:

1. Run the cleanup script to remove old files:

```bash
./cleanup.sh
```

2. Rename updated files to replace the old ones:

```bash
mv src/agents/updated_my_agent.py src/agents/my_agent.py
mv updated_run_agent.py run_agent.py
```

## Additional Resources

- See `example_agent.py` for a complete example of an agent using the new system
- See `updated_planner_agent.py` for an example of migrating an existing agent
- See `updated_run_agent.py` for an example of the updated runner script
- See `src/config.py` for model configuration options 