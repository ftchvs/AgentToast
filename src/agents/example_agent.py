"""Example agent demonstrating the updated BaseAgent implementation."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import json
import os

from agents import function_tool

from src.agents.base_agent import BaseAgent
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
            Your job is to fetch news from a given category and provide a brief summary of the main points.
            
            1. Use the fetch_news tool to get articles from the requested category
            2. Review the articles and extract the most important information
            3. Create a concise summary of the news in the category
            4. Format your response in proper Markdown format with appropriate headers and formatting
            
            Always follow these formatting guidelines:
            - Use a level 1 header (# ) for the main title
            - Use level 2 headers (## ) for major sections
            - Use level 3 headers (### ) for subsections
            - Use bullet points (- ) for lists of items
            - Use proper links: [Link text](URL)
            - Use bold (**bold**) and italics (*italics*) for emphasis
            
            IMPORTANT: Always include a dedicated "## Summary" or "### Key Points" section with 1-2 paragraphs
            that concisely summarize the main takeaways from all articles. This section will be used for audio summaries.
            
            Your final output should be properly formatted Markdown that would render correctly on a Markdown viewer.
            """,
            tools=[fetch_news],
            verbose=verbose,
            model=model,
            temperature=temperature
        )
        
        logger.info("NewsAgent initialized with news fetching tool")
    
    async def run(self, input_data: NewsRequest) -> NewsSummary:
        """
        Run the news agent to fetch and summarize articles.
        
        Args:
            input_data: The input parameters
            
        Returns:
            A summary of the news articles
        """
        # Run the base agent implementation
        result = await super().run(input_data)
        
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
        """
        Process the agent's output into a structured NewsSummary.
        
        Args:
            output: The raw output string from the agent
            
        Returns:
            A structured NewsSummary object
        """
        try:
            # Try to parse the output as JSON
            data = json.loads(output)
            
            # Extract the required fields
            category = data.get("category", "general")
            article_count = data.get("article_count", 0)
            articles_data = data.get("articles", [])
            summary = data.get("summary", "No summary provided")
            
            # Convert article data to NewsArticle objects
            articles = []
            for article_data in articles_data:
                article = NewsArticle(
                    title=article_data.get("title", "No title"),
                    description=article_data.get("description", "No description"),
                    url=article_data.get("url", ""),
                    source=article_data.get("source", "Unknown source"),
                    published_at=article_data.get("published_at", "")
                )
                articles.append(article)
            
            # Create and return the NewsSummary
            return NewsSummary(
                category=category,
                article_count=article_count,
                articles=articles,
                summary=summary,
                markdown=summary  # Store the markdown version
            )
            
        except json.JSONDecodeError:
            # If the output is not valid JSON, attempt to extract info from text
            self.logger.warning("Failed to parse agent output as JSON")
            
            # Simple attempt to extract article info using pattern matching
            articles = []
            category = "general"
            summary = output
            
            # Try to find article titles and urls in the text
            import re
            title_pattern = r"\*\*Title:\*\*\s*(.*?)(?:\n|$)|\*\*\[(.*?)\]\("
            desc_pattern = r"\*\*Description:\*\*\s*(.*?)(?:\n|$)"
            source_pattern = r"\*\*Source:\*\*\s*(.*?)(?:\n|$)"
            url_pattern = r"\[Read more\]\((.*?)\)|\*\*\[[^\]]+\]\((.*?)\)"
            published_pattern = r"\*\*Published [Aa]t:\*\*\s*(.*?)(?:\n|$)"
            
            # Try to extract the category
            category_match = re.search(r"NEWS SUMMARY:\s*(.*?)(?:\n|$)", output, re.IGNORECASE)
            if category_match:
                category = category_match.group(1).lower()
            
            # Find titles and create article objects
            title_matches = list(re.finditer(title_pattern, output))
            url_matches = list(re.finditer(url_pattern, output))
            
            for i, title_match in enumerate(title_matches):
                # Get the title from either group 1 or group 2 (depending on which pattern matched)
                title = title_match.group(1) if title_match.group(1) else title_match.group(2)
                title = title.strip() if title else "No title"
                
                # Find corresponding description, source, and URL
                match_pos = title_match.end()
                desc_match = re.search(desc_pattern, output[match_pos:])
                source_match = re.search(source_pattern, output[match_pos:])
                published_match = re.search(published_pattern, output[match_pos:])
                
                # Get URL either from the pattern or try to match with url_matches
                url = ""
                if i < len(url_matches):
                    url_match = url_matches[i]
                    url = url_match.group(1) if url_match.group(1) else url_match.group(2)
                    url = url.strip() if url else ""
                
                description = desc_match.group(1).strip() if desc_match else "No description"
                source = source_match.group(1).strip() if source_match else "Unknown source"
                published_at = published_match.group(1).strip() if published_match else ""
                
                article = NewsArticle(
                    title=title,
                    description=description,
                    url=url,
                    source=source,
                    published_at=published_at
                )
                articles.append(article)
            
            # Try to extract the summary section
            summary_match = re.search(r"(?:### Summary:?|### Summary of .+?:)(.*?)(?:-{5,}|$)", output, re.DOTALL | re.IGNORECASE)
            if summary_match:
                summary = summary_match.group(1).strip()
            
            return NewsSummary(
                category=category,
                article_count=len(articles),
                articles=articles,
                summary=summary,
                markdown=output  # Store the full markdown output
            )
        except Exception as e:
            # Log any other errors and return a minimal object
            self.logger.error(f"Error processing agent output: {str(e)}")
            return NewsSummary(
                category="general",
                article_count=0,
                articles=[],
                summary=f"Error processing output: {str(e)}",
                markdown=output
            ) 