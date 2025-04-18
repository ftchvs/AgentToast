"""Analyst agent for providing deeper insights on news articles."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
import json
import re

from src.agents.base_agent import BaseAgent
from src.config import get_logger
from agents import WebSearchTool

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
    financial_data: Optional[Dict] = Field(
        description="Optional financial data dictionary for the ticker, if requested.",
        default=None
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
    confidence: Optional[str] = Field(
        description="Confidence level in the analysis",
        default=None
    )

class AnalystAgent(BaseAgent[AnalystInput, AnalystOutput]):
    """Agent that analyzes news articles to provide deeper insights."""
    
    DEFAULT_INSTRUCTIONS = ("""
You are an expert News Analyst AI. Your task is to analyze the provided news articles, summary,
and optional financial data, considering the requested analysis depth.

Your goal is to identify:
1.  **Key Insights:** What are the most important takeaways or hidden meanings in the news?
2.  **Potential Trends:** What broader patterns or shifts might this news indicate?
3.  **Implications:** What are the potential consequences or effects of these events?

**Use the provided WebSearchTool** to find additional context, verify information from the articles against broader sources, or gather supporting data for your analysis, especially for deeper analysis depths.

Structure your output clearly, focusing on actionable or significant observations.
If financial data is provided, incorporate it into your analysis regarding market impact or company performance.

Format your final output as a single JSON object with a single key 'analysis' containing your full analysis as a well-formatted markdown string.
""")

    def __init__(self, verbose: bool = False, model: str = None, temperature: float = None):
        """Initialize the analyst agent."""
        
        super().__init__(
            name="AnalystAgent",
            instructions=self.DEFAULT_INSTRUCTIONS,
            tools=[WebSearchTool()],
            verbose=verbose,
            model=model,
            temperature=temperature
        )
        
        self.logger = get_logger("agent.analyst")
    
    def _process_output(self, output: str) -> AnalystOutput:
        """Process the agent output into the proper format."""
        try:
            # Try to parse as JSON first
            data = json.loads(output)
            return AnalystOutput(
                insights=data.get("insights", ""),
                trends=data.get("trends", []),
                implications=data.get("implications", []),
                confidence=data.get("confidence", None)
            )
        except json.JSONDecodeError:
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
            
            # If no specific sections found, use the whole output as insights
            if not insights:
                insights = output.strip()

            return AnalystOutput(
                insights=insights,
                trends=trends,
                implications=implications,
                confidence=None
            )
        except Exception as e:
            self.logger.error(f"Error processing AnalystAgent output: {e}")
            # Return a default or error state
            return AnalystOutput(insights=f"Error processing output: {e}")

# Example Usage (if needed)
if __name__ == '__main__':
    import asyncio
    import re # Make sure re is imported for the example

    # Mock data
    mock_articles = [
        {"title": "Tech Layoffs Continue", "description": "Major tech firm announces cuts.", "source": "Tech News", "url": "http://example.com/1", "published_at": "..."},
        {"title": "AI Chip Demand Soars", "description": "Chipmakers see record profits.", "source": "Biz Journal", "url": "http://example.com/2", "published_at": "..."}
    ]
    mock_summary = "Tech industry sees layoffs alongside high demand for AI chips."

    async def run_analyst():
        agent = AnalystAgent(verbose=True, model='gpt-3.5-turbo') # Specify model for example
        input_data = AnalystInput(
            category="technology",
            articles=mock_articles,
            summary=mock_summary,
            depth="moderate"
        )
        result = await agent.run(input_data)
        print("\n--- Analyst Agent Output ---")
        print(f"Insights: {result.insights}")
        if result.trends:
            print(f"Trends: {result.trends}")
        if result.implications:
            print(f"Implications: {result.implications}")
        if result.confidence:
             print(f"Confidence: {result.confidence}")

    asyncio.run(run_analyst()) 
