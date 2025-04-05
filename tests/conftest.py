"""Common test fixtures for AgentToast."""
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile
import json
from dotenv import load_dotenv
from typing import Dict, List

from agenttoast.core.config import get_settings, Settings
from agenttoast.core.user import UserManager, UserPreferences
from agenttoast.core.safety import SafetyManager
from agenttoast.agents.news_scraper import NewsScraperAgent, Article
from agenttoast.agents.summarizer import SummarizerAgent
from agenttoast.agents.audio_generator import AudioGeneratorAgent
from agenttoast.core.logger import logger
from agenttoast.agents.analytics import AnalyticsAgent
from agenttoast.agents.content_filter import ContentFilterAgent
from agenttoast.agents.delivery import DeliveryAgent
from agenttoast.agents.language_processor import LanguageProcessingAgent


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables before running tests."""
    load_dotenv()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def mock_settings(temp_dir):
    """Mock settings for testing."""
    settings = get_settings()
    settings.storage_path = str(temp_dir)
    settings.audio_path = str(temp_dir / "audio")
    settings.summaries_path = str(temp_dir / "summaries")
    settings.config_path = str(temp_dir / "config")
    
    # Create necessary directories
    os.makedirs(settings.audio_path, exist_ok=True)
    os.makedirs(settings.summaries_path, exist_ok=True)
    os.makedirs(settings.config_path, exist_ok=True)
    
    return settings


@pytest.fixture
def mock_safety_manager(mock_settings):
    """Mock SafetyManager for testing."""
    safety_manager = SafetyManager(Path(mock_settings.config_path))
    return safety_manager


@pytest.fixture
def mock_news_api():
    """Mock NewsAPI responses."""
    return {
        'articles': [
            {
                'title': 'Test Article 1',
                'source': {'name': 'Test Source'},
                'url': 'http://test.com/1',
                'content': 'Test content 1',
                'description': 'Test description 1',
                'publishedAt': '2024-03-14T12:00:00Z'
            },
            {
                'title': 'Test Article 2',
                'source': {'name': 'Test Source'},
                'url': 'http://test.com/2',
                'content': 'Test content 2',
                'description': 'Test description 2',
                'publishedAt': '2024-03-14T13:00:00Z'
            }
        ]
    }


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API responses."""
    class MockResponse:
        def __init__(self, content):
            self.content = content
            self.choices = [
                type('Choice', (), {'message': type('Message', (), {'content': content})})()
            ]
    
    return MockResponse("This is a test summary.")


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    preferences = UserPreferences(
        categories=['technology', 'general'],
        sources=['Test Source'],
        max_stories=5,
        voice_id='alloy'
    )
    
    return {
        'id': 'test_user_1',
        'name': 'Test User',
        'preferences': preferences
    }


@pytest.fixture
def mock_user_manager(mock_user):
    """Mock UserManager for testing."""
    manager = UserManager()
    manager.get_user = MagicMock(return_value=mock_user)
    return manager


@pytest.fixture
def sample_article() -> Dict:
    """Sample article for testing."""
    return {
        "title": "Test Article",
        "description": "This is a test article for unit testing.",
        "content": "This is the full content of the test article. It contains multiple sentences and paragraphs to simulate a real article.",
        "url": "https://example.com/test-article",
        "publishedAt": "2024-03-14T12:00:00Z",
        "source": {"id": "test-source", "name": "Test News"}
    }


@pytest.fixture
def sample_articles() -> List[Dict]:
    """List of sample articles for testing."""
    return [
        {
            "title": "First Test Article",
            "description": "Description of first test article",
            "content": "Content of first test article with multiple sentences.",
            "url": "https://example.com/article1",
            "publishedAt": "2024-03-14T12:00:00Z",
            "source": {"id": "test-source", "name": "Test News"}
        },
        {
            "title": "Second Test Article",
            "description": "Description of second test article",
            "content": "Content of second test article. This one has different content.",
            "url": "https://example.com/article2",
            "publishedAt": "2024-03-14T13:00:00Z",
            "source": {"id": "test-source", "name": "Test News"}
        }
    ]


@pytest.fixture
def test_output_dir(tmp_path) -> str:
    """Create and return a temporary directory for test outputs."""
    output_dir = tmp_path / "test_outputs"
    output_dir.mkdir()
    return str(output_dir) 