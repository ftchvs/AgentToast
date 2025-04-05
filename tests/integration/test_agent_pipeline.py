import pytest
import asyncio
from datetime import datetime
from pathlib import Path
import json

from agenttoast.agents.news_scraper import NewsScraperAgent
from agenttoast.agents.content_filter import ContentFilterAgent
from agenttoast.agents.summarizer import SummarizerAgent
from agenttoast.agents.audio_gen import AudioGeneratorAgent
from agenttoast.agents.analytics import AnalyticsAgent
from agenttoast.safety import SafetyManager

@pytest.fixture
async def safety_manager():
    config_path = Path("test_config")
    config_path.mkdir(exist_ok=True)
    manager = SafetyManager(config_path)
    await manager.load_or_create_limits({
        "api_calls_per_day": 100,
        "cost_per_day": 5.0,  # Set $5 limit for testing
        "storage_mb": 100
    })
    return manager

@pytest.fixture
async def agents(safety_manager):
    news_scraper = NewsScraperAgent(safety_manager)
    content_filter = ContentFilterAgent(safety_manager)
    summarizer = SummarizerAgent(safety_manager)
    audio_gen = AudioGeneratorAgent(safety_manager)
    analytics = AnalyticsAgent(safety_manager)
    
    return {
        "news_scraper": news_scraper,
        "content_filter": content_filter,
        "summarizer": summarizer,
        "audio_gen": audio_gen,
        "analytics": analytics
    }

async def save_results(summaries, audio_files):
    """Save summaries and audio files locally."""
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    # Save summaries
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = output_dir / f"summaries_{timestamp}.md"
    
    with open(summary_file, "w") as f:
        for i, summary in enumerate(summaries, 1):
            f.write(f"# Summary {i}\n\n")
            f.write(f"## {summary.title}\n\n")
            f.write(f"{summary.content}\n\n")
            f.write(f"Source: {summary.source_url}\n\n")
            f.write("---\n\n")
    
    # Copy audio files to output directory
    audio_paths = []
    for i, audio_file in enumerate(audio_files, 1):
        dest_path = output_dir / f"audio_{timestamp}_{i}.mp3"
        Path(audio_file).rename(dest_path)
        audio_paths.append(dest_path)
    
    return {
        "summary_file": summary_file,
        "audio_files": audio_paths
    }

async def test_small_pipeline(agents, safety_manager):
    """Run a small test pipeline through all agents."""
    
    # 1. Fetch 2 articles
    articles = await agents["news_scraper"].run(
        query="technology",
        max_articles=2
    )
    assert len(articles) > 0, "Should fetch at least one article"
    
    # 2. Filter content
    filtered_articles = await agents["content_filter"].run(articles)
    assert len(filtered_articles) > 0, "Should have at least one article pass filtering"
    
    # 3. Generate summaries
    summaries = await agents["summarizer"].run(filtered_articles)
    assert len(summaries) > 0, "Should have summaries"
    
    # 4. Generate audio
    audio_files = await agents["audio_gen"].run(summaries)
    assert len(audio_files) > 0, "Should have audio files"
    
    # 5. Save results locally
    saved_files = await save_results(summaries, audio_files)
    print("\nFiles saved:")
    print(f"Summaries: {saved_files['summary_file']}")
    print("Audio files:")
    for audio_file in saved_files['audio_files']:
        print(f"- {audio_file}")
    
    # 6. Collect analytics
    analytics_result = await agents["analytics"].run()
    assert analytics_result, "Should collect analytics"
    
    # Get final usage stats
    usage = await safety_manager.get_current_usage()
    print("\nTest Pipeline Results:")
    print(f"API Calls: {usage['api_calls']}")
    print(f"Total Cost: ${usage['cost']:.2f}")
    print(f"Storage Used: {usage['storage_mb']:.2f}MB")
    
    return usage

if __name__ == "__main__":
    asyncio.run(test_small_pipeline()) 