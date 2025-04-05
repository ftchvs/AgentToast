import pytest
from unittest.mock import Mock, patch
from src.agents.news_agent import NewsAgent

@pytest.fixture
def mock_news_api():
    """Create a mock NEWS API client."""
    return Mock()

@pytest.fixture
def mock_openai():
    """Create a mock OpenAI client."""
    return Mock()

@pytest.fixture
def news_agent(mock_news_api, mock_openai):
    """Create a NewsAgent instance with mock clients."""
    with patch('newsapi.NewsApiClient') as mock_news_api_cls, \
         patch('openai.OpenAI') as mock_openai_cls:
        mock_news_api_cls.return_value = mock_news_api
        mock_openai_cls.return_value = mock_openai
        agent = NewsAgent()
        return agent

def test_fetch_top_news_success(news_agent, mock_news_api):
    """Test successful news fetching."""
    # Mock response data
    mock_articles = {
        'articles': [
            {
                'title': 'Test Article',
                'description': 'Test Description'
            }
        ]
    }
    mock_news_api.get_top_headlines.return_value = mock_articles
    
    # Test the method
    result = news_agent.fetch_top_news(count=1)
    
    assert len(result) == 1
    assert result[0]['title'] == 'Test Article'
    assert result[0]['description'] == 'Test Description'

def test_fetch_top_news_failure(news_agent, mock_news_api):
    """Test news fetching with API error."""
    mock_news_api.get_top_headlines.side_effect = Exception("API Error")
    
    result = news_agent.fetch_top_news()
    assert result == []

def test_generate_summary_success(news_agent, mock_openai):
    """Test successful summary generation."""
    # Mock article data
    article = {
        'title': 'Test Article',
        'description': 'Test Description'
    }
    
    # Mock OpenAI response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Test Summary"
    mock_openai.chat.completions.create.return_value = mock_response
    
    result = news_agent.generate_summary(article)
    assert result == "Test Summary"

def test_generate_audio_success(news_agent, mock_openai):
    """Test successful audio generation."""
    # Mock audio response
    mock_response = Mock()
    mock_response.content = b"Test Audio Data"
    mock_openai.audio.speech.create.return_value = mock_response
    
    result = news_agent.generate_audio("Test text")
    assert result == b"Test Audio Data" 