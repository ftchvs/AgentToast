"""News scraping agent for collecting articles from various sources."""
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import openai
from newsapi import NewsApiClient
from pydantic import BaseModel

from ..core.config import get_settings
from ..core.logger import logger
from ..core.agent import Agent

settings = get_settings()


class NewsSource(BaseModel):
    """News source configuration."""
    name: str
    url: str
    category: str


class Article(BaseModel):
    """Article data model."""
    title: str
    source: str
    url: str
    content: str
    category: str
    published_at: str


class NewsScraperAgent(Agent):
    """Agent for scraping news from configured sources."""

    def __init__(self):
        super().__init__()
        self.news_api = NewsApiClient(api_key=settings.news_api_key)
        self.sources = [
            NewsSource(
                name="TechCrunch",
                url="techcrunch.com",
                category="technology"
            ),
            NewsSource(
                name="Reuters",
                url="reuters.com",
                category="general"
            ),
            NewsSource(
                name="BBC News",
                url="bbc.co.uk",
                category="general"
            ),
        ]

    async def scrape_from_newsapi(self) -> List[Article]:
        """Fetch articles from NewsAPI."""
        try:
            articles = []
            for source in self.sources:
                response = self.news_api.get_everything(
                    domains=source.url,
                    language='en',
                    sort_by='publishedAt',
                    page_size=5
                )
                
                for article in response['articles']:
                    articles.append(
                        Article(
                            title=article['title'],
                            source=article['source']['name'],
                            url=article['url'],
                            content=article['content'] or article['description'],
                            category=source.category,
                            published_at=article['publishedAt']
                        )
                    )
            
            logger.info(f"Fetched {len(articles)} articles from NewsAPI")
            return articles
        
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {str(e)}")
            return []

    async def run(self, user_preferences: Dict = None) -> List[Article]:
        """Run the news scraping agent.
        
        Args:
            user_preferences: Optional user preferences for filtering articles
        
        Returns:
            List[Article]: List of scraped articles
        """
        logger.info("Starting news scraping")
        
        # Fetch articles from NewsAPI
        articles = await self.scrape_from_newsapi()
        
        # Filter by user preferences if provided
        if user_preferences:
            filtered_articles = []
            for article in articles:
                if (
                    article.category in user_preferences.get('categories', [])
                    or article.source in user_preferences.get('sources', [])
                ):
                    filtered_articles.append(article)
            articles = filtered_articles
        
        logger.info(f"Finished scraping {len(articles)} articles")
        return articles 