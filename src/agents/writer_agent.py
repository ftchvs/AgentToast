"""Writer agent for creating concise summaries."""

from typing import List, Optional
from pydantic import BaseModel, Field
import logging

from agents import function_tool
from src.agents.base_agent import BaseAgent
from src.config import get_logger

logger = get_logger(__name__)

class WriterInput(BaseModel):
    """Input for the writer agent."""
    
    category: str = Field(
        description="The category of news articles (e.g., technology, business)",
    )
    articles: List[dict] = Field(
        description="List of news articles with title, description, source, url and published_at",
    )
    max_length: int = Field(
        description="Maximum length of the summary in characters",
        default=500
    )
    style: str = Field(
        description="Style of the summary (e.g., formal, conversational, brief)",
        default="conversational"
    )
    additional_context: Optional[str] = Field(
        description="Additional context such as news summary, fact checks, analysis, and trends",
        default=None
    )

class WriterOutput(BaseModel):
    """Output from the writer agent."""
    
    summary: str = Field(
        description="A concise 1-2 paragraph summary of the news articles"
    )

class WriterAgent(BaseAgent[WriterInput, WriterOutput]):
    """Agent that creates concise summaries from news articles."""
    
    def __init__(self, verbose: bool = False, model: str = None, temperature: float = None):
        """Initialize the writer agent."""
        
        super().__init__(
            name="WriterAgent",
            instructions="""
            You are a professional writer specializing in creating concise news summaries.
            
            Your task is to review news articles and create a brief, engaging summary that:
            1. Accurately summarizes the main news stories from the provided articles
            2. Captures key events, people, and important developments
            3. Highlights the most newsworthy aspects of the stories
            4. Presents factual information in a clear, accessible way
            5. Uses language suitable for audio narration
            
            Your summary should:
            - Be concise (1-2 paragraphs)
            - Accurately reflect the actual news content of the articles
            - Include the most important facts and details from the articles
            - Be written in a way that would sound natural when spoken aloud
            - Focus on the actual news rather than generic observations
            
            IMPORTANT: Your audio summary must accurately reflect the content of the original news articles. 
            Don't write generic summaries - include specific facts, events, and information from the actual news stories.
            
            Adjust your writing style based on the 'style' parameter:
            - 'formal': More professional, objective phrasing
            - 'conversational': Natural, approachable language
            - 'brief': Maximum information density with minimal words
            
            If additional context is provided, use it to inform your summary and ensure accuracy.
            
            Keep your summary under the specified maximum length.
            """,
            tools=[],  # No tools needed for this agent
            verbose=verbose,
            model=model,
            temperature=temperature
        )
        
        logger.info("WriterAgent initialized")
    
    def _process_output(self, output: str) -> WriterOutput:
        """Process the agent output into the proper format."""
        return WriterOutput(summary=output.strip()) 
