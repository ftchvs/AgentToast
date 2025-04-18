#!/usr/bin/env python3
"""
AgentToast Runner Script

This script runs the AgentToast coordinator agent based on a user prompt
or specified arguments.

Usage:
    python run_agent.py --prompt "Get the latest tech news from the US"
    python run_agent.py --category business --count 3 --verbose

Arguments:
    --prompt: Natural language request for the agent (e.g., "Summarize business news")
    --category, --count, etc.: Specific overrides for CoordinatorInput (optional if prompt is used)
    --model: Default model for agents (e.g., gpt-4o)
    --[agent]-model: Specific model override for an agent (e.g., --news-model gpt-3.5-turbo)
    --temperature: Model temperature (0.0-1.0)
    --verbose: Enable verbose logging
    --trace: Enable tracing
    --use-planner: Use the PlannerAgent to determine workflow
    --no-audio: Disable audio generation
    --voice: Voice for audio output
    --play-audio: Play generated audio
    --output-dir: Directory for output files
    --save-pdf: Save the final report as a PDF file
    --save-analysis: Save analysis output separately (if applicable)
    --full-report: Generate a comprehensive report (passed to CoordinatorAgent)

"""

import os
import asyncio
import argparse
from dotenv import load_dotenv
from datetime import datetime
import json
import logging
from typing import Dict, Any, Optional, List

# Removed PlannerAgent and NewsAgent specific imports as they are run via Coordinator
from src.agents.coordinator_agent import CoordinatorAgent, CoordinatorInput
from src.config import ENABLE_TRACING, LOG_LEVEL, VERBOSITY, MODEL_NAME, MODEL_CONFIG
from src.utils.tracing import tracing
from src.utils.output_utils import save_pdf_report, save_analysis_report, save_full_report, play_audio_file # Updated import

# Set up argument parser - Simplified
parser = argparse.ArgumentParser(description="Run AgentToast Coordinator Agent")

# Core Input
parser.add_argument("--prompt", type=str, default=None, 
                    help="Natural language user request (e.g., 'latest tech news in the US')")

# Coordinator Input Overrides (Optional - primarily for testing or specific use cases)
parser.add_argument("--category", type=str, default="general", 
                    help="News category override (if not using prompt)")
parser.add_argument("--count", type=int, default=5, 
                    help="Number of articles override (if not using prompt)")
parser.add_argument("--country", type=str, default=None,
                    help="Two-letter country code override")
parser.add_argument("--sources", type=str, default=None,
                    help="Comma-separated news sources override")
parser.add_argument("--query", type=str, default=None,
                    help="Keywords or phrase override")
parser.add_argument("--ticker", type=str, default=None,
                    help="Stock ticker symbol override")
parser.add_argument("--summary-style", type=str, choices=["formal", "conversational", "brief"],
                    default="conversational", help="Summary style override")
parser.add_argument("--analysis-depth", type=str, choices=["basic", "moderate", "deep"],
                    default="moderate", help="Analysis depth override")
parser.add_argument("--no-fact-check", action="store_true",
                    help="Disable fact checking override")
parser.add_argument("--no-trend-analysis", action="store_true",
                    help="Disable trend analysis override")
parser.add_argument("--max-fact-claims", type=int, default=5,
                    help="Max fact claims override")

# Agent Configuration
parser.add_argument("--verbose", action="store_true", 
                    help="Enable verbose logging")
parser.add_argument("--trace", action="store_true", 
                    help="Enable tracing")
parser.add_argument("--use-planner", action="store_true",
                    help="Use PlannerAgent to determine workflow")
parser.add_argument("--model", type=str, choices=list(MODEL_CONFIG.keys()), default="gpt-4o",
                    help="Default model for agents")
parser.add_argument("--news-model", type=str, choices=list(MODEL_CONFIG.keys()), default=None,
                    help="Model override for NewsAgent")
parser.add_argument("--planner-model", type=str, choices=list(MODEL_CONFIG.keys()), default=None,
                    help="Model override for PlannerAgent")
parser.add_argument("--analyst-model", type=str, choices=list(MODEL_CONFIG.keys()), default=None,
                    help="Model override for AnalystAgent")
parser.add_argument("--factchecker-model", type=str, choices=list(MODEL_CONFIG.keys()), default=None,
                    help="Model override for FactCheckerAgent")
parser.add_argument("--trend-model", type=str, choices=list(MODEL_CONFIG.keys()), default=None,
                    help="Model override for TrendAgent")
parser.add_argument("--writer-model", type=str, choices=list(MODEL_CONFIG.keys()), default=None,
                    help="Model override for WriterAgent")
parser.add_argument("--finance-model", type=str, choices=list(MODEL_CONFIG.keys()), default=None,
                    help="Model override for FinanceAgent") # Added finance model override arg
parser.add_argument("--temperature", type=float, default=None,
                    help="Global temperature override for models (0.0-1.0)")

# Audio Options
parser.add_argument("--no-audio", action="store_true",
                    help="Disable audio generation")
parser.add_argument("--voice", type=str, choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                    default="alloy", help="Voice for audio output")
parser.add_argument("--play-audio", action="store_true",
                    help="Play the generated audio file")

# Output Options
parser.add_argument("--output-dir", type=str, default="output",
                    help="Directory to save output files")
parser.add_argument("--save-pdf", action="store_true",
                    help="Save the final report as a PDF file")
parser.add_argument("--save-analysis", action="store_true",
                    help="Save analysis output separately (if applicable)")
parser.add_argument("--full-report", action="store_true",
                    help="Generate and save a comprehensive report with all agent outputs")

# Removed run_planner_agent and run_news_agent functions

async def run_coordinator_agent(args):
    """Run the coordinator agent."""
    print("\n🚀 Running Coordinator Agent...")
    
    # Initialize the agent
    agent = CoordinatorAgent(
        verbose=args.verbose,
        model=args.model,
        temperature=args.temperature,
        # Pass model overrides
        news_model_override=args.news_model,
        analyst_model_override=args.analyst_model,
        factchecker_model_override=args.factchecker_model,
        trend_model_override=args.trend_model,
        writer_model_override=args.writer_model,
        finance_model_override=args.finance_model,
        planner_model_override=args.planner_model
    )
    
    # Prepare input data
    # Prioritize prompt, but allow overrides from specific args
    input_data = CoordinatorInput(
        prompt=args.prompt, # Pass the prompt
        # Pass other args as potential overrides or defaults if prompt doesn't specify
        category=args.category,
        count=args.count,
        country=args.country,
        sources=args.sources,
        query=args.query,
        ticker_symbol=args.ticker,
        voice=args.voice,
        generate_audio=not args.no_audio,
        summary_style=args.summary_style,
        analysis_depth=args.analysis_depth,
        use_fact_checker=not args.no_fact_check,
        use_trend_analyzer=not args.no_trend_analysis,
        max_fact_claims=args.max_fact_claims,
        use_planner=args.use_planner
    )

    # Run the coordinator agent
    result = await agent.run(input_data)

    # --- Output Processing --- 
    print("\n" + "="*60)
    print(f"COORDINATOR AGENT RESULTS")
    print("="*60)

    if result.news_summary:
        print("\n📰 Final News Summary:")
        print("-"*50)
        print(result.news_summary)
        print("-"*50)
    else:
        print("\n📰 No final news summary was generated.")

    if result.analysis:
        print("\n📊 Analysis:")
        print(result.analysis)

    if result.fact_check:
        print("\n✅ Fact Check:")
        print(result.fact_check)

    if result.trends:
        print("\n📈 Trends:")
        print(result.trends)

    if result.financial_data:
        print("\n💰 Financial Data:")
        # Pretty print the dict
        print(json.dumps(result.financial_data, indent=2))
        if result.graph_files:
            print(f"\n📈 Generated Graphs: {', '.join(result.graph_files)}")

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Save PDF Report
    if args.save_pdf and result.markdown:
        try:
            # Use the new PDF saving function
            file_path = save_pdf_report(result.markdown, args.output_dir, input_data.category) # Pass category from input_data
            print(f"\n💾 PDF report saved to: {file_path}")
        except Exception as e:
            print(f"\n❌ Error saving PDF report: {e}")

    # Save Analysis Report
    if args.save_analysis and result.analysis:
        try:
            # Assuming save_analysis_report function exists
            file_path = save_analysis_report(result.analysis, args.output_dir, args.category)
            print(f"\n💾 Analysis report saved to: {file_path}")
        except Exception as e:
            print(f"\n❌ Error saving analysis report: {e}")

    # Save Full Report (Comprehensive)
    if args.full_report:
        try:
             # Assuming save_full_report function exists
            file_path = save_full_report(result, args.output_dir, args.category)
            print(f"\n💾 Full report saved to: {file_path}")
        except Exception as e:
            print(f"\n❌ Error saving full report: {e}")

    # Play Audio
    if args.play_audio and result.audio_file:
        print(f"\n🔊 Playing audio file: {result.audio_file}")
        try:
            # Assuming play_audio_file function exists
            play_audio_file(result.audio_file)
        except Exception as e:
            print(f"\n❌ Error playing audio file: {e}")
    elif not args.no_audio and result.audio_file:
         print(f"\n🔊 Audio file generated: {result.audio_file}")

    # Print Agent Results Summary
    print("\n📋 Agent Execution Summary:")
    for res in result.agent_results:
        status = "✅ Success" if res.success else f"❌ Failed: {res.error}"
        print(f"  - {res.agent_name}: {status}")
        
    if result.processing_plan:
        print("\n🗺️ Generated Plan:")
        for step in result.processing_plan.steps:
             print(f"  - Step {step.step}: {step.action} ({step.params})")

    print("\n" + "="*60)
    print("Coordinator Agent run finished.")
    print("="*60 + "\n")
    return result

# Removed run_all_agents function

async def main():
    """Main entry point for the script."""
    load_dotenv() # Load environment variables
    args = parser.parse_args()

    # Setup logging level based on verbosity
    log_level = logging.DEBUG if args.verbose else LOG_LEVEL
    logging.basicConfig(level=log_level)
    # Reduce log spam from dependencies
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # Configure tracing
    if args.trace or ENABLE_TRACING:
        tracing.enable()
        print("🔍 Tracing enabled.")
    else:
        tracing.disable()

    # Validate input: Prompt or specific parameters are needed
    if not args.prompt and not (args.category or args.query or args.sources or args.ticker):
        print("\n❌ Error: Please provide a --prompt or specify news criteria like --category, --query, --sources, or --ticker.")
        parser.print_help()
        return

    # Run the coordinator agent (main entry point)
    try:
        await run_coordinator_agent(args)
    except Exception as e:
        logging.exception(f"An error occurred during agent execution: {e}")
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
