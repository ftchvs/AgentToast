"""Fact checker agent for verifying claims in news articles."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import logging
import json

from agents import function_tool, WebSearchTool
from src.agents.base_agent import BaseAgent
from src.config import get_logger

logger = get_logger(__name__)

class Claim(BaseModel):
    """Model for a fact claim."""
    
    text: str = Field(description="The text of the claim")
    source: str = Field(description="Source of the claim (e.g., article title)")
    
class FactCheckerInput(BaseModel):
    """Input for the fact checker agent."""
    
    articles: List[dict] = Field(
        description="List of news articles with title, description, source, url and published_at",
    )
    summary: str = Field(
        description="The summary text that might contain claims to verify",
    )
    max_claims: int = Field(
        description="Maximum number of claims to verify",
        default=5
    )

class VerificationResult(BaseModel):
    """Result of a single fact verification."""
    
    claim: str = Field(description="The claim that was checked")
    assessment: str = Field(description="Assessment of the claim (Verified, Unverified, Misleading, False, Needs Context)")
    explanation: str = Field(description="Explanation of the assessment")
    confidence: str = Field(description="Confidence level (Low, Medium, High)")
    sources: List[str] = Field(description="Sources consulted for verification", default_factory=list)

class FactCheckerOutput(BaseModel):
    """Output from the fact checker agent."""
    
    verifications: List[VerificationResult] = Field(
        description="List of verification results",
        default_factory=list
    )
    summary: str = Field(
        description="Summary of fact-checking results"
    )

class FactCheckerAgent(BaseAgent[FactCheckerInput, FactCheckerOutput]):
    """Agent that verifies factual claims in news articles."""
    
    DEFAULT_INSTRUCTIONS = (
        "You are a meticulous Fact Checker AI. Your goal is to identify key factual claims presented "
        "in the provided news articles or summary and verify their accuracy. "
        "Use the provided web search tool to find corroborating or conflicting evidence from reliable sources. "
        "For each significant claim you identify (up to the specified maximum):\n"
        "1. Clearly state the claim.\n"
        "2. Briefly explain the verification process (e.g., 'Searched for [query]', 'Compared with [source]').\n"
        "3. Assess the claim as 'Verified', 'Needs Context', or 'Unverified'.\n"
        "4. Provide a concise explanation for your assessment, citing sources found using the web search tool where possible.\n"
        "5. Rate your confidence level in the assessment (High, Medium, Low).\n"
        "Finally, provide a brief overall summary of your findings.\n"
        "Focus on objective, verifiable facts, not opinions or subjective statements."
    )

    def __init__(self, verbose: bool = False, model: str = None, temperature: float = None):
        """Initialize the fact checker agent."""
        
        super().__init__(
            name="FactCheckerAgent",
            instructions=self.DEFAULT_INSTRUCTIONS,
            tools=[WebSearchTool()],
            verbose=verbose,
            model=model,
            temperature=temperature
        )
        
        # Override logger
        self.logger = get_logger("agent.fact_checker")
        
        logger.info("FactCheckerAgent initialized")
    
    def _process_output(self, output: str) -> FactCheckerOutput:
        """Process the agent output into the proper format."""
        import re
        
        try:
            # Try to parse as JSON first
            data = json.loads(output)
            verifications = []
            for v in data.get("verifications", []):
                verifications.append(VerificationResult(
                    claim=v.get("claim", ""),
                    assessment=v.get("assessment", "Unverified"),
                    explanation=v.get("explanation", ""),
                    confidence=v.get("confidence", "Low"),
                    sources=v.get("sources", [])
                ))
            
            return FactCheckerOutput(
                verifications=verifications,
                summary=data.get("summary", "")
            )
        except:
            # If not JSON, try to extract information from text
            verifications = []
            
            # Try to find claim sections
            claim_pattern = r"(?:Claim|CLAIM)\s*(?:\d+)?:\s*(.*?)(?:\n|$)"
            assessment_pattern = r"(?:Assessment|ASSESSMENT):\s*(.*?)(?:\n|$)"
            explanation_pattern = r"(?:Explanation|EXPLANATION):\s*(.*?)(?:\n\n|\n(?:Claim|Confidence)|$)"
            confidence_pattern = r"(?:Confidence|CONFIDENCE):\s*(.*?)(?:\n|$)"
            sources_pattern = r"(?:Sources|SOURCES):\s*(.*?)(?:\n\n|\n(?:Claim)|$)"
            
            claims = re.finditer(claim_pattern, output, re.DOTALL)
            
            for claim_match in claims:
                claim = claim_match.group(1).strip()
                pos = claim_match.end()
                
                # Find assessment
                assessment_match = re.search(assessment_pattern, output[pos:pos+500])
                assessment = assessment_match.group(1).strip() if assessment_match else "Unverified"
                
                # Find explanation
                explanation_match = re.search(explanation_pattern, output[pos:pos+1000], re.DOTALL)
                explanation = explanation_match.group(1).strip() if explanation_match else ""
                
                # Find confidence
                confidence_match = re.search(confidence_pattern, output[pos:pos+500])
                confidence = confidence_match.group(1).strip() if confidence_match else "Low"
                
                # Find sources
                sources = []
                sources_match = re.search(sources_pattern, output[pos:pos+500], re.DOTALL)
                if sources_match:
                    sources_text = sources_match.group(1).strip()
                    sources = [s.strip() for s in re.split(r',|\n-', sources_text) if s.strip()]
                
                verifications.append(VerificationResult(
                    claim=claim,
                    assessment=assessment,
                    explanation=explanation,
                    confidence=confidence,
                    sources=sources
                ))
            
            # Extract summary
            summary_match = re.search(r"(?:Summary|SUMMARY):(.*?)(?:$)", output, re.DOTALL | re.IGNORECASE)
            summary = summary_match.group(1).strip() if summary_match else output
            
            return FactCheckerOutput(
                verifications=verifications,
                summary=summary
            ) 
