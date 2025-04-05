"""Tests for worker tasks."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from agenttoast.tasks.workers import (
    scrape_news,
    generate_digests,
    process_user_digest,
    retry_failed_delivery,
    cleanup_old_files,
    reset_usage_stats
)
from agenttoast.db.models import Article, Summary

@pytest.fixture
def mock_news_scraper():
    """Fixture for mocked NewsScraperAgent."""
    scraper = MagicMock()
    scraper.run.return_value = [
        Article(
            title="Test Article 1",
            source="Test Source",
            url="http://test.com/1",
            content="Test content 1",
            category="technology",
            published_at="2024-02-20T12:00:00Z"
        ),
        Article(
            title="Test Article 2",
            source="Test Source",
            url="http://test.com/2",
            content="Test content 2",
            category="business",
            published_at="2024-02-20T13:00:00Z"
        )
    ]
    return scraper

@pytest.fixture
def mock_summarizer():
    """Fixture for mocked SummarizerAgent."""
    summarizer = MagicMock()
    summarizer.run.return_value = [
        Summary(
            article=Article(
                title="Test Article 1",
                source="Test Source",
                url="http://test.com/1",
                content="Test content 1",
                category="technology",
                published_at="2024-02-20T12:00:00Z"
            ),
            content="Test summary 1",
            tokens=50,
            cost=0.001
        )
    ]
    return summarizer

@pytest.fixture
def mock_audio_generator():
    """Fixture for mocked AudioGeneratorAgent."""
    generator = MagicMock()
    generator.run.return_value = [Path("/test/audio1.mp3")]
    return generator

@pytest.mark.asyncio
async def test_scrape_news_success(mock_news_scraper, mock_user, mock_safety_manager):
    """Test successful news scraping."""
    with patch("agenttoast.tasks.workers.NewsScraperAgent", return_value=mock_news_scraper):
        articles = await scrape_news(mock_user.id)
        
        assert len(articles) == 2
        assert all(isinstance(article, Article) for article in articles)
        mock_news_scraper.run.assert_called_once()

@pytest.mark.asyncio
async def test_scrape_news_with_safety_limits(mock_news_scraper, mock_user, mock_safety_manager):
    """Test news scraping with safety limits."""
    # Set up safety manager to deny API access
    mock_safety_manager.check_api_limit.return_value = False
    
    with patch("agenttoast.tasks.workers.NewsScraperAgent", return_value=mock_news_scraper):
        articles = await scrape_news(mock_user.id)
        
        assert len(articles) == 0
        mock_news_scraper.run.assert_not_called()

@pytest.mark.asyncio
async def test_generate_digests_success(
    mock_summarizer,
    mock_audio_generator,
    mock_user,
    mock_safety_manager
):
    """Test successful digest generation."""
    articles = [
        Article(
            title="Test Article",
            source="Test Source",
            url="http://test.com",
            content="Test content",
            category="technology",
            published_at="2024-02-20T12:00:00Z"
        )
    ]
    
    with (
        patch("agenttoast.tasks.workers.SummarizerAgent", return_value=mock_summarizer),
        patch("agenttoast.tasks.workers.AudioGeneratorAgent", return_value=mock_audio_generator)
    ):
        summaries, audio_paths = await generate_digests(articles, mock_user.id)
        
        assert len(summaries) == 1
        assert len(audio_paths) == 1
        assert isinstance(summaries[0], Summary)
        assert isinstance(audio_paths[0], Path)

@pytest.mark.asyncio
async def test_generate_digests_with_safety_limits(
    mock_summarizer,
    mock_audio_generator,
    mock_user,
    mock_safety_manager
):
    """Test digest generation with safety limits."""
    articles = [
        Article(
            title="Test Article",
            source="Test Source",
            url="http://test.com",
            content="Test content",
            category="technology",
            published_at="2024-02-20T12:00:00Z"
        )
    ]
    
    # Set up safety manager to deny cost limit
    mock_safety_manager.check_cost_limit.return_value = False
    
    with (
        patch("agenttoast.tasks.workers.SummarizerAgent", return_value=mock_summarizer),
        patch("agenttoast.tasks.workers.AudioGeneratorAgent", return_value=mock_audio_generator)
    ):
        summaries, audio_paths = await generate_digests(articles, mock_user.id)
        
        assert len(summaries) == 0
        assert len(audio_paths) == 0
        mock_summarizer.run.assert_not_called()
        mock_audio_generator.run.assert_not_called()

@pytest.mark.asyncio
async def test_process_user_digest_success(
    mock_news_scraper,
    mock_summarizer,
    mock_audio_generator,
    mock_user,
    mock_safety_manager
):
    """Test successful user digest processing."""
    with (
        patch("agenttoast.tasks.workers.NewsScraperAgent", return_value=mock_news_scraper),
        patch("agenttoast.tasks.workers.SummarizerAgent", return_value=mock_summarizer),
        patch("agenttoast.tasks.workers.AudioGeneratorAgent", return_value=mock_audio_generator)
    ):
        result = await process_user_digest(mock_user.id)
        assert result is True

@pytest.mark.asyncio
async def test_retry_failed_delivery(mock_user):
    """Test retrying failed delivery."""
    delivery_info = {
        "user_id": mock_user.id,
        "summaries": [
            {
                "article": {
                    "title": "Test Article",
                    "source": "Test Source",
                    "url": "http://test.com",
                    "content": "Test content",
                    "category": "technology",
                    "published_at": "2024-02-20T12:00:00Z"
                },
                "content": "Test summary",
                "tokens": 50,
                "cost": 0.001
            }
        ],
        "audio_paths": ["/test/audio1.mp3"]
    }
    
    result = await retry_failed_delivery(delivery_info)
    assert result is True

@pytest.mark.asyncio
async def test_cleanup_old_files_success(mock_safety_manager, mock_settings):
    """Test successful cleanup of old files."""
    await cleanup_old_files()
    mock_safety_manager.cleanup_old_files.assert_called()

@pytest.mark.asyncio
async def test_reset_usage_stats_success(mock_safety_manager):
    """Test successful reset of usage stats."""
    await reset_usage_stats()
    mock_safety_manager.load_or_create_stats.assert_called() 