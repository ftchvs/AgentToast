"""Content filtering agent for ensuring quality and relevance of articles."""
from typing import Dict, List, Optional
from datetime import datetime

import openai
from pydantic import BaseModel
import nltk
from nltk.tokenize import sent_tokenize
from textblob import TextBlob
from difflib import SequenceMatcher

from ..core.config import get_settings
from ..core.logger import logger
from .news_scraper import Article
from ..core.agent import Agent

settings = get_settings()

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class ContentQuality(BaseModel):
    """Content quality assessment model."""
    is_duplicate: bool = False
    duplicate_score: float = 0.0
    sentiment_score: float = 0.0
    bias_score: float = 0.0
    nsfw_probability: float = 0.0
    category_confidence: float = 0.0
    quality_score: float = 0.0

class ContentFilterAgent(Agent):
    """Agent for filtering and assessing content quality."""

    def __init__(self):
        super().__init__()
        self.client = openai.OpenAI(
            api_key=settings.openai_api_key,
            organization=settings.openai_org_id
        )

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        return SequenceMatcher(None, text1, text2).ratio()

    def check_duplicates(self, article: Article, existing_articles: List[Article]) -> tuple[bool, float]:
        """Check if article is duplicate of existing ones."""
        if not existing_articles:
            return False, 0.0

        max_similarity = 0.0
        for existing in existing_articles:
            similarity = self._calculate_similarity(
                article.title + article.content,
                existing.title + existing.content
            )
            max_similarity = max(max_similarity, similarity)
            if max_similarity > settings.duplicate_threshold:
                return True, max_similarity

        return False, max_similarity

    async def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text using TextBlob."""
        blob = TextBlob(text)
        # Returns value between -1 (negative) and 1 (positive)
        return blob.sentiment.polarity

    async def check_nsfw_content(self, text: str) -> float:
        """Check for NSFW content using OpenAI's moderation endpoint."""
        try:
            response = self.client.moderations.create(input=text)
            # Get the highest category score for NSFW content
            nsfw_categories = ['sexual', 'violence', 'hate', 'self-harm']
            scores = [
                response.results[0].category_scores.get(cat, 0.0)
                for cat in nsfw_categories
            ]
            return max(scores)
        except Exception as e:
            logger.error(f"Error checking NSFW content: {str(e)}")
            return 0.0

    async def verify_category(self, article: Article) -> float:
        """Verify article category using OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a news categorization expert. Given an article, determine if it matches the provided category. Return a confidence score between 0 and 1."
                    },
                    {
                        "role": "user",
                        "content": f"Article Title: {article.title}\nContent: {article.content}\nCategory: {article.category}"
                    }
                ],
                max_tokens=50,
                temperature=0.2
            )
            
            # Extract confidence score from response
            try:
                score = float(response.choices[0].message.content.strip())
                return min(max(score, 0.0), 1.0)  # Ensure score is between 0 and 1
            except ValueError:
                return 0.5  # Default to neutral if parsing fails
            
        except Exception as e:
            logger.error(f"Error verifying category: {str(e)}")
            return 0.5

    async def analyze_bias(self, text: str) -> float:
        """Analyze potential bias in content using OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a media bias expert. Analyze the text for potential bias and return a score between 0 (neutral) and 1 (highly biased)."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                max_tokens=50,
                temperature=0.2
            )
            
            try:
                score = float(response.choices[0].message.content.strip())
                return min(max(score, 0.0), 1.0)
            except ValueError:
                return 0.5
            
        except Exception as e:
            logger.error(f"Error analyzing bias: {str(e)}")
            return 0.5

    def calculate_quality_score(self, quality: ContentQuality) -> float:
        """Calculate overall quality score."""
        weights = {
            'duplicate': -1.0,
            'sentiment': 0.2,
            'bias': -0.3,
            'nsfw': -0.8,
            'category': 0.4
        }
        
        score = 1.0  # Start with perfect score
        if quality.is_duplicate:
            score += weights['duplicate'] * quality.duplicate_score
        score += weights['sentiment'] * abs(quality.sentiment_score)  # Use absolute value for sentiment
        score += weights['bias'] * quality.bias_score
        score += weights['nsfw'] * quality.nsfw_probability
        score += weights['category'] * quality.category_confidence
        
        return max(min(score, 1.0), 0.0)  # Ensure score is between 0 and 1

    async def assess_article(self, article: Article, existing_articles: List[Article]) -> ContentQuality:
        """Assess article quality and generate quality metrics."""
        # Check for duplicates
        is_duplicate, duplicate_score = self.check_duplicates(article, existing_articles)
        
        # Run various quality checks
        sentiment_score = await self.analyze_sentiment(article.content)
        nsfw_prob = await self.check_nsfw_content(article.content)
        category_conf = await self.verify_category(article)
        bias_score = await self.analyze_bias(article.content)
        
        quality = ContentQuality(
            is_duplicate=is_duplicate,
            duplicate_score=duplicate_score,
            sentiment_score=sentiment_score,
            bias_score=bias_score,
            nsfw_probability=nsfw_prob,
            category_confidence=category_conf
        )
        
        # Calculate overall quality score
        quality.quality_score = self.calculate_quality_score(quality)
        
        return quality

    async def run(self, articles: List[Article], min_quality_score: float = 0.6) -> List[Article]:
        """Run the content filter agent.
        
        Args:
            articles: List of articles to filter
            min_quality_score: Minimum quality score required (0-1)
        
        Returns:
            List[Article]: Filtered list of articles
        """
        logger.info(f"Starting content filtering for {len(articles)} articles")
        
        filtered_articles = []
        existing_articles = []  # Keep track of processed articles for duplicate detection
        
        for article in articles:
            quality = await self.assess_article(article, existing_articles)
            
            if quality.quality_score >= min_quality_score:
                filtered_articles.append(article)
                existing_articles.append(article)
                
                logger.info(
                    f"Article passed quality check",
                    extra={
                        "title": article.title,
                        "quality_score": quality.quality_score,
                        "metrics": quality.model_dump()
                    }
                )
            else:
                logger.warning(
                    f"Article failed quality check",
                    extra={
                        "title": article.title,
                        "quality_score": quality.quality_score,
                        "metrics": quality.model_dump()
                    }
                )
        
        logger.info(
            f"Finished content filtering",
            extra={
                "input_articles": len(articles),
                "filtered_articles": len(filtered_articles)
            }
        )
        
        return filtered_articles 