# Agent Diagram Tools

This directory contains several tools for visualizing and understanding the structure and interactions of agents in the AgentToast system.

## Overview

The AgentToast system uses a multi-agent architecture where different specialized agents collaborate to process news content. Understanding how these agents interact can be complex, so we've provided several visualization tools.

## Available Visualization Tools

### 1. Simple Mermaid Diagrams (`agent_diagram.md`)

This file contains static [Mermaid.js](https://mermaid-js.github.io/mermaid/) diagrams that visualize:
- Agent Architecture Overview
- Agent Class Hierarchy
- Message Flow Sequence
- Agent & Tool Relationships
- Data Flow Diagram

**Usage:**
- Open the file in a Markdown viewer that supports Mermaid diagrams (like VS Code with the Mermaid extension)
- The diagrams will render automatically

### 2. Interactive D3.js Visualization (`agent_diagram.html`)

An interactive web-based visualization using D3.js that allows you to:
- Explore the agent network with draggable nodes
- View the agent hierarchy in a tree layout
- Examine the sequence flow of operations
- Zoom, pan, and click on agents for details

**Usage:**
- Open `agent_diagram.html` in any modern web browser
- Use the tabs to switch between different visualization types
- Drag nodes to rearrange the network view
- Click on agents to see detailed information
- Use the zoom controls to adjust the view

### 3. Auto-generated Detailed Diagrams (`generate_agent_diagram.py`)

A Python script that analyzes your actual codebase to generate accurate and up-to-date diagrams based on the current implementation.

**Usage:**
```bash
# Make sure you're in the project root directory
python generate_agent_diagram.py
```

This will generate a file called `agent_diagram_detailed.md` with diagrams that reflect the actual structure of your code.

## Understanding Agent Interactions

The key agent interactions in the system are:

1. **Coordinator/Orchestrator Agent**: The central agent that manages the workflow and delegates tasks to specialized agents

2. **Specialized Agents**:
   - **News Agent**: Fetches and summarizes news articles
   - **Writer Agent**: Generates content summaries
   - **Analyst Agent**: Analyzes content for insights
   - **Fact Checker Agent**: Verifies factual claims
   - **Trend Agent**: Identifies trends in the data

3. **Agent Workflow**:
   - User submits a task to the Coordinator
   - Coordinator plans and delegates subtasks to specialized agents
   - Specialized agents process their tasks using tools
   - Results are returned to the Coordinator
   - Coordinator assembles final output for the user

## Extending the Diagrams

If you add new agents or modify the existing ones, you can:

1. Update the manually created diagrams in `agent_diagram.md`
2. Modify the D3.js visualization data in `agent_diagram.html`
3. Or simply run `generate_agent_diagram.py` again to automatically create updated diagrams

## Troubleshooting

- If the D3.js visualization doesn't appear, check your browser console for errors
- If the Mermaid diagrams don't render, ensure you're using a Markdown viewer with Mermaid support
- If the Python script fails, check that you're running it from the project root directory 