"""News API tools for fetching and processing news articles."""

import os
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import requests
from src.config import get_logger

logger = get_logger(__name__)

class FetchNewsInput(BaseModel):
    """Input schema for fetching news articles."""
    
    category: str = Field(
        description="News category (top-headlines, business, entertainment, health, science, sports, technology, general)"
    )
    count: int = Field(default=5, description="Number of articles to fetch (1-10)")
    country: Optional[str] = Field(
        default=None, 
        description="The 2-letter ISO 3166-1 code of the country (e.g., us, gb, au)"
    )
    sources: Optional[str] = Field(
        default=None, 
        description="A comma-separated string of news source IDs (e.g., bbc-news,cnn)"
    )
    query: Optional[str] = Field(
        default=None, 
        description="Keywords or phrase to search for in the news"
    )
    page: Optional[int] = Field(
        default=None, 
        description="Page number for paginated results"
    )
    
class FetchNewsTool:
    """Tool for fetching news articles from the News API."""
    
    def __init__(self):
        """Initialize the news fetching tool."""
        self.api_key = os.getenv("NEWS_API_KEY")
        if not self.api_key:
            logger.warning("NEWS_API_KEY not found in environment variables")
    
    def run(self, input_data: FetchNewsInput) -> List[Dict[str, Any]]:
        """
        Fetch news articles from the specified category.
        
        Args:
            input_data: The input parameters for the news fetch
            
        Returns:
            A list of news articles
        """
        logger.info(f"Fetching {input_data.count} articles from category: {input_data.category}")
        
        if not self.api_key:
            logger.error("Cannot fetch news: NEWS_API_KEY not found")
            return []
            
        # Validate and adjust count
        count = max(1, min(input_data.count, 10))
        
        try:
            # Construct the API request
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "apiKey": self.api_key,
                "pageSize": count,
                "language": "en"
            }
            
            # Handle category - top-headlines is an endpoint, not a category
            is_top_headlines = input_data.category.lower() == "top-headlines"
            
            # Add category parameter if it's a valid category (not top-headlines or all)
            if input_data.category and input_data.category.lower() not in ["all", "top-headlines"]:
                params["category"] = input_data.category
                logger.info(f"Using category parameter: {input_data.category}")
            
            # Handle country parameter
            if input_data.country:
                params["country"] = input_data.country
                logger.info(f"Using country: {input_data.country}")
            elif is_top_headlines and not input_data.sources:
                # Default to US for top headlines if no country specified and no sources
                params["country"] = "us"
                logger.info("No country specified for top-headlines, defaulting to 'us'")
            
            # Handle sources parameter (cannot be used with country or category)
            if input_data.sources:
                params["sources"] = input_data.sources
                logger.info(f"Using sources: {input_data.sources}")
                
                # NewsAPI doesn't allow sources to be used with country or category
                if "country" in params:
                    logger.warning("Removing 'country' parameter - cannot be used with 'sources'")
                    del params["country"]
                if "category" in params:
                    logger.warning("Removing 'category' parameter - cannot be used with 'sources'")
                    del params["category"]
            
            # Handle query parameter
            if input_data.query:
                params["q"] = input_data.query
                logger.info(f"Using search query: {input_data.query}")
            
            # Handle pagination
            if input_data.page and input_data.page > 0:
                params["page"] = input_data.page
                logger.info(f"Using page: {input_data.page}")
            
            # Log the final request parameters
            logger.info(f"API Request: {url} with params: {params}")
            
            # Make the API request
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process and return the articles
            articles = data.get("articles", [])
            total_results = data.get("totalResults", 0)
            logger.info(f"Successfully fetched {len(articles)} articles (total available: {total_results})")
            
            # Format articles for agent consumption
            processed_articles = []
            for article in articles:
                processed_articles.append({
                    "title": article.get("title", "No title"),
                    "description": article.get("description", "No description"),
                    "url": article.get("url", ""),
                    "source": article.get("source", {}).get("name", "Unknown source"),
                    "published_at": article.get("publishedAt", ""),
                    "content": article.get("content", "No content")
                })
                
            return processed_articles
            
        except Exception as e:
            logger.error(f"Error fetching news: {str(e)}")
            return []

# Create the tool instance
fetch_news_tool = FetchNewsTool() 