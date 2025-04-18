"""Coordinator agent that orchestrates the multi-agent news workflow."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import logging
import asyncio
import re

from agents import function_tool
from src.agents.base_agent import BaseAgent
from src.agents.example_agent import NewsAgent, NewsRequest, NewsSummary
from src.agents.writer_agent import WriterAgent, WriterInput
from src.agents.analyst_agent import AnalystAgent, AnalystInput
from src.agents.fact_checker_agent import FactCheckerAgent, FactCheckerInput
from src.agents.trend_agent import TrendAgent, TrendInput
from src.agents.finance_agent import FinanceAgent, FinanceInput, FinanceOutput, FinanceErrorOutput
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
    ticker_symbol: Optional[str] = Field(
        description="Optional stock ticker symbol to fetch financial data for (e.g., AAPL, GOOGL)",
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
    financial_data: Optional[Dict[str, Any]] = Field(description="Financial data for the requested ticker symbol", default=None)
    agent_results: List[AgentResult] = Field(description="Results from individual agents", default_factory=list)

class CoordinatorAgent:
    """Agent that coordinates the multi-agent news workflow."""
    
    def __init__(self, 
                 verbose: bool = False, 
                 model: str = None, 
                 temperature: float = None,
                 # Add model override arguments
                 news_model_override: Optional[str] = None,
                 analyst_model_override: Optional[str] = None,
                 factchecker_model_override: Optional[str] = None,
                 trend_model_override: Optional[str] = None,
                 writer_model_override: Optional[str] = None):
        """Initialize the coordinator agent."""
        self.verbose = verbose
        self.model = model # Default/fallback model
        self.temperature = temperature
        # Store overrides
        self.model_overrides = {
            "NewsAgent": news_model_override,
            "AnalystAgent": analyst_model_override,
            "FactCheckerAgent": factchecker_model_override,
            "TrendAgent": trend_model_override,
            "WriterAgent": writer_model_override
        }
        logger.info(f"CoordinatorAgent initialized with default model: {self.model}")
        active_overrides = {k: v for k, v in self.model_overrides.items() if v}
        if active_overrides:
            logger.info(f"  Model overrides: {active_overrides}")
    
    def _get_agent_model(self, agent_name: str) -> str:
        """Get the appropriate model for a given agent, considering overrides."""
        return self.model_overrides.get(agent_name) or self.model

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
            news_model = self._get_agent_model("NewsAgent")
            logger.info(f"  (Using model: {news_model})")
            news_agent = NewsAgent(
                verbose=self.verbose,
                model=news_model, # Use specific or fallback model
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
            
            # Log the article data to help with debugging
            logger.info(f"NewsAgent returned {len(news_result.articles)} articles for category: {news_result.category}")
            
            # Verify we have article data - if not, try to extract from markdown
            if not articles_data and news_result.markdown:
                logger.warning("No structured article data found, attempting to extract from markdown")
                
                # Try to match against the numbered article pattern first
                numbered_article_pattern = r"##\s+\d+\.\s+\[(.*?)\]\((.*?)\)"
                article_matches = list(re.finditer(numbered_article_pattern, news_result.markdown))
                
                if article_matches:
                    for i, match in enumerate(article_matches):
                        title = match.group(1).strip()
                        url = match.group(2).strip()
                        
                        # Get the text block between this article and the next one (or end of text)
                        start_pos = match.end()
                        end_pos = len(news_result.markdown)
                        if i + 1 < len(article_matches):
                            end_pos = article_matches[i + 1].start()
                        
                        block_text = news_result.markdown[start_pos:end_pos]
                        
                        # Extract metadata using specific patterns
                        source_match = re.search(r"\*\*Source:\*\*\s*(.*?)(?:\n|$)", block_text)
                        published_match = re.search(r"\*\*Published At:\*\*\s*(.*?)(?:\n|$)", block_text)
                        desc_match = re.search(r"- (.*?)(?:\n\n|$)", block_text)
                        
                        source = source_match.group(1).strip() if source_match else "Unknown source"
                        published_at = published_match.group(1).strip() if published_match else ""
                        description = desc_match.group(1).strip() if desc_match else "No description"
                        
                        articles_data.append({
                            "title": title,
                            "description": description,
                            "source": source,
                            "url": url,
                            "published_at": published_at
                        })
                else:
                    # If numbered pattern didn't work, try the "Article X" pattern
                    article_pattern = r"##\s+Article\s+\d+:\s+\[(.*?)\]\((.*?)\)"
                    article_matches = re.finditer(article_pattern, news_result.markdown)
                    
                    for match in article_matches:
                        title = match.group(1).strip()
                        url = match.group(2).strip()
                        # Extract description and source
                        block_start = match.end()
                        block_end = news_result.markdown.find("##", block_start)
                        if block_end == -1:
                            block_end = len(news_result.markdown)
                        block = news_result.markdown[block_start:block_end]
                        
                        desc_match = re.search(r"\*\*Description:?\*\*\s*(.*?)(?:\n|$)", block)
                        source_match = re.search(r"\*\*Source:?\*\*\s*(.*?)(?:\n|$)", block)
                        published_match = re.search(r"\*\*Published(?:\s+At)?:?\*\*\s*(.*?)(?:\n|$)", block)
                        
                        description = desc_match.group(1).strip() if desc_match else "No description"
                        source = source_match.group(1).strip() if source_match else "Unknown source"
                        published_at = published_match.group(1).strip() if published_match else ""
                        
                        articles_data.append({
                            "title": title,
                            "description": description,
                            "source": source,
                            "url": url,
                            "published_at": published_at
                        })
                    
                    # If still no articles, try parsing the entire markdown as a last resort
                    if not articles_data:
                        # Extract any lines that look like headlines with links
                        headline_matches = re.finditer(r'(?:##|###)\s+\d+\.\s+\[(.*?)\]\((.*?)\)', news_result.markdown)
                        for match in headline_matches:
                            title = match.group(1)
                            url = match.group(2)
                            
                            articles_data.append({
                                "title": title,
                                "description": "Extracted from headline",
                                "source": "Unknown source",
                                "url": url,
                                "published_at": ""
                            })
                
                logger.info(f"Extracted {len(articles_data)} articles from markdown content")
            
            agent_results.append(AgentResult(
                agent_name="NewsAgent",
                success=True,
                data={
                    "category": news_result.category,
                    "article_count": len(articles_data),  # Use actual count
                    "summary": news_result.summary
                }
            ))
            
        except Exception as e:
            logger.error(f"Error in NewsAgent: {str(e)}")
            agent_results.append(AgentResult(
                agent_name="NewsAgent",
                success=False,
                error=str(e)
            ))
            # If news fails, we can't proceed with analysis agents
            return CoordinatorOutput(agent_results=agent_results, error="Failed to retrieve news articles")

        # If NewsAgent succeeded and we have articles, proceed with other agents
        if agent_results[-1].success and articles_data:
            # Step 2: Run analysis agents concurrently (Analyst, FactChecker, Trend)
            analysis_tasks = []
            
            # Analyst Agent
            analysis_tasks.append(self._run_analyst_agent(
                category=news_result.category,
                articles=articles_data,
                summary=news_result.summary,
                depth=input_data.analysis_depth
            ))
            
            # Fact Checker Agent (optional)
            if input_data.use_fact_checker:
                analysis_tasks.append(self._run_fact_checker_agent(
                    articles=articles_data,
                    summary=news_result.summary,
                    max_claims=input_data.max_fact_claims
                ))
                
            # Trend Analyzer Agent (optional)
            if input_data.use_trend_analyzer:
                analysis_tasks.append(self._run_trend_agent(
                    category=news_result.category,
                    articles=articles_data
                ))
                
            # Run analysis tasks concurrently
            analysis_agent_outputs = await asyncio.gather(*analysis_tasks)
            agent_results.extend(analysis_agent_outputs)

            # --- Add FinanceAgent execution here ---
            finance_result_data = None
            if input_data.ticker_symbol:
                logger.info(f"Starting FinanceAgent for symbol: {input_data.ticker_symbol}")
                try:
                    finance_agent = FinanceAgent(verbose=self.verbose) # No model/temp needed
                    finance_input = FinanceInput(symbol=input_data.ticker_symbol)
                    finance_output = finance_agent.run_sync(finance_input) # Use run_sync
                    
                    if isinstance(finance_output, FinanceErrorOutput):
                        agent_results.append(AgentResult(
                            agent_name="FinanceAgent",
                            success=False,
                            error=finance_output.error
                        ))
                    else:
                        finance_result_data = finance_output.model_dump()
                        agent_results.append(AgentResult(
                            agent_name="FinanceAgent",
                            success=True,
                            data=finance_result_data
                        ))
                except Exception as e:
                    logger.error(f"Error running FinanceAgent for {input_data.ticker_symbol}: {e}")
                    agent_results.append(AgentResult(
                        agent_name="FinanceAgent",
                        success=False,
                        error=f"FinanceAgent failed: {str(e)}"
                    ))
            # ----------------------------------------

            # Step 3: Prepare context and run WriterAgent
            # Collect outputs from successful analysis agents
            analysis_context = ""
            fact_check_context = ""
            trend_context = ""
            
            for result in agent_results:
                if result.success:
                    if result.agent_name == "AnalystAgent":
                        analysis_context = result.data.get("insights", "")
                    elif result.agent_name == "FactCheckerAgent":
                        fact_check_context = result.data.get("summary", "")
                    elif result.agent_name == "TrendAgent":
                        trend_context = result.data.get("summary", "")
            
            # Combine context for the writer
            # TODO: Decide if/how to include finance_result_data in writer context
            combined_context = f"Original News Summary:\n{news_result.summary}\n\nAnalysis:\n{analysis_context}\n\nFact Check Summary:\n{fact_check_context}\n\nTrend Summary:\n{trend_context}"
            
            try:
                logger.info("Starting WriterAgent")
                writer_model = self._get_agent_model("WriterAgent")
                logger.info(f"  (Using model: {writer_model})")
                writer_agent = WriterAgent(
                    verbose=self.verbose,
                    model=writer_model, # Use specific or fallback model
                    temperature=self.temperature
                )
                writer_input = WriterInput(
                    context=combined_context,
                    summary_style=input_data.summary_style,
                    generate_audio=input_data.generate_audio,
                    voice=input_data.voice,
                    output_dir=None # Let the agent handle default/config
                )
                
                writer_result = await writer_agent.run(writer_input)
                
                agent_results.append(AgentResult(
                    agent_name="WriterAgent",
                    success=True,
                    data={
                        "final_summary": writer_result.final_summary,
                        "markdown_output": writer_result.markdown_output,
                        "audio_file": writer_result.audio_file
                    }
                ))
                
                # Step 4: Prepare final CoordinatorOutput
                final_output = CoordinatorOutput(
                    news_summary=writer_result.final_summary,
                    audio_file=writer_result.audio_file,
                    markdown=writer_result.markdown_output,
                    analysis=analysis_context,
                    fact_check=fact_check_context,
                    trends=trend_context,
                    financial_data=finance_result_data, # Include financial data here
                    agent_results=agent_results
                )
                
            except Exception as e:
                logger.error(f"Error in WriterAgent: {str(e)}")
                agent_results.append(AgentResult(
                    agent_name="WriterAgent",
                    success=False,
                    error=str(e)
                ))
                # Still return partial results if WriterAgent fails
                final_output = CoordinatorOutput(
                    analysis=analysis_context,
                    fact_check=fact_check_context,
                    trends=trend_context,
                    financial_data=finance_result_data,
                    agent_results=agent_results,
                    error="WriterAgent failed to generate final summary"
                )
                
        else:
            # Handle case where NewsAgent succeeded but found no articles
            error_message = "NewsAgent ran but could not find or extract articles."
            logger.warning(error_message)
            final_output = CoordinatorOutput(agent_results=agent_results, error=error_message)

        # Final logging of overall performance
        successful_agents = [r.agent_name for r in agent_results if r.success]
        failed_agents = [r.agent_name for r in agent_results if not r.success]
        logger.info(f"Coordinator run finished. Success: {successful_agents}, Failed: {failed_agents}")
        
        return final_output
    
    async def _run_analyst_agent(self, category: str, articles: List[Dict], summary: str, depth: str) -> AgentResult:
        """Run the analyst agent and return its result."""
        try:
            analyst_model = self._get_agent_model("AnalystAgent")
            logger.info(f"Starting AnalystAgent with depth: {depth} (Using model: {analyst_model})")
            analyst_agent = AnalystAgent(
                verbose=self.verbose,
                model=analyst_model, # Use specific or fallback model
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
            factchecker_model = self._get_agent_model("FactCheckerAgent")
            logger.info(f"Starting FactCheckerAgent with max claims: {max_claims} (Using model: {factchecker_model})")
            fact_checker_agent = FactCheckerAgent(
                verbose=self.verbose,
                model=factchecker_model, # Use specific or fallback model
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
            trend_model = self._get_agent_model("TrendAgent")
            logger.info(f"Starting TrendAgent for category: {category} (Using model: {trend_model})")
            
            # Check if articles list is empty or None
            if not articles:
                logger.warning("No articles provided to TrendAgent. Skipping trend analysis.")
                return AgentResult(
                    agent_name="TrendAgent",
                    success=False,
                    error="No articles provided for trend analysis"
                )
                
            trend_agent = TrendAgent(
                verbose=self.verbose,
                model=trend_model, # Use specific or fallback model
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
