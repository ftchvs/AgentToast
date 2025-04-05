from typing import List, Dict, Any
from openai.lib import pydantic_function_tool
from pydantic import BaseModel, Field, ConfigDict
from src.agents.base_agent import BaseAgent
import logging
import os
from newsapi import NewsApiClient

class NewsParams(BaseModel):
    model_config = ConfigDict(extra='forbid')
    category: str = Field(
        description="News category to fetch",
        pattern="^(business|entertainment|general|health|science|sports|technology)$"
    )
    count: int = Field(
        description="Number of articles to fetch",
        ge=1,
        le=10,
        default=5
    )

class Article(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: str = Field(description="Article title")
    description: str = Field(description="Article description")
    url: str = Field(description="Article URL")
    source: str = Field(description="Article source")

class FetchResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    articles: List[Article] = Field(description="List of fetched articles")
    category: str = Field(description="Category of fetched articles")
    total_found: int = Field(description="Total number of articles found")

class FetcherAgent(BaseAgent):
    """Agent responsible for fetching news articles."""
    
    def __init__(self):
        """Initialize the FetcherAgent."""
        # Create the fetch_news function tool
        self.fetch_news_tool = pydantic_function_tool(
            model=NewsParams,
            name="fetch_news",
            description="Fetch news articles from a specific category"
        )
        
        super().__init__(
            name="News Fetcher",
            instructions="""I am a fetcher agent that retrieves news articles from various sources.
            I ensure articles are properly formatted and contain all required information.""",
            tools=[self.fetch_news_tool]
        )
        
        # Initialize NewsAPI client
        api_key = os.getenv('NEWS_API_KEY')
        if not api_key:
            raise ValueError("NEWS_API_KEY environment variable is required")
        self.news_client = NewsApiClient(api_key=api_key)

    async def fetch_news(self, params: NewsParams) -> FetchResult:
        """
        Fetch news articles from a specific category.
        
        Args:
            params: Parameters containing:
                - category: News category to fetch from
                - count: Number of articles to fetch
            
        Returns:
            FetchResult containing:
            - articles: List of fetched articles
            - category: Category of fetched articles
            - total_found: Total number of articles found
        """
        try:
            logging.info(f"Fetching {params.count} articles from category: {params.category}")
            
            # Fetch articles from NewsAPI
            response = self.news_client.get_top_headlines(
                category=params.category,
                language='en',
                page_size=params.count
            )
            
            # Process and validate articles
            articles = []
            for article_data in response.get('articles', []):
                if all(article_data.get(field) for field in ['title', 'description', 'url']):
                    article = Article(
                        title=article_data['title'],
                        description=article_data['description'],
                        url=article_data['url'],
                        source=article_data['source']['name'] if article_data.get('source') else 'Unknown'
                    )
                    articles.append(article)
                
                if len(articles) >= params.count:
                    break
            
            result = FetchResult(
                articles=articles,
                category=params.category,
                total_found=response.get('totalResults', 0)
            )
            
            logging.info(f"Fetched {len(articles)} articles successfully")
            return result
            
        except Exception as e:
            logging.error(f"Error fetching news: {str(e)}")
            raise

    async def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a news fetching task."""
        try:
            params = NewsParams(
                category=task.get('category', 'general'),
                count=task.get('count', 5)
            )
            result = await self.fetch_news(params)
            return {
                'success': True,
                **result.model_dump()
            }
        except Exception as e:
            logging.error(f"Error executing task: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        
    def plan_and_act(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Plan and execute news fetching task.
        
        Args:
            task: Dictionary containing task parameters like count and categories
            
        Returns:
            Dictionary containing fetched articles
        """
        count = task.get('count', 5)
        categories = task.get('categories', None)
        
        articles = self.fetch_top_news(count, categories)
        return {'articles': articles}
        
    def fetch_top_news(self, count: int = 5, categories: List[str] = None) -> List[Dict[str, Any]]:
        """Fetch top news articles from NEWS API.
        
        Args:
            count: Number of articles to fetch (default: 5)
            categories: List of categories to filter by (default: None)
            
        Returns:
            List of news articles
        """
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        try:
            params = {
                'language': 'en',
                'page_size': count
            }
            
            if categories and len(categories) == 1:
                params['category'] = categories[0]  # NewsAPI only accepts a single category
                
            top_headlines = self.news_client.get_top_headlines(**params)
            
            if not top_headlines['articles']:
                raise ValueError("No articles found")
                
            return top_headlines['articles']
            
        except Exception as e:
            print(f"Error fetching news: {str(e)}")
            return [] 