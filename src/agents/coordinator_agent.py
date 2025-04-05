"""Coordinator agent that orchestrates the multi-agent news workflow."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import logging
import asyncio

from agents import function_tool
from src.agents.base_agent import BaseAgent
from src.agents.example_agent import NewsAgent, NewsRequest, NewsSummary
from src.agents.writer_agent import WriterAgent, WriterInput
from src.agents.analyst_agent import AnalystAgent, AnalystInput
from src.agents.fact_checker_agent import FactCheckerAgent, FactCheckerInput
from src.agents.trend_agent import TrendAgent, TrendInput
from src.config import get_logger
from src.utils.tts import text_to_speech

logger = get_logger(__name__)

class CoordinatorInput(BaseModel):
    """Input for the coordinator agent."""
    
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
    analysis_depth: Optional[str] = Field(
        description="Depth of analysis (basic, moderate, deep)",
        default="moderate"
    )
    use_fact_checker: bool = Field(
        description="Whether to use the fact checker agent",
        default=True
    )
    use_trend_analyzer: bool = Field(
        description="Whether to use the trend analyzer agent",
        default=True
    )
    max_fact_claims: int = Field(
        description="Maximum number of fact claims to check",
        default=5
    )

class AgentResult(BaseModel):
    """Result from a single agent."""
    
    agent_name: str = Field(description="Name of the agent")
    success: bool = Field(description="Whether the agent completed successfully")
    data: Dict[str, Any] = Field(description="Output data from the agent", default_factory=dict)
    error: Optional[str] = Field(description="Error message if the agent failed", default=None)

class CoordinatorOutput(BaseModel):
    """Output from the coordinator agent."""
    
    news_summary: Optional[str] = Field(description="Summary of the news")
    audio_file: Optional[str] = Field(description="Path to the generated audio file")
    markdown: Optional[str] = Field(description="Full markdown output")
    analysis: Optional[str] = Field(description="Analysis of the news")
    fact_check: Optional[str] = Field(description="Fact check results")
    trends: Optional[str] = Field(description="Identified trends")
    agent_results: List[AgentResult] = Field(description="Results from individual agents", default_factory=list)

class CoordinatorAgent:
    """Agent that coordinates the multi-agent news workflow."""
    
    def __init__(self, verbose: bool = False, model: str = None, temperature: float = None):
        """Initialize the coordinator agent."""
        self.verbose = verbose
        self.model = model
        self.temperature = temperature
        logger.info("CoordinatorAgent initialized")
    
    async def run(self, input_data: CoordinatorInput) -> CoordinatorOutput:
        """
        Run the multi-agent news workflow.
        
        Args:
            input_data: The input parameters
            
        Returns:
            A comprehensive output with results from all agents
        """
        agent_results = []
        
        # Step 1: Fetch and summarize news articles with the NewsAgent
        try:
            logger.info(f"Starting NewsAgent for category: {input_data.category}")
            news_agent = NewsAgent(
                verbose=self.verbose,
                model=self.model,
                temperature=self.temperature
            )
            
            news_input = NewsRequest(
                category=input_data.category,
                count=input_data.count,
                country=input_data.country,
                sources=input_data.sources,
                query=input_data.query,
                voice=input_data.voice,
                # Disable audio generation here - we'll handle it at the end
                generate_audio=False
            )
            
            news_result = await news_agent.run(news_input)
            
            agent_results.append(AgentResult(
                agent_name="NewsAgent",
                success=True,
                data={
                    "category": news_result.category,
                    "article_count": news_result.article_count,
                    "summary": news_result.summary
                }
            ))
            
            # Prepare data for other agents
            articles_data = [
                {
                    "title": article.title,
                    "description": article.description,
                    "source": article.source,
                    "url": article.url,
                    "published_at": article.published_at
                }
                for article in news_result.articles
            ]
            
        except Exception as e:
            logger.error(f"Error in NewsAgent: {str(e)}")
            agent_results.append(AgentResult(
                agent_name="NewsAgent",
                success=False,
                error=str(e)
            ))
            # Return early if news fetching fails
            return CoordinatorOutput(agent_results=agent_results)
        
        # Tasks for parallel execution
        tasks = []
        
        # Step 2: Run the AnalystAgent to analyze the news
        if input_data.analysis_depth:
            tasks.append(self._run_analyst_agent(
                category=news_result.category, 
                articles=articles_data, 
                summary=news_result.summary, 
                depth=input_data.analysis_depth
            ))
        
        # Step 3: Run the FactCheckerAgent if enabled
        if input_data.use_fact_checker:
            tasks.append(self._run_fact_checker_agent(
                articles=articles_data, 
                summary=news_result.summary, 
                max_claims=input_data.max_fact_claims
            ))
        
        # Step 4: Run the TrendAgent if enabled
        if input_data.use_trend_analyzer:
            tasks.append(self._run_trend_agent(
                category=news_result.category, 
                articles=articles_data
            ))
        
        # Execute all tasks in parallel
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error in one of the agent tasks: {str(result)}")
                    continue
                agent_results.append(result)
        
        # Step 5: Run the WriterAgent to create the final audio summary
        audio_file = None
        try:
            if input_data.generate_audio:
                logger.info(f"Creating audio summary with voice: {input_data.voice}")
                
                # Get fact-checking and analysis results if available
                fact_check_summary = None
                analysis_insights = None
                trends_summary = None
                
                for result in agent_results:
                    if result.agent_name == "FactCheckerAgent" and result.success:
                        fact_check_summary = result.data.get("summary")
                    elif result.agent_name == "AnalystAgent" and result.success:
                        analysis_insights = result.data.get("insights")
                    elif result.agent_name == "TrendAgent" and result.success:
                        trends_summary = result.data.get("summary")
                
                # Create an enhanced context for the writer
                context = f"""
                News Summary: {news_result.summary}
                
                {f"Fact Check: {fact_check_summary}" if fact_check_summary else ""}
                
                {f"Analysis: {analysis_insights}" if analysis_insights else ""}
                
                {f"Trends: {trends_summary}" if trends_summary else ""}
                """
                
                writer_agent = WriterAgent(
                    verbose=self.verbose,
                    model=self.model,
                    temperature=self.temperature
                )
                
                writer_input = WriterInput(
                    category=news_result.category,
                    articles=articles_data,
                    max_length=600,  # Target length for TTS
                    style=input_data.summary_style,
                    additional_context=context  # Pass the context to the writer agent
                )
                
                writer_result = await writer_agent.run(writer_input)
                
                agent_results.append(AgentResult(
                    agent_name="WriterAgent",
                    success=True,
                    data={
                        "summary": writer_result.summary
                    }
                ))
                
                # Generate the audio file
                audio_file = text_to_speech(
                    text=writer_result.summary,
                    voice=input_data.voice
                )
                
                if audio_file:
                    logger.info(f"Generated audio file: {audio_file}")
                
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            agent_results.append(AgentResult(
                agent_name="WriterAgent",
                success=False,
                error=str(e)
            ))
        
        # Prepare the final output
        analysis = None
        fact_check = None
        trends = None
        
        for result in agent_results:
            if result.agent_name == "AnalystAgent" and result.success:
                analysis = result.data.get("insights")
            elif result.agent_name == "FactCheckerAgent" and result.success:
                fact_check = result.data.get("summary")
            elif result.agent_name == "TrendAgent" and result.success:
                trends = result.data.get("summary")
        
        return CoordinatorOutput(
            news_summary=news_result.summary,
            audio_file=audio_file,
            markdown=news_result.markdown,
            analysis=analysis,
            fact_check=fact_check,
            trends=trends,
            agent_results=agent_results
        )
    
    async def _run_analyst_agent(self, category: str, articles: List[Dict], summary: str, depth: str) -> AgentResult:
        """Run the analyst agent and return its result."""
        try:
            logger.info(f"Starting AnalystAgent with depth: {depth}")
            analyst_agent = AnalystAgent(
                verbose=self.verbose,
                model=self.model,
                temperature=self.temperature
            )
            
            analyst_input = AnalystInput(
                category=category,
                articles=articles,
                summary=summary,
                depth=depth
            )
            
            analyst_result = await analyst_agent.run(analyst_input)
            
            return AgentResult(
                agent_name="AnalystAgent",
                success=True,
                data={
                    "insights": analyst_result.insights,
                    "trends": analyst_result.trends,
                    "implications": analyst_result.implications
                }
            )
            
        except Exception as e:
            logger.error(f"Error in AnalystAgent: {str(e)}")
            return AgentResult(
                agent_name="AnalystAgent",
                success=False,
                error=str(e)
            )
    
    async def _run_fact_checker_agent(self, articles: List[Dict], summary: str, max_claims: int) -> AgentResult:
        """Run the fact checker agent and return its result."""
        try:
            logger.info(f"Starting FactCheckerAgent with max claims: {max_claims}")
            fact_checker_agent = FactCheckerAgent(
                verbose=self.verbose,
                model=self.model,
                temperature=self.temperature
            )
            
            fact_checker_input = FactCheckerInput(
                articles=articles,
                summary=summary,
                max_claims=max_claims
            )
            
            fact_checker_result = await fact_checker_agent.run(fact_checker_input)
            
            return AgentResult(
                agent_name="FactCheckerAgent",
                success=True,
                data={
                    "verifications": [v.dict() for v in fact_checker_result.verifications],
                    "summary": fact_checker_result.summary
                }
            )
            
        except Exception as e:
            logger.error(f"Error in FactCheckerAgent: {str(e)}")
            return AgentResult(
                agent_name="FactCheckerAgent",
                success=False,
                error=str(e)
            )
    
    async def _run_trend_agent(self, category: str, articles: List[Dict]) -> AgentResult:
        """Run the trend agent and return its result."""
        try:
            logger.info(f"Starting TrendAgent for category: {category}")
            trend_agent = TrendAgent(
                verbose=self.verbose,
                model=self.model,
                temperature=self.temperature
            )
            
            trend_input = TrendInput(
                category=category,
                articles=articles
            )
            
            trend_result = await trend_agent.run(trend_input)
            
            return AgentResult(
                agent_name="TrendAgent",
                success=True,
                data={
                    "trends": [t.dict() for t in trend_result.trends],
                    "meta_trends": trend_result.meta_trends,
                    "summary": trend_result.summary
                }
            )
            
        except Exception as e:
            logger.error(f"Error in TrendAgent: {str(e)}")
            return AgentResult(
                agent_name="TrendAgent",
                success=False,
                error=str(e)
            ) 