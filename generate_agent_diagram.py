#!/usr/bin/env python3
"""
Generates Mermaid.js diagram definitions for agent interactions.
This script analyzes the agent code and produces diagrams visualizing
the structure and relationships between different agents and tools.
"""

import os
import re
import ast
import glob
from pathlib import Path
from collections import defaultdict

# Paths to analyze
AGENTS_DIR = "src/agents"
TOOLS_DIR = "src/tools"
OUTPUT_FILE = "agent_diagram_detailed.md"

class AgentInfo:
    """Stores information about an agent."""
    def __init__(self, name, file_path):
        self.name = name
        self.file_path = file_path
        self.input_type = None
        self.output_type = None
        self.tools = []
        self.calls_to = set()
        self.inherits_from = None
        self.methods = []

class ToolInfo:
    """Stores information about a tool."""
    def __init__(self, name, file_path):
        self.name = name
        self.file_path = file_path
        self.description = ""
        self.used_by = set()

def extract_agent_info(file_path):
    """Extract information about an agent from its file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract class name
    class_match = re.search(r'class\s+(\w+)(?:\([\w\[\],\s]+\))?:', content)
    if not class_match:
        return None
    
    agent_name = class_match.group(1)
    if not agent_name.endswith('Agent'):
        return None
    
    agent = AgentInfo(agent_name, file_path)
    
    # Extract inheritance
    inheritance_match = re.search(r'class\s+' + agent_name + r'\s*\(\s*(\w+)[\[\],\s\w]*\):', content)
    if inheritance_match:
        agent.inherits_from = inheritance_match.group(1)
    
    # Extract input and output types
    type_hints = re.findall(r'async def run\s*\(\s*self\s*,\s*input_data\s*:\s*(\w+)\s*\)\s*->\s*(\w+)', content)
    if type_hints:
        agent.input_type, agent.output_type = type_hints[0]
    
    # Extract method names
    methods = re.findall(r'def\s+(\w+)\s*\(\s*self', content)
    agent.methods = [m for m in methods if not m.startswith('_')]
    
    # Extract tool usage and agent calls
    tool_matches = re.findall(r'self\.tools\.append\(\s*(\w+)', content)
    agent.tools = tool_matches
    
    # Look for agent instantiations
    agent_calls = re.findall(r'(\w+Agent)\s*\(', content)
    agent.calls_to = set([call for call in agent_calls if call != agent_name])
    
    return agent

def extract_tool_info(file_path):
    """Extract information about a tool from its file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract class name
    class_match = re.search(r'class\s+(\w+)(?:\([\w\[\],\s]+\))?:', content)
    if not class_match:
        return None
    
    tool_name = class_match.group(1)
    if not tool_name.endswith('Tool'):
        return None
    
    tool = ToolInfo(tool_name, file_path)
    
    # Extract description
    doc_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if doc_match:
        tool.description = doc_match.group(1).strip().split('\n')[0]
    
    return tool

def find_tool_usage(agents, tools):
    """Find which agents use which tools."""
    # Analyze each agent file to find tool usage
    for agent in agents.values():
        with open(agent.file_path, 'r') as f:
            content = f.read()
        
        for tool_name, tool in tools.items():
            if tool_name in content:
                agent.tools.append(tool_name)
                tool.used_by.add(agent.name)

def generate_class_diagram(agents):
    """Generate a Mermaid class diagram for agents."""
    diagram = ["```mermaid", "classDiagram"]
    
    # Add inheritance relationships
    for agent_name, agent in agents.items():
        if agent.inherits_from and agent.inherits_from in agents:
            diagram.append(f"    {agent.inherits_from} <|-- {agent_name}")
    
    # Add class details
    for agent_name, agent in agents.items():
        diagram.append(f"    class {agent_name} {{")
        
        # Add properties
        if agent.input_type:
            diagram.append(f"        +{agent.input_type} input_type")
        if agent.output_type:
            diagram.append(f"        +{agent.output_type} output_type")
        
        # Add methods
        for method in agent.methods[:5]:  # Limit to 5 methods to avoid cluttered diagrams
            diagram.append(f"        +{method}()")
        
        diagram.append("    }")
    
    diagram.append("```")
    return '\n'.join(diagram)

def generate_flow_diagram(agents, tools):
    """Generate a Mermaid flow diagram for agent interactions."""
    diagram = ["```mermaid", "graph TD"]
    
    # Add agents
    for agent_name in agents:
        diagram.append(f"    {agent_name}[{agent_name}]")
    
    # Add tools
    for tool_name in tools:
        diagram.append(f"    {tool_name}[{tool_name}]")
    
    # Add relationships
    for agent_name, agent in agents.items():
        for called_agent in agent.calls_to:
            if called_agent in agents:
                diagram.append(f"    {agent_name} -->|calls| {called_agent}")
        
        for tool_name in agent.tools:
            if tool_name in tools:
                diagram.append(f"    {agent_name} -->|uses| {tool_name}")
    
    # Add styling
    coordinator_agents = [name for name in agents if "Coordinator" in name or "Orchestrator" in name]
    if coordinator_agents:
        for coord in coordinator_agents:
            diagram.append(f"    class {coord} coordinator;")
        diagram.append("    classDef coordinator fill:#f9d,stroke:#333,stroke-width:2px;")
    
    diagram.append("```")
    return '\n'.join(diagram)

def generate_sequence_diagram(agents):
    """Generate a Mermaid sequence diagram for agent interactions."""
    diagram = ["```mermaid", "sequenceDiagram"]
    
    # Find all agents including a Coordinator/Orchestrator
    coordinator_agents = [name for name in agents if "Coordinator" in name or "Orchestrator" in name]
    
    if not coordinator_agents:
        # If no coordinator found, just show all agents
        diagram.append("    participant User")
        for agent_name in agents:
            short_name = agent_name.replace("Agent", "")
            diagram.append(f"    participant {short_name} as {agent_name}")
        
        # Simple flow if no coordinator
        diagram.append("    User->>"+list(agents.keys())[0]+": Request")
        diagram.append("    "+list(agents.keys())[-1]+"-->>User: Response")
    else:
        # Setup with coordinator
        coordinator = coordinator_agents[0]
        diagram.append("    participant User")
        diagram.append(f"    participant Coord as {coordinator}")
        
        # Add other agents
        for agent_name in agents:
            if agent_name != coordinator:
                short_name = agent_name.replace("Agent", "")
                diagram.append(f"    participant {short_name} as {agent_name}")
        
        # Initial interaction
        diagram.append("    User->>Coord: Submit Task")
        
        # Interactions between coordinator and agents
        for agent_name in agents:
            if agent_name != coordinator:
                short_name = agent_name.replace("Agent", "")
                diagram.append(f"    Coord->>+{short_name}: Process Task")
                diagram.append(f"    {short_name}-->>-Coord: Return Result")
        
        # Final response
        diagram.append("    Coord-->>User: Return Final Result")
    
    diagram.append("```")
    return '\n'.join(diagram)

def main():
    """Main function to analyze agent files and generate diagrams."""
    # Collect all agent and tool files
    agent_files = glob.glob(os.path.join(AGENTS_DIR, "*_agent.py"))
    tool_files = glob.glob(os.path.join(TOOLS_DIR, "*_tool.py"))
    
    # Extract information
    agents = {}
    for file_path in agent_files:
        agent = extract_agent_info(file_path)
        if agent:
            agents[agent.name] = agent
    
    tools = {}
    for file_path in tool_files:
        tool = extract_tool_info(file_path)
        if tool:
            tools[tool.name] = tool
    
    # Find tool usage
    find_tool_usage(agents, tools)
    
    # Generate diagrams
    class_diagram = generate_class_diagram(agents)
    flow_diagram = generate_flow_diagram(agents, tools)
    sequence_diagram = generate_sequence_diagram(agents)
    
    # Create output file
    with open(OUTPUT_FILE, 'w') as f:
        f.write("# Detailed Agent Interaction Diagrams\n\n")
        f.write("## Agent Class Hierarchy\n\n")
        f.write(class_diagram + "\n\n")
        f.write("## Agent & Tool Interaction Flow\n\n")
        f.write(flow_diagram + "\n\n")
        f.write("## Message Sequence Flow\n\n")
        f.write(sequence_diagram + "\n\n")
        
        # Also write a list of agents and tools
        f.write("## Agents in the System\n\n")
        for agent_name, agent in agents.items():
            f.write(f"### {agent_name}\n\n")
            f.write(f"- Input Type: {agent.input_type or 'Not specified'}\n")
            f.write(f"- Output Type: {agent.output_type or 'Not specified'}\n")
            f.write(f"- Tools Used: {', '.join(agent.tools) or 'None'}\n")
            f.write(f"- Calls Agents: {', '.join(agent.calls_to) or 'None'}\n")
            f.write(f"- Methods: {', '.join(agent.methods[:5]) or 'None'}")
            if len(agent.methods) > 5:
                f.write(f" (+ {len(agent.methods) - 5} more)")
            f.write("\n\n")
        
        f.write("## Tools in the System\n\n")
        for tool_name, tool in tools.items():
            f.write(f"### {tool_name}\n\n")
            f.write(f"- Description: {tool.description or 'No description'}\n")
            f.write(f"- Used by: {', '.join(tool.used_by) or 'No agents'}\n\n")

    print(f"Generated agent diagrams in {OUTPUT_FILE}")

if __name__ == "__main__":
    main() 