"""Example agent demonstrating the updated BaseAgent implementation."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import json
import os

from agents import function_tool

from src.agents.base_agent import BaseAgent, Trace
from src.agents.writer_agent import WriterAgent, WriterInput
from src.tools.news_tool import fetch_news_tool, FetchNewsInput
from src.config import get_logger
from src.utils.tts import text_to_speech

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
    
    category: str
    article_count: int
    articles: List[NewsArticle]
    summary: str
    audio_file: Optional[str] = None
    markdown: Optional[str] = None

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
        
        # Initialize the base agent with the news tool
        super().__init__(
            name="NewsAgent",
            instructions="""
            You are an agent that fetches and summarizes news articles.
            Your primary task is to use the fetch_news tool to get articles based on the user's request (category, count, etc.).
            After fetching, review the articles and perform the following:
            1. Create a concise summary (1-2 paragraphs) covering the main points from ALL fetched articles.
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
            tools=[fetch_news],
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
        # Run the base agent implementation, passing the parent trace
        result = await super().run(input_data, parent_trace=parent_trace)
        
        # Generate audio if requested
        if input_data.generate_audio and result.summary:
            try:
                logger.info(f"Generating audio from summary with voice: {input_data.voice}")
                
                # Use the writer agent to create a concise audio summary
                writer_agent = WriterAgent(
                    verbose=self.verbose,
                    model=self.model,
                    temperature=self.temperature
                )
                
                # Prepare articles data for the writer
                articles_data = [
                    {
                        "title": article.title,
                        "description": article.description,
                        "source": article.source,
                        "url": article.url,
                        "published_at": article.published_at
                    }
                    for article in result.articles
                ]
                
                # Create input for the writer agent
                writer_input = WriterInput(
                    category=result.category,
                    articles=articles_data,
                    max_length=600,  # Target length for TTS
                    style=input_data.summary_style  # Use the style specified in the input
                )
                
                # Run the writer agent to get a concise summary
                # TODO: Should the writer agent call also be traced under the NewsAgent trace?
                # This would require passing the trace from super().run() down.
                # For now, writer runs independently trace-wise within NewsAgent.
                writer_result = await writer_agent.run(writer_input)
                
                # Use the writer's summary for TTS
                tts_text = writer_result.summary
                
                # Generate the audio file
                audio_file = text_to_speech(
                    text=tts_text,
                    voice=input_data.voice
                )
                
                if audio_file:
                    result.audio_file = audio_file
                    logger.info(f"Generated audio file: {audio_file}")
                
            except Exception as e:
                logger.error(f"Error generating audio: {str(e)}")
                # Fallback to original summary method if writer agent fails
                tts_text = self._create_audio_summary(result)
                audio_file = text_to_speech(text=tts_text, voice=input_data.voice)
                if audio_file:
                    result.audio_file = audio_file
                    logger.info(f"Generated audio file (fallback): {audio_file}")
        
        return result
    
    def _create_audio_summary(self, result: NewsSummary) -> str:
        """
        Create a concise 1-2 paragraph summary of the news articles specifically for audio.
        
        Args:
            result: The full news summary result
            
        Returns:
            A concise text suitable for text-to-speech
        """
        # Get category and article count for intro
        category = result.category.capitalize()
        article_count = result.article_count
        
        # Create a brief introduction
        intro = f"Here's a summary of {article_count} {category} news articles."
        
        # Extract the most important points
        # First, try to find if there's already a summary section in the markdown
        import re
        summary_text = ""
        
        # Look for a summary section in the markdown
        summary_match = re.search(r"(?:### Summary:?|## Summary|### Key Points)(.*?)(?:##|\Z)", 
                                  result.summary, re.DOTALL | re.IGNORECASE)
        
        if summary_match:
            # Use the existing summary section if found
            summary_text = summary_match.group(1).strip()
            # Clean up markdown formatting
            summary_text = self._prepare_text_for_tts(summary_text)
        else:
            # If no summary section found, create one from the full text
            # Extract article titles for context
            titles = [article.title for article in result.articles]
            
            # Create a brief overview
            if titles:
                topics = ", ".join(titles[:3])
                if len(titles) > 3:
                    topics += f", and {len(titles) - 3} more"
                summary_text = f"Topics include {topics}. "
            
            # Add main points from the full summary, limited to ~2 paragraphs
            full_text = self._prepare_text_for_tts(result.summary)
            
            # Split by sentences and limit to create a concise summary
            sentences = re.split(r'(?<=[.!?])\s+', full_text)
            important_sentences = sentences[:min(8, len(sentences))]
            summary_text += " ".join(important_sentences)
        
        # Combine intro and summary, ensure it's not too long (limit to ~500 characters)
        full_summary = f"{intro} {summary_text}"
        if len(full_summary) > 800:
            # Truncate and add an ending if too long
            full_summary = full_summary[:790] + "... That concludes this summary."
        
        return full_summary
    
    def _prepare_text_for_tts(self, markdown_text: str) -> str:
        """
        Prepare markdown text for text-to-speech by removing excessive markdown syntax.
        
        Args:
            markdown_text: The markdown text to clean
            
        Returns:
            A cleaned version of the text suitable for TTS
        """
        import re
        
        # Store the original markdown
        result = markdown_text
        
        # Replace markdown headers with plain text
        result = re.sub(r'^#{1,6}\s+(.+)$', r'\1.', result, flags=re.MULTILINE)
        
        # Replace markdown links with just the text
        result = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', result)
        
        # Replace bold and italic with plain text
        result = re.sub(r'\*\*([^*]+)\*\*', r'\1', result)  # Bold
        result = re.sub(r'\*([^*]+)\*', r'\1', result)      # Italic
        
        # Replace bullet points with dashes
        result = re.sub(r'^[\*\-\+]\s+', '- ', result, flags=re.MULTILINE)
        
        # Remove any remaining special characters
        result = re.sub(r'[\\`]', '', result)
        
        return result
    
    def _process_output(self, output: str) -> NewsSummary:
        """Process the agent's JSON output."""
        try:
            self.logger.debug(f"Attempting to parse NewsAgent output as JSON: {output[:500]}...")
            data = json.loads(output)
            
            articles_data = data.get("articles", [])
            articles = []
            for article_dict in articles_data:
                # Basic validation/handling of potentially missing keys
                articles.append(NewsArticle(
                    title=article_dict.get("title", "N/A"),
                    description=article_dict.get("description", "N/A"),
                    url=article_dict.get("url", ""),
                    source=article_dict.get("source", "Unknown"),
                    published_at=article_dict.get("published_at", "")
                ))
            
            summary = data.get("summary", "Summary not found in output.")
            markdown = data.get("markdown", None) # Markdown is optional in the output model

            # Assume category comes from input, not LLM output typically
            # We might need to pass the input category through context if needed here
            # For now, setting a placeholder or potentially erroring if not available
            category = "unknown" # Placeholder - ideally get from input context
            self.logger.warning("Category not directly available in _process_output, using placeholder.")

            return NewsSummary(
                category=category, # Needs to be set correctly
                article_count=len(articles),
                articles=articles,
                summary=summary,
                markdown=markdown
            )

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse NewsAgent output as JSON: {e}")
            self.logger.debug(f"Raw output causing JSON error: {output}")
            # Fallback or error handling if JSON parsing fails
            # Returning an empty/error state might be safer than trying complex regex
            return NewsSummary(
                category="error", 
                article_count=0, 
                articles=[], 
                summary=f"Error: Failed to parse agent output. Output was: {output[:200]}...",
                markdown=f"# Error\nFailed to parse agent output.\n\nRaw output:\n```\n{output}\n```"
            )
        except Exception as e:
            self.logger.exception(f"An unexpected error occurred processing NewsAgent output: {e}")
            return NewsSummary(
                category="error", 
                article_count=0, 
                articles=[], 
                summary=f"Error: Unexpected error processing output: {str(e)}",
                markdown=f"# Error\nUnexpected error processing output: {str(e)}"
            ) 
