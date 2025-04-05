from typing import List, Dict, Any
from openai.lib import pydantic_function_tool
from pydantic import BaseModel, Field, ConfigDict
from src.agents.base_agent import BaseAgent
from src.agents.fetcher_agent import Article
import logging

class ArticleSummaryParams(BaseModel):
    model_config = ConfigDict(extra='forbid')
    articles: List[Dict[str, Any]] = Field(description="List of articles to summarize")
    max_length: int = Field(
        description="Maximum length of each summary",
        ge=50,
        le=500,
        default=200
    )

class Summary(BaseModel):
    model_config = ConfigDict(extra='forbid')
    article: Article = Field(description="Original article")
    summary: str = Field(description="Generated summary")
    length: int = Field(description="Length of the summary")

class SummaryStats(BaseModel):
    model_config = ConfigDict(extra='forbid')
    total_articles: int = Field(description="Total number of articles processed")
    avg_summary_length: float = Field(description="Average summary length")
    min_summary_length: int = Field(description="Minimum summary length")
    max_summary_length: int = Field(description="Maximum summary length")

class SummaryResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    summaries: List[Summary] = Field(description="List of article summaries")
    stats: SummaryStats = Field(description="Summary statistics")

class SummarizerAgent(BaseAgent):
    """Agent responsible for summarizing news articles."""
    
    def __init__(self):
        """Initialize the SummarizerAgent."""
        # Create the summarize_articles function tool
        self.summarize_articles_tool = pydantic_function_tool(
            model=ArticleSummaryParams,
            name="summarize_articles",
            description="Generate concise summaries of news articles"
        )
        
        super().__init__(
            name="Article Summarizer",
            instructions="""I am a summarization agent that creates concise article summaries.
            I ensure summaries capture key information while staying within length limits.""",
            tools=[self.summarize_articles_tool]
        )

    async def summarize_articles(self, params: ArticleSummaryParams) -> SummaryResult:
        """
        Generate summaries for a list of articles.
        
        Args:
            params: Parameters containing:
                - articles: List of articles to summarize
                - max_length: Maximum length of each summary
            
        Returns:
            SummaryResult containing:
            - summaries: List of article summaries
            - stats: Summary statistics
        """
        try:
            logging.info(f"Summarizing {len(params.articles)} articles")
            
            summaries = []
            total_length = 0
            min_length = float('inf')
            max_length = 0
            
            for article_data in params.articles:
                article = Article(**article_data)
                
                # Generate summary by combining title and description
                full_text = f"{article.description}"
                
                # Ensure summary ends at a sentence boundary
                if len(full_text) > params.max_length:
                    # Find the last sentence boundary before max_length
                    end_markers = ['. ', '! ', '? ']
                    possible_ends = [
                        full_text[:params.max_length].rindex(marker)
                        for marker in end_markers
                        if marker in full_text[:params.max_length]
                    ]
                    
                    if possible_ends:
                        # Take the latest sentence boundary
                        end_idx = max(possible_ends) + 1  # Include the period
                        summary_text = full_text[:end_idx].strip()
                    else:
                        # If no sentence boundary found, use the full text up to max_length
                        summary_text = full_text[:params.max_length].strip()
                else:
                    summary_text = full_text.strip()
                
                summary_length = len(summary_text)
                
                summary = Summary(
                    article=article,
                    summary=summary_text,
                    length=summary_length
                )
                summaries.append(summary)
                
                # Update statistics
                total_length += summary_length
                min_length = min(min_length, summary_length)
                max_length = max(max_length, summary_length)
            
            # Calculate statistics
            total_articles = len(summaries)
            avg_length = total_length / total_articles if total_articles > 0 else 0
            min_length = min_length if total_articles > 0 else 0
            
            stats = SummaryStats(
                total_articles=total_articles,
                avg_summary_length=avg_length,
                min_summary_length=min_length,
                max_summary_length=max_length
            )
            
            result = SummaryResult(
                summaries=summaries,
                stats=stats
            )
            
            logging.info(f"Summarization complete: {total_articles} articles processed")
            return result
            
        except Exception as e:
            logging.error(f"Error summarizing articles: {str(e)}")
            raise

    async def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an article summarization task."""
        try:
            params = ArticleSummaryParams(
                articles=task.get('articles', []),
                max_length=task.get('max_length', 200)
            )
            result = await self.summarize_articles(params)
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