#!/usr/bin/env python3
"""
Test script for the updated agents and tools.
"""

import os
import asyncio
from dotenv import load_dotenv
import unittest
from typing import Dict, Any, List

from src.agents.planner_agent import PlannerAgent, PlannerInput
from src.agents.example_agent import NewsAgent, NewsRequest
from src.tools.news_tool import fetch_news_tool
from src.tools.sentiment_tool import sentiment_tool, SentimentInput
from src.config import get_logger, MODEL_NAME

logger = get_logger(__name__)

class ToolTests(unittest.TestCase):
    """Tests for the various tools."""
    
    def test_fetch_news_tool(self):
        """Test the news fetching tool."""
        # Run the tool
        input_data = FetchNewsInput(
            category="technology",
            count=2
        )
        result = fetch_news_tool.run(input_data)
        
        # Check the result
        self.assertIsInstance(result, list)
        
        if result:  # Only check content if we got results
            self.assertGreaterEqual(len(result), 0)
            if len(result) > 0:
                article = result[0]
                self.assertIn("title", article)
                self.assertIn("description", article)
                self.assertIn("url", article)
                self.assertIn("source", article)
    
    def test_sentiment_tool(self):
        """Test the sentiment analysis tool."""
        # Run the tool with positive text
        positive_input = SentimentInput(
            text="I love this amazing product! It's the best thing I've ever used.",
            include_explanation=True
        )
        positive_result = sentiment_tool.run(positive_input)
        
        # Check the result
        self.assertIn("score", positive_result)
        self.assertIn("sentiment", positive_result)
        self.assertIn("explanation", positive_result)
        self.assertGreater(positive_result["score"], 0)
        
        # Run the tool with negative text
        negative_input = SentimentInput(
            text="This is terrible. I hate it and will never use it again.",
            include_explanation=False
        )
        negative_result = sentiment_tool.run(negative_input)
        
        # Check the result
        self.assertIn("score", negative_result)
        self.assertIn("sentiment", negative_result)
        self.assertLess(negative_result["score"], 0)
        self.assertEqual(negative_result["explanation"], "")

class AgentTests(unittest.TestCase):
    """Tests for the agents."""
    
    async def test_planner_agent(self):
        """Test the planner agent."""
        # Set up the agent - explicitly use GPT-3.5 Turbo for cost-efficient testing
        agent = PlannerAgent(
            verbose=True,
            model="gpt-3.5-turbo",
            temperature=0.2  # Lower temperature for more predictable outputs in tests
        )
        
        # Create input
        input_data = PlannerInput(
            count=3,
            categories=["technology"],
            voice="nova"
        )
        
        # Run the agent
        result = await agent.create_plan(input_data)
        
        # Check the result
        self.assertTrue(result.success)
        self.assertIsNotNone(result.plan)
        self.assertGreater(len(result.plan.steps), 0)
        
        # Check that a trace ID was generated
        self.assertIsNotNone(result.trace_id)
    
    async def test_news_agent(self):
        """Test the news agent."""
        # Set up the agent - explicitly use GPT-3.5 Turbo for cost-efficient testing
        agent = NewsAgent(
            verbose=True,
            model="gpt-3.5-turbo",
            temperature=0.2  # Lower temperature for more predictable outputs in tests
        )
        
        # Create input
        input_data = NewsRequest(
            category="technology",
            count=3
        )
        
        # Run the agent
        result = await agent.run(input_data)
        
        # Check the result
        self.assertIsNotNone(result.summary)
        self.assertGreaterEqual(len(result.articles), 0)
        self.assertEqual(result.category, "technology")

def run_tests():
    """Run the tests."""
    # Set the model to GPT-3.5 Turbo for all tests
    os.environ["OPENAI_MODEL"] = "gpt-3.5-turbo"
    
    print(f"\nRunning tests with model: {os.environ.get('OPENAI_MODEL', MODEL_NAME)}")
    
    # Run the synchronous tests
    unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(ToolTests))
    
    # Set up and run the async tests
    async def run_async_tests():
        agent_test = AgentTests()
        try:
            await agent_test.test_planner_agent()
            print("\nPlanner agent test passed")
        except Exception as e:
            print(f"\nPlanner agent test failed: {e}")
        
        try:
            await agent_test.test_news_agent()
            print("\nNews agent test passed")
        except Exception as e:
            print(f"\nNews agent test failed: {e}")
    
    # Run the async tests
    asyncio.run(run_async_tests())

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Import here to avoid circular imports
    from src.tools.news_tool import FetchNewsInput
    
    # Run the tests
    print("\nRunning tests for updated agents and tools...\n")
    run_tests() 