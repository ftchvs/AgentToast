"""Tests for SummarizerAgent."""
import pytest
from unittest.mock import MagicMock, patch

from agenttoast.agents.summarizer import SummarizerAgent, Summary
from agenttoast.agents.news_scraper import Article


@pytest.fixture
def summarizer():
    """Create a SummarizerAgent instance for testing."""
    agent = SummarizerAgent()
    agent.client.chat.completions.create = MagicMock()
    return agent


@pytest.fixture
def test_article():
    """Create a test article."""
    return Article(
        title="Test Article",
        source="Test Source",
        url="http://test.com/article",
        content="This is a test article content for summarization.",
        category="technology",
        published_at="2024-03-14T12:00:00Z"
    )


@pytest.mark.asyncio
async def test_summarize_article_success(summarizer, test_article, mock_openai_response):
    """Test successful article summarization."""
    # Setup
    summarizer.client.chat.completions.create.return_value = mock_openai_response
    
    # Execute
    summary = await summarizer.summarize_article(test_article)
    
    # Assert
    assert isinstance(summary, Summary)
    assert summary.title == test_article.title
    assert summary.source == test_article.source
    assert summary.original_url == test_article.url
    assert summary.category == test_article.category
    assert summary.summary == "This is a test summary."


@pytest.mark.asyncio
async def test_summarize_article_error(summarizer, test_article):
    """Test error handling in article summarization."""
    # Setup
    summarizer.client.chat.completions.create.side_effect = Exception("API Error")
    
    # Execute
    summary = await summarizer.summarize_article(test_article)
    
    # Assert
    assert summary is None


@pytest.mark.asyncio
async def test_run_with_multiple_articles(summarizer, test_article, mock_openai_response):
    """Test summarization of multiple articles."""
    # Setup
    summarizer.client.chat.completions.create.return_value = mock_openai_response
    articles = [test_article, test_article]  # Two test articles
    
    # Execute
    summaries = await summarizer.run(articles)
    
    # Assert
    assert len(summaries) == 2
    assert all(isinstance(summary, Summary) for summary in summaries)
    assert all(summary.summary == "This is a test summary." for summary in summaries)


@pytest.mark.asyncio
async def test_run_with_empty_list(summarizer):
    """Test summarization with empty article list."""
    # Execute
    summaries = await summarizer.run([])
    
    # Assert
    assert len(summaries) == 0


@pytest.mark.asyncio
async def test_run_with_partial_failures(summarizer, test_article, mock_openai_response):
    """Test summarization with some articles failing."""
    # Setup
    articles = [test_article, test_article, test_article]  # Three test articles
    
    # Make second article fail
    def mock_create(*args, **kwargs):
        if summarizer.client.chat.completions.create.call_count == 2:
            raise Exception("API Error")
        return mock_openai_response
    
    summarizer.client.chat.completions.create.side_effect = mock_create
    
    # Execute
    summaries = await summarizer.run(articles)
    
    # Assert
    assert len(summaries) == 2  # Should have two successful summaries
    assert all(isinstance(summary, Summary) for summary in summaries) 