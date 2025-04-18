"""Example agent demonstrating the updated BaseAgent implementation."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import json
import os

from agents import function_tool, WebSearchTool

from src.agents.base_agent import BaseAgent, Trace
from src.tools.news_tool import fetch_news_tool, FetchNewsInput
from src.config import get_logger

logger = get_logger(__name__)

class NewsRequest(BaseModel):
    """Input model for the news agent."""
    
    category: str = Field(
        description="News category to fetch articles from (business, entertainment, general, health, science, sports, technology)",
        default="general"
    )
    count: int = Field(
        description="Number of articles to fetch",
        default=5
    )
    country: Optional[str] = Field(
        description="The 2-letter ISO 3166-1 code of the country (e.g., us, gb, au)",
        default=None
    )
    sources: Optional[str] = Field(
        description="A comma-separated string of news source IDs (e.g., bbc-news,cnn)",
        default=None
    )
    query: Optional[str] = Field(
        description="Keywords or phrase to search for in the news",
        default=None
    )
    page: Optional[int] = Field(
        description="Page number for paginated results",
        default=None
    )
    voice: Optional[str] = Field(
        description="Voice to use for audio output (alloy, echo, fable, onyx, nova, shimmer)",
        default="alloy"
    )
    generate_audio: bool = Field(
        description="Whether to generate an audio file from the summary",
        default=True
    )
    summary_style: Optional[str] = Field(
        description="Style of the summary (formal, conversational, brief)",
        default="conversational"
    )

class NewsArticle(BaseModel):
    """Model for a news article."""
    
    title: str
    description: str
    url: str
    source: str
    published_at: str

class NewsSummary(BaseModel):
    """Model for a news summary."""
    
    category: str = Field(description="Category requested")
    article_count: int = Field(description="Number of articles processed")
    articles: List[NewsArticle] = Field(description="List of processed articles")
    summary: str = Field(description="Concise summary of the articles")
    markdown: Optional[str] = Field(description="Markdown representation of the summary and articles", default=None)

# Create a function_tool from the existing fetch_news_tool
@function_tool
def fetch_news(
    category: str, 
    count: int, 
    country: str = None, 
    sources: str = None, 
    query: str = None, 
    page: int = None
) -> List[Dict[str, Any]]:
    """Fetch news articles from a specified category.
    
    Args:
        category: The news category (business, entertainment, general, health, science, sports, technology)
        count: Number of articles to fetch
        country: The 2-letter ISO 3166-1 code of the country (e.g., us, gb, au)
        sources: A comma-separated string of news source IDs (e.g., bbc-news,cnn)
        query: Keywords or phrase to search for in the news
        page: Page number for paginated results
    
    Returns:
        A list of news articles
    """
    # Handle default count inside function
    count = count if count > 0 else 5
    
    # Create input data with all parameters
    input_data = FetchNewsInput(
        category=category, 
        count=count,
        country=country,
        sources=sources,
        query=query,
        page=page
    )
    
    return fetch_news_tool.run(input_data)

class NewsAgent(BaseAgent[NewsRequest, NewsSummary]):
    """Agent that fetches and summarizes news articles."""
    
    def __init__(self, verbose: bool = False, model: str = None, temperature: float = None):
        """Initialize the news agent with the news fetching tool."""
        # Store category for later use in _process_output
        self._requested_category = "unknown" 
        
        super().__init__(
            name="NewsAgent",
            instructions="""
            You are an agent that fetches and summarizes news articles.
            Your primary task is to use the fetch_news tool to get articles based on the user's request (category, count, etc.).
            After fetching, review the articles.
            If the initial articles seem insufficient or you need broader context for a good summary, you MAY use the WebSearchTool to find additional relevant information or recent articles on the same topic.
            Perform the following:
            1. Create a concise summary (1-2 paragraphs) covering the main points from ALL fetched articles (from fetch_news and potentially web search).
            2. Prepare a list of the fetched articles, including their title, description, source, url, and published_at date.
            
            IMPORTANT: Structure your FINAL output as a single JSON object containing:
            - A key "articles" whose value is a JSON list of the fetched article objects (each object having keys: "title", "description", "source", "url", "published_at").
            - A key "summary" whose value is the concise summary string you created.
            - A key "markdown" whose value is a string containing a user-friendly markdown representation of the articles and the summary (Use H2 for sections like '## Articles' and '## Summary').
            
            Example JSON Output Structure:
            {
              "articles": [
                {
                  "title": "Example Title 1", 
                  "description": "Example description 1.", 
                  "source": "Example Source 1", 
                  "url": "http://example.com/1", 
                  "published_at": "YYYY-MM-DD"
                }, 
                {...} 
              ],
              "summary": "This is the concise summary paragraph.",
              "markdown": "## Articles\n\n### [Example Title 1](http://example.com/1)\n...\n\n## Summary\n\nThis is the concise summary paragraph."
            }
            
            Ensure the JSON is valid. Output ONLY the JSON object and nothing else.
            """,
            tools=[fetch_news, WebSearchTool()],
            verbose=verbose,
            model=model,
            temperature=temperature
        )
        
        logger.info("NewsAgent initialized with news fetching tool")
    
    async def run(self, input_data: NewsRequest, parent_trace: Optional[Trace] = None) -> NewsSummary:
        """
        Run the news agent to fetch and summarize articles.
        
        Args:
            input_data: The input parameters
            parent_trace: The parent trace for the agent's output
            
        Returns:
            A summary of the news articles
        """
        # Store the requested category for use in _process_output
        self._requested_category = input_data.category
        
        # Run the base agent implementation
        # No need for TTS logic here, Coordinator handles it
        result = await super().run(input_data, parent_trace=parent_trace)
        
        # The result from super().run calls _process_output internally, 
        # which now handles JSON parsing and returns a NewsSummary object.
        return result
    
    def _process_output(self, output: str) -> NewsSummary:
        """
        Process the raw output from the agent (expected to be JSON) into a NewsSummary object.
        
        Args:
            output: The raw output string from the agent.
            
        Returns:
            A NewsSummary object.
        """
        try:
            # Clean the output string: remove potential markdown code fences
            cleaned_output = output.strip().strip("`json\n").strip("```")
            
            # Attempt to parse the cleaned string as JSON
            data = json.loads(cleaned_output)
            
            # Validate and create the Pydantic model
            # Ensure required fields exist
            if "articles" not in data or "summary" not in data:
                raise ValueError("Missing required fields 'articles' or 'summary' in JSON output")
                
            # Manually add derived/contextual fields before validation
            data["category"] = self._requested_category # Use stored category
            data["article_count"] = len(data.get("articles", []))
            
            # Create the NewsSummary object
            news_summary = NewsSummary(**data)
            
            logger.info(f"Successfully parsed NewsAgent output for category: {news_summary.category}")
            return news_summary

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from NewsAgent output: {e}\nRaw output:\n{output}")
            # Return a default/empty NewsSummary on failure
            return NewsSummary(
                category=self._requested_category,
                article_count=0,
                articles=[],
                summary="Error: Could not parse news summary data.",
                markdown="## Error\n\nCould not parse news summary data from the agent."
            )
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Error validating/processing parsed JSON data: {e}\nParsed data:\n{data if 'data' in locals() else 'N/A'}\nRaw output:\n{output}")
             # Return a default/empty NewsSummary on failure
            return NewsSummary(
                category=self._requested_category,
                article_count=0,
                articles=[],
                summary=f"Error: Invalid data structure received: {e}",
                markdown=f"## Error\n\nInvalid data structure received from the agent: {e}"
            )
        except Exception as e:
            logger.error(f"Unexpected error processing NewsAgent output: {e}\nRaw output:\n{output}")
             # Return a default/empty NewsSummary on failure
            return NewsSummary(
                category=self._requested_category,
                article_count=0,
                articles=[],
                summary=f"Error: Unexpected error processing news data: {e}",
                markdown=f"## Error\n\nUnexpected error processing news data: {e}"
            ) 
