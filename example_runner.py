#!/usr/bin/env python3
"""
Example script to demonstrate the updated agent framework with tracing and verbosity.
"""

import os
import asyncio
import argparse
from dotenv import load_dotenv
import logging

from src.agents.example_agent import NewsAgent, NewsRequest
from src.config import VERBOSITY, LOG_LEVEL, ENABLE_TRACING, MODEL_NAME, MODEL_CONFIG

# Set up argument parser
parser = argparse.ArgumentParser(description="Run the example news agent")
parser.add_argument("--category", type=str, default="general", 
                    help="News category (general, business, technology, etc.)")
parser.add_argument("--count", type=int, default=5, 
                    help="Number of articles to fetch (1-10)")
parser.add_argument("--verbose", action="store_true", 
                    help="Enable verbose output")
parser.add_argument("--trace", action="store_true", 
                    help="Enable tracing")
parser.add_argument("--model", type=str, choices=list(MODEL_CONFIG.keys()), default=MODEL_NAME,
                    help=f"Model to use (default: {MODEL_NAME})")
parser.add_argument("--temperature", type=float, default=None,
                    help="Temperature setting for model (0.0-1.0)")

async def main():
    """Run the example news agent with provided arguments."""
    # Parse command line arguments
    args = parser.parse_args()
    
    # Update environment variables based on arguments
    if args.trace:
        os.environ["ENABLE_TRACING"] = "true"
    
    if args.verbose:
        os.environ["VERBOSITY"] = "debug"
        logging.basicConfig(level=logging.DEBUG)
    
    # Update model environment variable
    if args.model:
        os.environ["OPENAI_MODEL"] = args.model
    
    # Get model display name
    model_info = MODEL_CONFIG.get(args.model, {"name": args.model})
    model_display_name = model_info.get("name", args.model)
    
    # Create the agent with specified settings
    agent = NewsAgent(
        verbose=args.verbose,
        model=args.model,
        temperature=args.temperature
    )
    
    print(f"\nRunning NewsAgent to fetch {args.count} articles from '{args.category}' category")
    print(f"Model: {model_display_name}")
    if args.temperature is not None:
        print(f"Temperature: {args.temperature}")
    print(f"Verbose mode: {'enabled' if args.verbose else 'disabled'}")
    print(f"Tracing: {'enabled' if ENABLE_TRACING or args.trace else 'disabled'}")
    
    try:
        # Create the request
        request = NewsRequest(
            category=args.category,
            count=args.count
        )
        
        # Run the agent
        result = await agent.run(request)
        
        # Display the result
        print("\n" + "="*80)
        print(f"NEWS SUMMARY: {args.category.upper()}")
        print("="*80)
        print(f"Articles found: {result.article_count}")
        print("\nSUMMARY:")
        print("-"*80)
        print(result.summary)
        print("-"*80)
        
        print("\nARTICLES:")
        for i, article in enumerate(result.articles, 1):
            print(f"\n{i}. {article.title}")
            print(f"   Source: {article.source}")
            print(f"   URL: {article.url}")
        
        # If tracing is enabled, print the trace ID
        traces = agent.get_traces()
        if traces:
            print(f"\nTrace IDs for debugging:")
            for trace in traces:
                print(f"- {trace['name']}: {trace['trace_id']}")
    
    except Exception as e:
        print(f"Error running agent: {str(e)}")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run the main async function
    asyncio.run(main()) 