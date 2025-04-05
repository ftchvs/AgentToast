from typing import List, Dict, Any
from openai import OpenAI
from newsapi import NewsApiClient
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class NewsAgent:
    """Agent responsible for fetching and processing news articles."""
    
    def __init__(self):
        """Initialize the NewsAgent with API clients."""
        self.news_api = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def fetch_top_news(self, count: int = 5) -> List[Dict[str, Any]]:
        """Fetch top news articles from NEWS API.
        
        Args:
            count: Number of articles to fetch (default: 5)
            
        Returns:
            List of news articles with title and content
        """
        # Get yesterday's date for better article coverage
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        try:
            top_headlines = self.news_api.get_top_headlines(
                language='en',
                from_param=yesterday,
                page_size=count
            )
            
            if not top_headlines['articles']:
                raise ValueError("No articles found")
                
            return top_headlines['articles']
            
        except Exception as e:
            print(f"Error fetching news: {str(e)}")
            return []
            
    def generate_summary(self, article: Dict[str, Any]) -> str:
        """Generate a concise summary of a news article using OpenAI.
        
        Args:
            article: News article dictionary containing title and content
            
        Returns:
            Summarized version of the article
        """
        try:
            # Combine title and content for context
            content = f"Title: {article['title']}\n\nContent: {article['description']}"
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional news summarizer. Create a concise, clear summary of the news article in 2-3 sentences."},
                    {"role": "user", "content": content}
                ]
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return ""
            
    def generate_audio(self, text: str) -> bytes:
        """Convert text summary to audio using OpenAI's text-to-speech.
        
        Args:
            text: Text content to convert to speech
            
        Returns:
            Audio data in bytes
        """
        try:
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            
            return response.content
            
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            return b"" 