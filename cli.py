#!/usr/bin/env python3
"""
AgentToast Interactive CLI (Simplified)

This script provides a simple command-line interface for the AgentToast
multi-agent news analysis system. It takes a natural language prompt from the user.

Usage:
    python cli.py
    python cli.py --prompt "Get the latest business news from the US"
    python cli.py --prompt "Summarize tech news and save as markdown" --save-markdown --verbose

Optional arguments can be passed to override defaults or specific behaviors.
"""

import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

# Ensure we can import the run_agent module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import run_agent
from src.config import MODEL_CONFIG

# Keep only essential arguments for CLI override
cli_parser = argparse.ArgumentParser(description="Run AgentToast Coordinator via CLI")
cli_parser.add_argument("prompt", nargs='?', type=str, default=None, 
                        help="Natural language user request (e.g., 'latest tech news in the US'). If omitted, you will be prompted.")
cli_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
cli_parser.add_argument("--trace", action="store_true", help="Enable tracing")
cli_parser.add_argument("--use-planner", action="store_true", help="Use PlannerAgent to determine workflow")
cli_parser.add_argument("--model", type=str, choices=list(MODEL_CONFIG.keys()), default="gpt-4o", help="Default model for agents")
cli_parser.add_argument("--no-audio", action="store_true", help="Disable audio generation")
cli_parser.add_argument("--save-pdf", action="store_true", help="Save the final report as a PDF file")
cli_parser.add_argument("--output-dir", type=str, default="output", help="Directory to save output files")
cli_parser.add_argument("--play-audio", action="store_true", help="Play generated audio")
# Add other essential overrides if necessary (e.g., specific agent models)

async def main():
    """Main entry point for the simplified CLI."""
    load_dotenv()
    cli_args = cli_parser.parse_args()

    # Check for API keys
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("NEWS_API_KEY"):
        print("\n⚠️ Warning: API keys (OPENAI_API_KEY, NEWS_API_KEY) not found in environment or .env file.")
        print("Please set them up before proceeding.")
        # Decide whether to exit or continue
        # exit(1) 

    print("\n🚀 Welcome to AgentToast!"
          )
    # Get prompt interactively if not provided as argument
    if not cli_args.prompt:
        try:
            cli_args.prompt = input("Enter your news request (e.g., 'latest tech news in the US'): ")
        except EOFError:
            print("\nNo input received. Exiting.")
            return
        if not cli_args.prompt:
            print("Empty prompt received. Exiting.")
            return

    print(f"\nProcessing request: '{cli_args.prompt}'")

    # Prepare args for run_agent.main by simulating the full namespace
    # We pass the CLI args and let run_agent handle defaults for the rest
    run_agent_args = argparse.Namespace(
        prompt=cli_args.prompt,
        verbose=cli_args.verbose,
        trace=cli_args.trace,
        use_planner=cli_args.use_planner,
        model=cli_args.model,
        no_audio=cli_args.no_audio,
        save_pdf=cli_args.save_pdf,
        output_dir=cli_args.output_dir,
        play_audio=cli_args.play_audio,
        # Set other args required by run_coordinator_agent to None initially
        # run_agent.py will fill defaults from its argparse setup
        category=None,
        count=None,
        country=None,
        sources=None,
        query=None,
        ticker=None,
        summary_style=None,
        analysis_depth=None,
        no_fact_check=None,
        no_trend_analysis=None,
        max_fact_claims=None,
        voice=None,
        temperature=None,
        news_model=None,
        planner_model=None,
        analyst_model=None,
        factchecker_model=None,
        trend_model=None,
        writer_model=None,
        finance_model=None,
        save_analysis=None,
        full_report=None
    )

    # Run the appropriate agent function based on the collected args
    try:
        # Call the main function in run_agent, which now expects args
        # We need to ensure run_agent.main handles the namespace correctly
        # Let's modify run_agent.main to accept args directly instead of parsing again
        await run_agent.run_coordinator_agent(run_agent_args)
    except Exception as e:
        print(f"\n❌ An error occurred during processing: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
