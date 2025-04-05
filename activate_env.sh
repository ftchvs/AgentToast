#!/bin/bash
# Script to activate the virtual environment

echo "Activating virtual environment..."
source .venv/bin/activate

# Print Python and environment information
echo "Python version: $(python --version)"
echo "Virtual environment: $VIRTUAL_ENV"
echo ""
echo "Environment activated. Run 'deactivate' to exit."
echo ""
echo "You can now run the agent with:"
echo "./run_agent.py --agent news --category technology --count 2 --model gpt-3.5-turbo"
echo ""
echo "Or run tests with:"
echo "./test_agents.py" 