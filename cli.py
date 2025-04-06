#!/usr/bin/env python3
"""
AgentToast Interactive CLI

This script provides a user-friendly command-line interface for the AgentToast
multi-agent news analysis system. It allows users to interactively select news
categories and various configuration options.

Usage:
    python cli.py

The script will guide you through setting up and running the news analysis
with appropriate configuration options.
"""

import os
import sys
import asyncio
import argparse
import inquirer
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

# Ensure we can import the run_agent module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import run_agent

# Define constants
NEWS_CATEGORIES = [
    "top-headlines",
    "general", 
    "business", 
    "technology", 
    "sports", 
    "entertainment", 
    "health", 
    "science"
]

ANALYSIS_DEPTHS = ["basic", "moderate", "deep"]
SUMMARY_STYLES = ["formal", "conversational", "brief"]
VOICE_OPTIONS = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
AGENT_MODES = ["coordinator", "news", "planner", "all"]
MODEL_OPTIONS = ["gpt-3.5-turbo", "gpt-4-turbo-preview"]

def validate_count(value, answers=None) -> bool:
    """Validate the article count is between 1 and 10."""
    try:
        # Handle case where value might be a dict or another object
        if isinstance(value, dict) and answers is not None:
            return True  # Skip validation in this case
        
        count = int(value)
        return 1 <= count <= 10
    except (ValueError, TypeError):
        return False

def validate_float(value, answers=None) -> bool:
    """Validate input is a float between 0 and 1."""
    try:
        # Empty values are allowed
        if not value:
            return True
        
        # Handle case where value might be a dict or another object
        if isinstance(value, dict) and answers is not None:
            return True
            
        val = float(value)
        return 0 <= val <= 1
    except (ValueError, TypeError):
        return False

def validate_max_facts(value, answers=None) -> bool:
    """Validate max facts is a positive integer."""
    try:
        # Handle case where value might be a dict or another object
        if isinstance(value, dict) and answers is not None:
            return True
            
        count = int(value)
        return count > 0
    except (ValueError, TypeError):
        return False

def get_cli_args() -> Dict[str, Any]:
    """Get command-line arguments using interactive prompts."""
    
    # Check for API keys in environment
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️ Warning: OPENAI_API_KEY not found in environment or .env file")
        print("Please set up your OpenAI API key before proceeding.")
    
    if not os.getenv("NEWS_API_KEY"):
        print("\n⚠️ Warning: NEWS_API_KEY not found in environment or .env file")
        print("Please set up your News API key before proceeding.")
    
    print("\n🔍 AgentToast Interactive CLI")
    print("============================")
    
    # Start with the basic questions
    questions = [
        inquirer.List(
            "agent", 
            message="Select agent mode to run",
            choices=AGENT_MODES,
            default="coordinator"
        ),
        inquirer.List(
            "category",
            message="Select news category",
            choices=NEWS_CATEGORIES,
            default="general"
        ),
        inquirer.Text(
            "count",
            message="Number of articles to fetch (1-10)",
            default="5",
            validate=validate_count
        ),
        inquirer.List(
            "model",
            message="Select AI model to use",
            choices=MODEL_OPTIONS,
            default="gpt-3.5-turbo"
        ),
        inquirer.Text(
            "temperature",
            message="Model temperature (0.0-1.0, leave empty for default)",
            default="",
            validate=lambda x, answers=None: not x or validate_float(x, answers)
        )
    ]
    
    # Get the basic answers
    answers = inquirer.prompt(questions)
    
    # Convert count to integer
    answers["count"] = int(answers["count"])
    
    # Convert temperature to float if provided
    if answers["temperature"]:
        answers["temperature"] = float(answers["temperature"])
    else:
        answers["temperature"] = None
    
    # Additional questions based on agent mode
    if answers["agent"] in ["coordinator", "all"]:
        # Analysis options
        analysis_questions = [
            inquirer.List(
                "analysis_depth",
                message="Select analysis depth",
                choices=ANALYSIS_DEPTHS,
                default="moderate"
            ),
            inquirer.Confirm(
                "use_fact_check",
                message="Enable fact checking?",
                default=True
            ),
            inquirer.Confirm(
                "use_trend_analysis",
                message="Enable trend analysis?",
                default=True
            )
        ]
        
        analysis_answers = inquirer.prompt(analysis_questions)
        answers.update(analysis_answers)
        
        # If fact checking is enabled, ask for max claims
        if answers["use_fact_check"]:
            max_facts_question = [
                inquirer.Text(
                    "max_fact_claims",
                    message="Maximum number of fact claims to check",
                    default="5",
                    validate=validate_max_facts
                )
            ]
            max_facts_answer = inquirer.prompt(max_facts_question)
            answers["max_fact_claims"] = int(max_facts_answer["max_fact_claims"])
    
    # Audio options
    audio_questions = [
        inquirer.Confirm(
            "generate_audio",
            message="Generate audio summary?",
            default=True
        )
    ]
    
    audio_answers = inquirer.prompt(audio_questions)
    answers["generate_audio"] = audio_answers["generate_audio"]
    
    if answers["generate_audio"]:
        audio_config_questions = [
            inquirer.List(
                "voice",
                message="Select voice for audio",
                choices=VOICE_OPTIONS,
                default="alloy"
            ),
            inquirer.List(
                "summary_style",
                message="Select summary style",
                choices=SUMMARY_STYLES,
                default="conversational"
            ),
            inquirer.Confirm(
                "play_audio",
                message="Play audio after generation?",
                default=False
            )
        ]
        
        audio_config_answers = inquirer.prompt(audio_config_questions)
        answers.update(audio_config_answers)
    
    # Output options
    output_questions = [
        inquirer.Confirm(
            "save_markdown",
            message="Save news summary as Markdown?",
            default=False
        ),
        inquirer.Confirm(
            "save_analysis",
            message="Save analysis as separate file?",
            default=False
        ),
        inquirer.Confirm(
            "full_report",
            message="Generate comprehensive report?",
            default=False
        ),
        inquirer.Confirm(
            "verbose",
            message="Enable verbose output?",
            default=False
        ),
        inquirer.Confirm(
            "trace",
            message="Enable tracing?",
            default=False
        )
    ]
    
    output_answers = inquirer.prompt(output_questions)
    answers.update(output_answers)
    
    # Advanced options (optional)
    advanced_question = [
        inquirer.Confirm(
            "show_advanced",
            message="Configure advanced options?",
            default=False
        )
    ]
    
    show_advanced = inquirer.prompt(advanced_question)
    
    if show_advanced["show_advanced"]:
        advanced_questions = [
            inquirer.Text(
                "country",
                message="Country code (e.g., us, gb) [optional]",
                default=""
            ),
            inquirer.Text(
                "sources",
                message="News sources (comma-separated, e.g., bbc-news,cnn) [optional]",
                default=""
            ),
            inquirer.Text(
                "query",
                message="Search query [optional]",
                default=""
            ),
            inquirer.Text(
                "page",
                message="Page number [optional]",
                default=""
            ),
            inquirer.Text(
                "output_dir",
                message="Output directory",
                default="output"
            )
        ]
        
        advanced_answers = inquirer.prompt(advanced_questions)
        
        # Update answers with non-empty advanced options
        for key, value in advanced_answers.items():
            if value:
                if key == "page" and value.isdigit():
                    answers[key] = int(value)
                else:
                    answers[key] = value
    
    # Set defaults for any missing options
    if "output_dir" not in answers:
        answers["output_dir"] = "output"
    
    # Convert to run_agent argument format
    args = argparse.Namespace()
    
    # Basic options
    args.agent = answers["agent"]
    args.category = answers["category"]
    args.count = answers["count"]
    args.model = answers["model"]
    args.temperature = answers["temperature"]
    args.verbose = answers.get("verbose", False)
    args.trace = answers.get("trace", False)
    
    # Audio options
    args.no_audio = not answers.get("generate_audio", True)
    args.voice = answers.get("voice", "alloy")
    args.play_audio = answers.get("play_audio", False)
    args.summary_style = answers.get("summary_style", "conversational")
    
    # Analysis options
    args.analysis_depth = answers.get("analysis_depth", "moderate")
    args.no_fact_check = not answers.get("use_fact_check", True)
    args.no_trend_analysis = not answers.get("use_trend_analysis", True)
    args.max_fact_claims = answers.get("max_fact_claims", 5)
    
    # Output options
    args.save_markdown = answers.get("save_markdown", False)
    args.save_analysis = answers.get("save_analysis", False)
    args.full_report = answers.get("full_report", False)
    args.output_dir = answers.get("output_dir", "output")
    
    # Advanced News API options
    args.country = answers.get("country", None)
    args.sources = answers.get("sources", None)
    args.query = answers.get("query", None)
    args.page = answers.get("page", None)
    
    return args

async def main():
    """Main function to run the interactive CLI."""
    print("\n📰 Welcome to AgentToast News Analysis System!")
    
    try:
        args = get_cli_args()
        
        print("\n⚙️ Configuration Summary:")
        print(f"  Agent: {args.agent}")
        print(f"  Category: {args.category}")
        print(f"  Articles: {args.count}")
        print(f"  Model: {args.model}")
        
        # Show analysis config for coordinator
        if args.agent in ["coordinator", "all"]:
            print(f"  Analysis: {args.analysis_depth}")
            print(f"  Fact checking: {'enabled' if not args.no_fact_check else 'disabled'}")
            print(f"  Trend analysis: {'enabled' if not args.no_trend_analysis else 'disabled'}")
        
        # Show audio config
        print(f"  Audio generation: {'enabled' if not args.no_audio else 'disabled'}")
        if not args.no_audio:
            print(f"    Voice: {args.voice}")
            print(f"    Style: {args.summary_style}")
            print(f"    Play after generation: {'yes' if args.play_audio else 'no'}")
        
        print("\n🚀 Starting news analysis process...\n")
        
        if args.agent == "planner":
            await run_agent.run_planner_agent(args)
        elif args.agent == "news":
            await run_agent.run_news_agent(args)
        elif args.agent == "coordinator":
            await run_agent.run_coordinator_agent(args)
        else:  # args.agent == "all"
            await run_agent.run_all_agents(args)
        
        print("\n✅ News analysis complete!")
        
    except KeyboardInterrupt:
        print("\n\n❌ Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run the main async function
    asyncio.run(main()) 
