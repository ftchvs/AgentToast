"""Analyst agent for providing deeper insights on news articles."""

from typing import List, Optional
from pydantic import BaseModel, Field
import logging

from agents import function_tool
from src.agents.base_agent import BaseAgent
from src.config import get_logger

logger = get_logger(__name__)

class AnalystInput(BaseModel):
    """Input for the analyst agent."""
    
    category: str = Field(
        description="The category of news articles (e.g., technology, business)",
    )
    articles: List[dict] = Field(
        description="List of news articles with title, description, source, url and published_at",
    )
    summary: str = Field(
        description="The initial summary of the news articles",
    )
    depth: str = Field(
        description="Level of analysis depth (basic, moderate, deep)",
        default="moderate"
    )

class AnalystOutput(BaseModel):
    """Output from the analyst agent."""
    
    insights: str = Field(
        description="Key insights and analysis of the news"
    )
    trends: List[str] = Field(
        description="Identified trends or patterns",
        default_factory=list
    )
    implications: List[str] = Field(
        description="Potential implications of the news",
        default_factory=list
    )

class AnalystAgent(BaseAgent[AnalystInput, AnalystOutput]):
    """Agent that analyzes news articles to provide deeper insights."""
    
    def __init__(self, verbose: bool = False, model: str = None, temperature: float = None):
        """Initialize the analyst agent."""
        
        super().__init__(
            name="AnalystAgent",
            instructions="""
            You are an expert news analyst with deep expertise across multiple fields.
            
            Your task is to analyze news articles and provide:
            1. Critical insights that go beyond the surface of the news
            2. Identification of trends, patterns, or connections between stories
            3. Potential implications or consequences of the developments
            4. Historical context and relevance to current events
            5. Factual accuracy assessment of key claims when possible
            
            When analyzing news, consider:
            - Who benefits from the developments
            - What might be missing from the coverage
            - How this relates to broader industry or societal trends
            - What the long-term impact might be
            
            Adjust your analysis based on the 'depth' parameter:
            - 'basic': Focus on immediate implications and surface-level analysis
            - 'moderate': Include broader context and mid-term implications
            - 'deep': Provide comprehensive analysis including historical context, detailed implications,
              and connections to broader social, economic, or political trends
            
            Your analysis should be:
            - Evidence-based, citing specific details from the articles
            - Balanced, acknowledging different perspectives
            - Accessible to informed readers
            - Insightful, providing value beyond the original reporting
            
            Remain objective and avoid inserting political biases or opinions. Focus on analysis, not advocacy.
            """,
            tools=[],  # No tools needed for this agent
            verbose=verbose,
            model=model,
            temperature=temperature
        )
        
        logger.info("AnalystAgent initialized")
    
    def _process_output(self, output: str) -> AnalystOutput:
        """Process the agent output into the proper format."""
        import json
        import re
        
        try:
            # Try to parse as JSON first
            data = json.loads(output)
            return AnalystOutput(
                insights=data.get("insights", ""),
                trends=data.get("trends", []),
                implications=data.get("implications", [])
            )
        except:
            # If not JSON, try to extract information from text
            insights = output
            
            # Try to extract trends section
            trends = []
            trends_match = re.search(r"(?:Trends|TRENDS|Key Trends):(.*?)(?:\n\n|\n[A-Z]|$)", output, re.DOTALL | re.IGNORECASE)
            if trends_match:
                trends_text = trends_match.group(1).strip()
                trends = [t.strip() for t in re.split(r"\n-|\n\d+\.", trends_text) if t.strip()]
            
            # Try to extract implications section
            implications = []
            implications_match = re.search(r"(?:Implications|IMPLICATIONS|Key Implications):(.*?)(?:\n\n|\n[A-Z]|$)", output, re.DOTALL | re.IGNORECASE)
            if implications_match:
                implications_text = implications_match.group(1).strip()
                implications = [i.strip() for i in re.split(r"\n-|\n\d+\.", implications_text) if i.strip()]
            
            return AnalystOutput(
                insights=insights,
                trends=trends,
                implications=implications
            ) 