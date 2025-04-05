"""Summarizer agent for generating article summaries."""
from typing import Dict, List, Optional

import openai
from pydantic import BaseModel

from ..core.config import get_settings
from ..core.logger import logger
from .news_scraper import Article
from ..core.agent import Agent

settings = get_settings()


class Summary(BaseModel):
    """Summary data model."""
    title: str
    source: str
    summary: str
    original_url: str
    category: str


class SummarizerAgent(Agent):
    """Agent for generating article summaries."""

    def __init__(self):
        super().__init__()
        self.client = openai.OpenAI(
            api_key=settings.openai_api_key,
            organization=settings.openai_org_id
        )

    async def summarize_article(self, article: Article) -> Summary:
        """Generate a summary for a single article.
        
        Args:
            article: Article to summarize
        
        Returns:
            Summary: Generated summary
        """
        try:
            # Create a system message for consistent summarization
            system_message = """You are an expert news editor. Your task is to create 
            clear, concise, and engaging summaries of news articles. Focus on the key 
            points and maintain a neutral tone. The summary should be 2-3 sentences long."""
            
            # Generate summary using OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Title: {article.title}\n\nContent: {article.content}"}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            summary_text = response.choices[0].message.content.strip()
            
            return Summary(
                title=article.title,
                source=article.source,
                summary=summary_text,
                original_url=article.url,
                category=article.category
            )
        
        except Exception as e:
            logger.error(f"Error summarizing article: {str(e)}")
            return None

    async def run(self, articles: List[Article]) -> List[Summary]:
        """Run the summarization agent.
        
        Args:
            articles: List of articles to summarize
        
        Returns:
            List[Summary]: List of generated summaries
        """
        logger.info(f"Starting summarization of {len(articles)} articles")
        
        summaries = []
        for article in articles:
            summary = await self.summarize_article(article)
            if summary:
                summaries.append(summary)
        
        logger.info(f"Finished generating {len(summaries)} summaries")
        return summaries 