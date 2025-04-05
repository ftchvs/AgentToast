#!/usr/bin/env python3
"""
Simple test of using the agents SDK tools.
"""

import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import asyncio

from agents import Agent, Runner, function_tool

# Define input model
class WeatherInput(BaseModel):
    city: str = Field(description="The city to get weather for")

# Define a tool using the function_tool decorator
@function_tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"The weather in {city} is sunny and 75 degrees."

async def main():
    # Load environment variables
    load_dotenv()
    
    # Make sure we have an API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables")
        return
    
    # Create an agent with the tool
    agent = Agent(
        name="WeatherAgent",
        instructions="You provide weather information when asked.",
        tools=[get_weather],
        model="gpt-3.5-turbo"
    )
    
    # Run the agent
    result = await Runner.run(agent, "What's the weather like in San Francisco?")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main()) 