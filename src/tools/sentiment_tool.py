"""Sentiment analysis tool for news articles."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import openai
import os
from src.config import get_logger, OPENAI_API_KEY, MODEL_NAME, MODEL

logger = get_logger(__name__)

class SentimentInput(BaseModel):
    """Input schema for sentiment analysis."""
    
    text: str = Field(
        description="The text to analyze for sentiment"
    )
    include_explanation: bool = Field(
        default=True,
        description="Whether to include an explanation for the sentiment score"
    )

class SentimentTool:
    """Tool for analyzing sentiment in text using OpenAI."""
    
    def __init__(self):
        """Initialize the sentiment analysis tool."""
        self.api_key = OPENAI_API_KEY
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
    
    def run(self, input_data: SentimentInput) -> Dict[str, Any]:
        """
        Analyze the sentiment of the provided text.
        
        Args:
            input_data: The input parameters for sentiment analysis
            
        Returns:
            A dictionary containing sentiment analysis results
        """
        logger.info(f"Analyzing sentiment of text ({len(input_data.text)} chars)")
        
        if not self.api_key:
            logger.error("Cannot analyze sentiment: OPENAI_API_KEY not found")
            return {
                "score": 0,
                "sentiment": "neutral",
                "explanation": "Error: API key not found"
            }
        
        try:
            # Prepare the prompt
            system_prompt = """
            You are a sentiment analysis expert. Analyze the sentiment of the provided text 
            and return a JSON with the following fields:
            - score: a number from -1.0 (very negative) to 1.0 (very positive)
            - sentiment: one of "very negative", "negative", "slightly negative", 
                         "neutral", "slightly positive", "positive", "very positive"
            - explanation: a brief explanation of why you gave this score (if requested)
            """
            
            # Truncate text if it's too long
            max_length = 1000
            text = input_data.text[:max_length] if len(input_data.text) > max_length else input_data.text
            
            # Set up the client
            client = openai.OpenAI(api_key=self.api_key)
            
            # Get model configuration
            model = MODEL_NAME
            temperature = MODEL.get("temperature", 0)
            timeout = MODEL.get("timeout", 30)
            
            logger.debug(f"Using model {model} for sentiment analysis (temp: {temperature})")
            
            # Make the API request
            response = client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze the sentiment of this text: {text}"}
                ],
                temperature=0,  # Use 0 for deterministic responses in sentiment analysis
                timeout=timeout
            )
            
            # Extract and parse the result
            result = response.choices[0].message.content
            import json
            sentiment_data = json.loads(result)
            
            # Log the result
            logger.info(f"Sentiment analysis complete: {sentiment_data['sentiment']}")
            
            # Return the sentiment data
            return {
                "score": sentiment_data.get("score", 0),
                "sentiment": sentiment_data.get("sentiment", "neutral"),
                "explanation": sentiment_data.get("explanation", "") if input_data.include_explanation else ""
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {
                "score": 0,
                "sentiment": "neutral",
                "explanation": f"Error: {str(e)}"
            }

# Create the tool instance
sentiment_tool = SentimentTool() 