from typing import List, Dict, Any
from openai.lib import pydantic_function_tool
from pydantic import BaseModel, Field, ConfigDict
from src.agents.base_agent import BaseAgent
from src.agents.fetcher_agent import FetcherAgent, Article, NewsParams
from src.agents.verifier_agent import VerifierAgent, ArticleVerificationParams
from src.agents.summarizer_agent import SummarizerAgent, ArticleSummaryParams, SummaryResult, SummaryStats
import logging

class NewsProcessingParams(BaseModel):
    model_config = ConfigDict(extra='forbid')
    category: str = Field(
        description="News category to process",
        pattern="^(business|entertainment|general|health|science|sports|technology)$"
    )
    count: int = Field(
        description="Number of articles to process",
        ge=1,
        le=10,
        default=5
    )
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
    max_summary_length: int = Field(
        description="Maximum length of each summary",
        ge=50,
        le=500,
        default=200
    )

class ProcessingResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    category: str = Field(description="Category of processed articles")
    total_fetched: int = Field(description="Total number of articles fetched")
    total_verified: int = Field(description="Number of articles that passed verification")
    total_rejected: int = Field(description="Number of articles that failed verification")
    avg_summary_length: float = Field(description="Average summary length")
    summaries: List[Dict[str, Any]] = Field(description="List of article summaries")

class OrchestratorAgent(BaseAgent):
    """Agent responsible for orchestrating the news processing workflow."""
    
    def __init__(self):
        """Initialize the OrchestratorAgent."""
        # Create the process_news function tool
        self.process_news_tool = pydantic_function_tool(
            model=NewsProcessingParams,
            name="process_news",
            description="Process news articles from a specific category"
        )
        
        super().__init__(
            name="News Orchestrator",
            instructions="""I am an orchestration agent that coordinates the news processing workflow.
            I manage the fetching, verification, and summarization of news articles.""",
            tools=[self.process_news_tool]
        )
        
        # Initialize sub-agents
        self.fetcher = FetcherAgent()
        self.verifier = VerifierAgent()
        self.summarizer = SummarizerAgent()

    async def process_news(self, params: NewsProcessingParams) -> ProcessingResult:
        """
        Process news articles from a specific category.
        
        Args:
            params: Parameters containing:
                - category: News category to process
                - count: Number of articles to process
                - min_title_length: Minimum required title length
                - min_description_length: Minimum required description length
                - max_summary_length: Maximum length of each summary
            
        Returns:
            ProcessingResult containing:
            - category: Category of processed articles
            - total_fetched: Total number of articles fetched
            - total_verified: Number of articles that passed verification
            - total_rejected: Number of articles that failed verification
            - avg_summary_length: Average summary length
            - summaries: List of article summaries
        """
        try:
            logging.info(f"Processing news for category: {params.category}")
            
            # Step 1: Fetch articles
            fetch_params = NewsParams(
                category=params.category,
                count=params.count
            )
            fetch_result = await self.fetcher.fetch_news(fetch_params)
            
            if not fetch_result.articles:
                raise Exception("No articles were fetched")
            
            # Step 2: Verify articles
            # Convert Article objects to dictionaries
            articles_dict = [article.model_dump() for article in fetch_result.articles]
            verify_params = ArticleVerificationParams(
                articles=articles_dict,
                min_title_length=params.min_title_length,
                min_description_length=params.min_description_length
            )
            verify_result = await self.verifier.verify_articles(verify_params)
            
            # Step 3: Summarize verified articles
            if verify_result.total_verified > 0:
                # Convert verified articles to dictionaries
                verified_articles_dict = [article.model_dump() for article in verify_result.verified_articles]
                summary_params = ArticleSummaryParams(
                    articles=verified_articles_dict,
                    max_length=params.max_summary_length
                )
                summary_result = await self.summarizer.summarize_articles(summary_params)
            else:
                summary_result = SummaryResult(
                    summaries=[],
                    stats=SummaryStats(
                        total_articles=0,
                        avg_summary_length=0,
                        min_summary_length=0,
                        max_summary_length=0
                    )
                )
            
            # Prepare final result
            result = ProcessingResult(
                category=params.category,
                total_fetched=len(fetch_result.articles),
                total_verified=verify_result.total_verified,
                total_rejected=verify_result.total_rejected,
                avg_summary_length=summary_result.stats.avg_summary_length,
                summaries=[{
                    'title': s.article.title,
                    'summary': s.summary,
                    'url': s.article.url,
                    'source': s.article.source
                } for s in summary_result.summaries]
            )
            
            logging.info(f"News processing complete: {result.model_dump()}")
            return result
            
        except Exception as e:
            logging.error(f"Error processing news: {str(e)}")
            raise

    async def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a news processing task."""
        try:
            params = NewsProcessingParams(
                category=task.get('category', 'general'),
                count=task.get('count', 5),
                min_title_length=task.get('min_title_length', 20),
                min_description_length=task.get('min_description_length', 50),
                max_summary_length=task.get('max_summary_length', 200)
            )
            result = await self.process_news(params)
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