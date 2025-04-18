#!/usr/bin/env python3
"""
AgentToast Runner Script

This script provides a powerful multi-agent interface for news processing
with improved tracing and verbosity controls. It uses a team of specialized
AI agents to fetch, analyze, fact-check, and identify trends in news.

Usage:
    python run_agent.py --agent news --category technology --count 2 --model gpt-3.5-turbo

Basic Options:
    --agent: The agent to run (news, planner, coordinator, or all)
    --category: News category (general, business, technology, sports, etc.)
    --count: Number of articles to fetch (1-10)
    --model: Model to use (gpt-3.5-turbo, gpt-4, etc.)
    --temperature: Model temperature (0.0-1.0)
    --verbose: Enable verbose output
    --trace: Enable tracing

Audio Options:
    --voice: Voice to use for audio output (alloy, echo, fable, onyx, nova, shimmer)
    --no-audio: Disable audio generation
    --play-audio: Play the generated audio file immediately
    --output-dir: Directory to save output files
    --summary-style: Style of the audio summary (formal, conversational, brief)

Analysis Options:
    --analysis-depth: Depth of analysis (basic, moderate, deep)
    --no-fact-check: Disable fact checking
    --no-trend-analysis: Disable trend analysis
    --max-fact-claims: Maximum number of fact claims to check (default: 5)

Output Options:
    --save-markdown: Save the generated news summary as a Markdown file
    --save-analysis: Save the analysis as a separate file
    --full-report: Generate a comprehensive report with all agent outputs

Advanced News API Options:
    --country: Two-letter country code (e.g., us, gb)
    --sources: Comma-separated list of news sources (e.g., bbc-news,cnn)
    --query: Keywords or phrase to search for
    --page: Page number for paginated results

Examples:
    # Get technology news with multiple agent analysis
    python run_agent.py --agent coordinator --category technology --count 3
    
    # Get business news with deep analysis and fact checking
    python run_agent.py --agent coordinator --category business --analysis-depth deep
    
    # Get news with a formal audio summary but without trend analysis
    python run_agent.py --agent coordinator --summary-style formal --no-trend-analysis
    
    # Generate a full analysis report and save as markdown
    python run_agent.py --agent coordinator --category science --full-report --save-markdown
"""

import os
import asyncio
import argparse
from dotenv import load_dotenv
from datetime import datetime
import json
import logging
from typing import Dict, Any, Optional, List

from src.agents.planner_agent import PlannerAgent, PlannerInput
from src.agents.example_agent import NewsAgent, NewsRequest
from src.agents.coordinator_agent import CoordinatorAgent, CoordinatorInput
from src.config import ENABLE_TRACING, LOG_LEVEL, VERBOSITY, MODEL_NAME, MODEL_CONFIG
from src.utils.tracing import tracing

# Set up argument parser
parser = argparse.ArgumentParser(description="Run multi-agent news processing system")
parser.add_argument("--category", type=str, default="general", 
                    help="News category (general, business, technology, etc.)")
parser.add_argument("--count", type=int, default=5, 
                    help="Number of articles to fetch (1-10)")
parser.add_argument("--country", type=str, default=None,
                    help="Two-letter country code (e.g., us, gb)")
parser.add_argument("--sources", type=str, default=None,
                    help="Comma-separated list of news sources (e.g., bbc-news,cnn)")
parser.add_argument("--query", type=str, default=None,
                    help="Keywords or phrase to search for")
parser.add_argument("--ticker", type=str, default=None,
                    help="Optional stock ticker symbol (e.g., AAPL, GOOGL) to fetch financial data")
parser.add_argument("--page", type=int, default=None,
                    help="Page number for paginated results")
parser.add_argument("--verbose", action="store_true", 
                    help="Enable verbose output")
parser.add_argument("--trace", action="store_true", 
                    help="Enable tracing")
parser.add_argument("--voice", type=str, choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                    default="alloy", help="Voice to use for audio output")
parser.add_argument("--no-audio", action="store_true",
                    help="Disable audio generation")
parser.add_argument("--play-audio", action="store_true",
                    help="Play the generated audio file")
parser.add_argument("--agent", type=str, choices=["planner", "news", "coordinator", "all"], default="coordinator",
                    help="Agent to run (planner, news, coordinator, or all)")
parser.add_argument("--model", type=str, choices=list(MODEL_CONFIG.keys()), default=MODEL_NAME,
                    help="Default model to use for agent execution if specific agent model is not set")
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
parser.add_argument("--temperature", type=float, default=None,
                    help="Temperature setting for model (0.0-1.0)")
parser.add_argument("--output-dir", type=str, default="output",
                    help="Directory to save output files")
parser.add_argument("--save-markdown", action="store_true",
                    help="Save the markdown output to a file")
parser.add_argument("--summary-style", type=str, choices=["formal", "conversational", "brief"],
                    default="conversational", help="Style of the audio summary")
parser.add_argument("--analysis-depth", type=str, choices=["basic", "moderate", "deep"],
                    default="moderate", help="Depth of news analysis")
parser.add_argument("--no-fact-check", action="store_true",
                    help="Disable fact checking")
parser.add_argument("--no-trend-analysis", action="store_true",
                    help="Disable trend analysis")
parser.add_argument("--max-fact-claims", type=int, default=5,
                    help="Maximum number of fact claims to check")
parser.add_argument("--save-analysis", action="store_true",
                    help="Save the analysis as a separate file")
parser.add_argument("--full-report", action="store_true",
                    help="Generate a comprehensive report with all agent outputs")

async def run_planner_agent(args):
    """Run the planner agent."""
    print("\nRunning Planner Agent...")
    
    # Determine the model to use for this agent
    planner_model = args.planner_model if args.planner_model else args.model
    print(f"  (Using model: {planner_model})")

    # Initialize the agent with the specified model
    agent = PlannerAgent(
        verbose=args.verbose,
        model=planner_model,
        temperature=args.temperature
    )
    
    # Prepare input
    categories = [args.category] if args.category != "all" else None
    input_data = PlannerInput(
        count=args.count,
        categories=categories,
        voice=args.voice
    )
    
    # Run the agent
    result = await agent.create_plan(input_data)
    
    # Display the result
    if result.success:
        print("\nPlanning complete!")
        print(f"\nProcessing Plan:")
        print("-" * 60)
        
        for step in result.plan.steps:
            print(f"Step {step.step}: {step.action.capitalize()}")
            print(f"  Parameters: {step.params}")
        
        print("-" * 60)
        
        if result.trace_id:
            print(f"\nTrace ID: {result.trace_id}")
        
        return result
    else:
        print(f"\nPlanning failed: {result.error}")
        return None

async def run_news_agent(args):
    """Run the news agent."""
    print("\nRunning News Agent...")
    
    # Determine the model to use for this agent
    news_model = args.news_model if args.news_model else args.model
    print(f"  (Using model: {news_model})")

    # Initialize the agent with the specified model
    agent = NewsAgent(
        verbose=args.verbose,
        model=news_model,
        temperature=args.temperature
    )
    
    # Prepare input
    input_data = NewsRequest(
        category=args.category,
        count=args.count,
        country=args.country,
        sources=args.sources,
        query=args.query,
        page=args.page,
        voice=args.voice,
        generate_audio=not args.no_audio,
        summary_style=args.summary_style
    )
    
    # Run the agent
    result = await agent.run(input_data)
    
    # Save markdown if requested
    if args.save_markdown and result.markdown:
        try:
            # Set up output directory
            output_dir = args.output_dir
            if not output_dir:
                today = datetime.now().strftime("%Y-%m-%d")
                output_dir = os.path.join("output", today)
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename
            timestamp = int(datetime.now().timestamp())
            markdown_file = os.path.join(output_dir, f"news_summary_{timestamp}.md")
            
            # Write markdown to file
            with open(markdown_file, "w") as f:
                f.write(result.markdown)
            
            print(f"\nMarkdown saved to: {markdown_file}")
        except Exception as e:
            print(f"Error saving markdown: {str(e)}")
    
    # Display the result
    print("\n" + "="*60)
    print(f"NEWS SUMMARY: {args.category.upper()}")
    print("="*60)
    print(f"Articles found: {result.article_count}")
    print("\nSUMMARY:")
    print("-"*60)
    print(result.summary)
    print("-"*60)
    
    print("\nARTICLES:")
    for i, article in enumerate(result.articles, 1):
        print(f"\n{i}. {article.title}")
        print(f"   Source: {article.source}")
        print(f"   URL: {article.url}")
    
    # Display audio information if generated
    if result.audio_file:
        print(f"\nAudio summary generated: {result.audio_file}")
        
        if args.play_audio:
            from src.utils.tts import get_playback_command
            import subprocess
            
            try:
                cmd = get_playback_command(result.audio_file)
                print(f"Playing audio... ({cmd})")
                subprocess.run(cmd, shell=True)
            except Exception as e:
                print(f"Error playing audio: {str(e)}")
    
    # Display traces
    traces = agent.get_traces()
    if traces:
        print(f"\nTrace IDs for debugging:")
        for trace in traces:
            print(f"- {trace['name']}: {trace['trace_id']}")
    
    return result

async def run_coordinator_agent(args):
    """Run the coordinator agent with all specialized agents."""
    print("\nRunning Coordinator with Multi-Agent Team...")
    
    # Coordinator itself uses the main model, but passes overrides down
    coordinator_model = args.model
    print(f"  (Coordinator coordinating with model: {coordinator_model})")

    # Initialize the coordinator agent, passing model overrides
    coordinator = CoordinatorAgent(
        verbose=args.verbose,
        model=coordinator_model, # Base model for coordinator/fallback
        temperature=args.temperature,
        # Pass specific model overrides
        news_model_override=args.news_model,
        analyst_model_override=args.analyst_model,
        factchecker_model_override=args.factchecker_model,
        trend_model_override=args.trend_model,
        writer_model_override=args.writer_model
    )
    
    # Prepare input
    input_data = CoordinatorInput(
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
        max_fact_claims=args.max_fact_claims
    )
    
    # Run the coordinator
    result = await coordinator.run(input_data)
    
    # Save markdown if requested
    if args.save_markdown and result.markdown:
        try:
            # Set up output directory
            today = datetime.now().strftime("%Y-%m-%d")
            output_dir = os.path.join(args.output_dir, today)
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename
            timestamp = int(datetime.now().timestamp())
            markdown_file = os.path.join(output_dir, f"news_summary_{timestamp}.md")
            
            # Write markdown to file
            with open(markdown_file, "w") as f:
                f.write(result.markdown)
            
            print(f"\nMarkdown saved to: {markdown_file}")
        except Exception as e:
            print(f"Error saving markdown: {str(e)}")
    
    # Save analysis if requested
    if args.save_analysis and result.analysis:
        try:
            # Set up output directory
            today = datetime.now().strftime("%Y-%m-%d")
            output_dir = os.path.join(args.output_dir, today)
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename
            timestamp = int(datetime.now().timestamp())
            analysis_file = os.path.join(output_dir, f"news_analysis_{timestamp}.md")
            
            # Prepare analysis content
            analysis_content = f"""# News Analysis: {args.category.upper()}

## Insights
{result.analysis}

"""
            if result.fact_check:
                analysis_content += f"""## Fact Check
{result.fact_check}

"""
            
            if result.trends:
                analysis_content += f"""## Trends
{result.trends}

"""
            
            # Write analysis to file
            with open(analysis_file, "w") as f:
                f.write(analysis_content)
            
            print(f"\nAnalysis saved to: {analysis_file}")
        except Exception as e:
            print(f"Error saving analysis: {str(e)}")
    
    # Generate full report if requested
    if args.full_report:
        try:
            # Set up output directory
            today = datetime.now().strftime("%Y-%m-%d")
            output_dir = os.path.join(args.output_dir, today)
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename
            timestamp = int(datetime.now().timestamp())
            report_file = os.path.join(output_dir, f"full_report_{timestamp}.md")
            
            # Prepare report content
            report_content = f"""# Full News Report: {args.category.upper()}

## Summary
{result.news_summary}

"""
            if result.analysis:
                report_content += f"""## Analysis
{result.analysis}

"""
            
            if result.fact_check:
                report_content += f"""## Fact Check
{result.fact_check}

"""
            
            if result.trends:
                report_content += f"""## Trends
{result.trends}

"""
            
            report_content += f"""## Agent Team Results

"""
            for agent_result in result.agent_results:
                report_content += f"""### {agent_result.agent_name}
Status: {"✓ Success" if agent_result.success else "✗ Failed"}
"""
                if not agent_result.success and agent_result.error:
                    report_content += f"""Error: {agent_result.error}

"""
            
            # Write report to file
            with open(report_file, "w") as f:
                f.write(report_content)
            
            print(f"\nFull report saved to: {report_file}")
        except Exception as e:
            print(f"Error saving full report: {str(e)}")
    
    # Display the result
    print("\n" + "="*60)
    print(f"MULTI-AGENT NEWS REPORT: {args.category.upper()}")
    print("="*60)
    
    # Show summary of agent performance
    print("\nAgent Team Performance:")
    for agent_result in result.agent_results:
        status = "✓" if agent_result.success else "✗"
        print(f"{status} {agent_result.agent_name}")
    
    print("\nSUMMARY:")
    print("-"*60)
    print(result.news_summary)
    print("-"*60)
    
    # Show analysis if available
    if result.analysis:
        print("\nANALYSIS:")
        print("-"*60)
        print(result.analysis)
        print("-"*60)
    
    # Show fact check if available
    if result.fact_check:
        print("\nFACT CHECK:")
        print("-"*60)
        print(result.fact_check)
        print("-"*60)
    
    # Show trends if available
    if result.trends:
        print("\nTRENDS:")
        print("-"*60)
        print(result.trends)
        print("-"*60)
    
    # Print financial data if available
    if result.financial_data:
        print("\n" + "="*60)
        print(f"FINANCIAL DATA: {result.financial_data.get('symbol', 'N/A').upper()}")
        print("="*60)
        # Pretty print the JSON data
        print(json.dumps(result.financial_data, indent=2))
        print("-"*60)
    
    # Display audio information if generated
    if result.audio_file:
        print(f"\nAudio summary generated: {result.audio_file}")
        
        if args.play_audio:
            from src.utils.tts import get_playback_command
            import subprocess
            
            try:
                cmd = get_playback_command(result.audio_file)
                print(f"Playing audio... ({cmd})")
                subprocess.run(cmd, shell=True)
            except Exception as e:
                print(f"Error playing audio: {str(e)}")
    
    # Print trace information if available
    if traces:
        print("\nTrace Information:")
        for trace in traces:
            print(f"- {trace['name']}: {trace['trace_id']}")
    
    # Print specific model overrides if set
    overrides = {
        "NewsAgent": args.news_model,
        "PlannerAgent": args.planner_model,
        "AnalystAgent": args.analyst_model,
        "FactCheckerAgent": args.factchecker_model,
        "TrendAgent": args.trend_model,
        "WriterAgent": args.writer_model,
    }
    active_overrides = {name: model for name, model in overrides.items() if model}
    if active_overrides:
        print("Model Overrides:")
        for name, model in active_overrides.items():
            print(f"  - {name}: {model}")
    
    return result

async def run_all_agents(args):
    """Run planner, coordinator, and news agents in sequence."""
    # Run the planner agent first
    plan_result = await run_planner_agent(args)
    
    if not plan_result or not plan_result.success:
        print("Cannot proceed with other agents due to planning failure.")
        return
    
    # Extract parameters from the plan
    for step in plan_result.plan.steps:
        if step.action in ["fetch", "fetch_news", "initial"]:
            # Update count if provided in the plan
            if "count" in step.params:
                args.count = step.params["count"]
            
            # Update category if provided in the plan
            if "category" in step.params:
                args.category = step.params["category"]
            elif "categories" in step.params and step.params["categories"]:
                # Use the first category if a list is provided
                categories = step.params["categories"]
                if isinstance(categories, list) and categories:
                    args.category = categories[0]
            break
    
    # Run the coordinator agent
    await run_coordinator_agent(args)

async def main():
    """Run the multi-agent news processing system."""
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
    
    model_info = MODEL_CONFIG.get(args.model, {"name": args.model})
    model_display_name = model_info.get("name", args.model)
    
    print(f"\nAgentToast Multi-Agent System")
    print(f"============================")
    print(f"Agent mode: {args.agent}")
    print(f"Category: {args.category}")
    print(f"Article count: {args.count}")
    if args.country:
        print(f"Country: {args.country}")
    if args.sources:
        print(f"Sources: {args.sources}")
    if args.query:
        print(f"Query: {args.query}")
    if args.ticker:
        print(f"Ticker: {args.ticker}")
    if args.page:
        print(f"Page: {args.page}")
    print(f"Voice: {args.voice}")
    print(f"Generate audio: {'yes' if not args.no_audio else 'no'}")
    if args.play_audio:
        print(f"Play audio: yes")
    print(f"Default Model: {model_display_name}")
    if args.temperature is not None:
        print(f"Temperature: {args.temperature}")
    
    # Print specific model overrides if set
    overrides = {
        "NewsAgent": args.news_model,
        "PlannerAgent": args.planner_model,
        "AnalystAgent": args.analyst_model,
        "FactCheckerAgent": args.factchecker_model,
        "TrendAgent": args.trend_model,
        "WriterAgent": args.writer_model,
    }
    active_overrides = {name: model for name, model in overrides.items() if model}
    if active_overrides:
        print("Model Overrides:")
        for name, model in active_overrides.items():
            print(f"  - {name}: {model}")
    
    # Analysis options
    if args.agent == "coordinator" or args.agent == "all":
        print(f"Analysis depth: {args.analysis_depth}")
        print(f"Fact checking: {'disabled' if args.no_fact_check else 'enabled'}")
        print(f"Trend analysis: {'disabled' if args.no_trend_analysis else 'enabled'}")
    
    print(f"Verbose mode: {'enabled' if args.verbose else 'disabled'}")
    print(f"Tracing: {'enabled' if ENABLE_TRACING or args.trace else 'disabled'}")
    print(f"Save markdown: {'yes' if args.save_markdown else 'no'}")
    print(f"Save analysis: {'yes' if args.save_analysis else 'no'}")
    print(f"Full report: {'yes' if args.full_report else 'no'}")
    
    try:
        # Run the selected agent(s)
        if args.agent == "planner":
            await run_planner_agent(args)
        elif args.agent == "news":
            await run_news_agent(args)
        elif args.agent == "coordinator":
            await run_coordinator_agent(args)
        else:  # args.agent == "all"
            await run_all_agents(args)
            
        print("\nAll processing complete!")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run the main async function
    asyncio.run(main()) 
