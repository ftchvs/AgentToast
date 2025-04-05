from typing import List, Dict, Any
from openai.lib import pydantic_function_tool
from pydantic import BaseModel, Field, ConfigDict
from src.agents.base_agent import BaseAgent
from src.agents.fetcher_agent import Article
import logging

class ArticleVerificationParams(BaseModel):
    model_config = ConfigDict(extra='forbid')
    articles: List[Dict[str, Any]] = Field(description="List of articles to verify")
    min_title_length: int = Field(
        description="Minimum required title length",
        ge=10,
        le=200,
        default=20
    )
    min_description_length: int = Field(
        description="Minimum required description length",
        ge=20,
        le=1000,
        default=50
    )

class VerificationResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    total_verified: int = Field(description="Number of articles that passed verification")
    total_rejected: int = Field(description="Number of articles that failed verification")
    verified_articles: List[Article] = Field(description="List of verified articles")
    rejected_articles: List[Article] = Field(description="List of rejected articles")

class VerifierAgent(BaseAgent):
    """Agent responsible for verifying article quality."""
    
    def __init__(self):
        """Initialize the VerifierAgent."""
        # Create the verify_articles function tool
        self.verify_articles_tool = pydantic_function_tool(
            model=ArticleVerificationParams,
            name="verify_articles",
            description="Verify the quality of news articles"
        )
        
        super().__init__(
            name="Article Verifier",
            instructions="""I am a verification agent that checks article quality.
            I ensure articles meet minimum length requirements and contain valid content.""",
            tools=[self.verify_articles_tool]
        )

    async def verify_articles(self, params: ArticleVerificationParams) -> VerificationResult:
        """
        Verify the quality of news articles.
        
        Args:
            params: Parameters containing:
                - articles: List of articles to verify
                - min_title_length: Minimum required title length
                - min_description_length: Minimum required description length
            
        Returns:
            VerificationResult containing:
            - total_verified: Number of articles that passed verification
            - total_rejected: Number of articles that failed verification
            - verified_articles: List of verified articles
            - rejected_articles: List of rejected articles
        """
        try:
            logging.info(f"Verifying {len(params.articles)} articles")
            
            verified_articles = []
            rejected_articles = []
            
            for article_data in params.articles:
                article = Article(**article_data)
                
                # Check title length
                if len(article.title) < params.min_title_length:
                    rejected_articles.append(article)
                    continue
                
                # Check description length
                if len(article.description) < params.min_description_length:
                    rejected_articles.append(article)
                    continue
                
                verified_articles.append(article)
            
            result = VerificationResult(
                total_verified=len(verified_articles),
                total_rejected=len(rejected_articles),
                verified_articles=verified_articles,
                rejected_articles=rejected_articles
            )
            
            logging.info(f"Verification complete: {result.total_verified} passed, {result.total_rejected} rejected")
            return result
            
        except Exception as e:
            logging.error(f"Error verifying articles: {str(e)}")
            raise

    async def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an article verification task."""
        try:
            params = ArticleVerificationParams(
                articles=task.get('articles', []),
                min_title_length=task.get('min_title_length', 20),
                min_description_length=task.get('min_description_length', 50)
            )
            result = await self.verify_articles(params)
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