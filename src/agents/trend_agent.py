"""Trend agent for identifying patterns and trends across news articles."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import logging

from agents import function_tool
from src.agents.base_agent import BaseAgent
from src.config import get_logger

logger = get_logger(__name__)

class TrendInput(BaseModel):
    """Input for the trend agent."""
    
    category: str = Field(
        description="The category of news articles (e.g., technology, business)",
    )
    articles: List[dict] = Field(
        description="List of news articles with title, description, source, url and published_at",
    )
    historical_data: Optional[Dict[str, List[str]]] = Field(
        description="Optional historical data with categories as keys and lists of trends as values",
        default=None
    )

class Trend(BaseModel):
    """Model for a single identified trend."""
    
    name: str = Field(description="Name/title of the trend")
    description: str = Field(description="Detailed description of the trend")
    strength: str = Field(description="Strength of the trend (Emerging, Growing, Established, Declining)")
    supporting_articles: List[str] = Field(description="Articles supporting this trend identification")
    timeframe: str = Field(description="Estimated timeframe for this trend (Short-term, Long-term)")

class TrendOutput(BaseModel):
    """Output from the trend agent."""
    
    trends: List[Trend] = Field(
        description="List of identified trends",
        default_factory=list
    )
    meta_trends: List[str] = Field(
        description="Higher-level or meta trends that connect multiple trends",
        default_factory=list
    )
    summary: str = Field(
        description="Summary of trend analysis"
    )

class TrendAgent(BaseAgent[TrendInput, TrendOutput]):
    """Agent that identifies trends and patterns in news articles."""
    
    def __init__(self, verbose: bool = False, model: str = None, temperature: float = None):
        """Initialize the trend agent."""
        
        super().__init__(
            name="TrendAgent",
            instructions="""
            You are an expert trend analyst specializing in identifying emerging patterns in news.
            
            Your task is to:
            1. Identify significant trends and patterns in the provided news articles
            2. Connect these trends to broader movements or shifts when possible
            3. Assess the strength and potential trajectory of each trend
            4. Provide insightful analysis of what these trends might mean
            
            For each trend you identify, provide:
            - A clear, concise name for the trend
            - A detailed description explaining the trend
            - An assessment of the trend's strength (Emerging, Growing, Established, Declining)
            - Supporting evidence from the articles
            - An estimated timeframe for the trend (Short-term, Medium-term, Long-term)
            
            When identifying trends, consider:
            - Recurring themes or topics across multiple articles
            - Shifts in focus or emphasis within a topic
            - New developments that could signal future directions
            - Historical context when available
            - Geographic and demographic patterns
            
            Also identify any meta-trends:
            - These are higher-level patterns that connect multiple trends
            - They often indicate broader societal or industry shifts
            
            Your output should be well-organized and provide genuine insights beyond what's immediately obvious.
            Focus on quality over quantity - identify the most significant trends rather than listing everything.
            
            If there are fewer than 3 articles provided, note this limitation in your analysis.
            If there are no articles provided, respond with a clear message indicating no articles are available
            for trend analysis, and suggest what types of articles would be helpful to analyze in the future.
            """,
            tools=[],  # No tools needed for this agent
            verbose=verbose,
            model=model,
            temperature=temperature
        )
        
        logger.info("TrendAgent initialized")
    
    def _process_output(self, output: str) -> TrendOutput:
        """Process the agent output into the proper format."""
        import json
        import re
        
        try:
            # Try to parse as JSON first
            data = json.loads(output)
            trends = []
            
            for t in data.get("trends", []):
                trends.append(Trend(
                    name=t.get("name", ""),
                    description=t.get("description", ""),
                    strength=t.get("strength", "Emerging"),
                    supporting_articles=t.get("supporting_articles", []),
                    timeframe=t.get("timeframe", "Short-term")
                ))
            
            return TrendOutput(
                trends=trends,
                meta_trends=data.get("meta_trends", []),
                summary=data.get("summary", "")
            )
        except:
            # If not JSON, try to extract information from text
            trends = []
            
            # Try to find trend sections
            trend_pattern = r"(?:Trend|TREND)\s*(?:\d+)?:\s*(.*?)(?:\n|$)"
            description_pattern = r"(?:Description|DESCRIPTION):\s*(.*?)(?:\n\n|\n(?:Strength|Trend|Articles|Timeframe)|$)"
            strength_pattern = r"(?:Strength|STRENGTH):\s*(.*?)(?:\n|$)"
            articles_pattern = r"(?:Supporting Articles|SUPPORTING ARTICLES|Articles|ARTICLES):\s*(.*?)(?:\n\n|\n(?:Timeframe|Trend)|$)"
            timeframe_pattern = r"(?:Timeframe|TIMEFRAME):\s*(.*?)(?:\n|$)"
            
            trends_matches = re.finditer(trend_pattern, output, re.DOTALL)
            
            for trend_match in trends_matches:
                name = trend_match.group(1).strip()
                pos = trend_match.end()
                
                # Find description
                description_match = re.search(description_pattern, output[pos:pos+1000], re.DOTALL)
                description = description_match.group(1).strip() if description_match else ""
                
                # Find strength
                strength_match = re.search(strength_pattern, output[pos:pos+500])
                strength = strength_match.group(1).strip() if strength_match else "Emerging"
                
                # Find supporting articles
                supporting_articles = []
                articles_match = re.search(articles_pattern, output[pos:pos+1000], re.DOTALL)
                if articles_match:
                    articles_text = articles_match.group(1).strip()
                    supporting_articles = [a.strip() for a in re.split(r',|\n-', articles_text) if a.strip()]
                
                # Find timeframe
                timeframe_match = re.search(timeframe_pattern, output[pos:pos+500])
                timeframe = timeframe_match.group(1).strip() if timeframe_match else "Short-term"
                
                trends.append(Trend(
                    name=name,
                    description=description,
                    strength=strength,
                    supporting_articles=supporting_articles,
                    timeframe=timeframe
                ))
            
            # Extract meta-trends
            meta_trends = []
            meta_trends_match = re.search(r"(?:Meta[- ]Trends|META[- ]TRENDS):(.*?)(?:\n\n|$)", output, re.DOTALL | re.IGNORECASE)
            if meta_trends_match:
                meta_trends_text = meta_trends_match.group(1).strip()
                meta_trends = [m.strip() for m in re.split(r'\n-|\n\d+\.', meta_trends_text) if m.strip()]
            
            # Extract summary
            summary_match = re.search(r"(?:Summary|SUMMARY):(.*?)(?:$)", output, re.DOTALL | re.IGNORECASE)
            summary = summary_match.group(1).strip() if summary_match else output
            
            return TrendOutput(
                trends=trends,
                meta_trends=meta_trends,
                summary=summary
            )

    async def run(self, input_data: TrendInput) -> TrendOutput:
        """
        Run the trend agent to identify patterns and trends.
        
        Args:
            input_data: The input parameters
            
        Returns:
            Identified trends and analysis
        """
        # Log input data details
        logger.info(f"Running TrendAgent for category: {input_data.category}")
        logger.info(f"Received {len(input_data.articles)} articles for trend analysis")
        
        if len(input_data.articles) == 0:
            logger.warning("No articles provided for trend analysis")
            return TrendOutput(
                trends=[],
                meta_trends=[],
                summary="It seems there are no news articles provided at the moment. To perform trend analysis, I would need a collection of news articles related to similar topics or themes. With proper data, I could identify emerging patterns, assess their strength, and provide insights on how these trends might evolve over time."
            )
        
        if len(input_data.articles) < 3:
            logger.warning(f"Received only {len(input_data.articles)} articles - limited trend analysis possible")
        
        # Log article titles to help with debugging
        for i, article in enumerate(input_data.articles):
            title = article.get("title", "No title")
            source = article.get("source", "Unknown")
            logger.info(f"Article {i+1}: {title[:50]}... (source: {source})")
        
        # Continue with regular processing
        return await super().run(input_data) 