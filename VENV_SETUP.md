# Virtual Environment Setup

This project uses a Python virtual environment to manage dependencies. Follow these steps to set up and use the environment:

## Initial Setup

1. Create a new virtual environment:

```bash
python3 -m venv .venv
```

2. Activate the virtual environment:

```bash
source .venv/bin/activate  # On Unix/MacOS
# or
.\.venv\Scripts\activate  # On Windows
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

## Using the Environment

1. Use the provided activation script:

```bash
./activate_env.sh  # On Unix/MacOS
```

2. Run the agent:

```bash
./run_agent.py --agent news --category technology --count 2 --model gpt-3.5-turbo
```

3. Run tests:

```bash
./test_agents.py
```

## Note on OpenAI Agents SDK

This project uses the `openai-agents` package, which requires a different import pattern than the previous `openai.agents`. The imports are now:

```python
from agents import Agent, Tool, Runner
```

instead of:

```python
from openai.agents import Agent, Tool, Runner
```

## Deactivating the Environment

When you're done working with the project, you can deactivate the virtual environment:

```bash
deactivate
``` 