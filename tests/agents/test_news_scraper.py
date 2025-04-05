"""Tests for NewsScraperAgent."""
import pytest
from unittest.mock import MagicMock, patch

from agenttoast.agents.news_scraper import NewsScraperAgent, Article


@pytest.fixture
def news_scraper():
    """Create a NewsScraperAgent instance for testing."""
    agent = NewsScraperAgent()
    agent.news_api.get_everything = MagicMock()
    return agent


@pytest.mark.asyncio
async def test_scrape_from_newsapi_success(news_scraper, mock_news_api):
    """Test successful news scraping from NewsAPI."""
    # Setup
    news_scraper.news_api.get_everything.return_value = mock_news_api
    
    # Execute
    articles = await news_scraper.scrape_from_newsapi()
    
    # Assert
    assert len(articles) == 2
    assert isinstance(articles[0], Article)
    assert articles[0].title == 'Test Article 1'
    assert articles[0].source == 'Test Source'
    assert articles[0].url == 'http://test.com/1'
    assert articles[0].content == 'Test content 1'


@pytest.mark.asyncio
async def test_scrape_from_newsapi_error(news_scraper):
    """Test error handling in news scraping."""
    # Setup
    news_scraper.news_api.get_everything.side_effect = Exception("API Error")
    
    # Execute
    articles = await news_scraper.scrape_from_newsapi()
    
    # Assert
    assert articles == []


@pytest.mark.asyncio
async def test_run_with_user_preferences(news_scraper, mock_news_api):
    """Test news scraping with user preferences filtering."""
    # Setup
    news_scraper.news_api.get_everything.return_value = mock_news_api
    user_preferences = {
        'categories': ['technology'],
        'sources': ['Test Source']
    }
    
    # Execute
    articles = await news_scraper.run(user_preferences)
    
    # Assert
    assert len(articles) > 0
    for article in articles:
        assert (article.category in user_preferences['categories'] or
                article.source in user_preferences['sources'])


@pytest.mark.asyncio
async def test_run_without_preferences(news_scraper, mock_news_api):
    """Test news scraping without user preferences."""
    # Setup
    news_scraper.news_api.get_everything.return_value = mock_news_api
    
    # Execute
    articles = await news_scraper.run()
    
    # Assert
    assert len(articles) == 2
    assert all(isinstance(article, Article) for article in articles) 