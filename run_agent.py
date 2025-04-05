#!/usr/bin/env python3
"""
AgentToast Runner Script
This script provides a simple interface to run the news processing agents.
"""

import os
import asyncio
from dotenv import load_dotenv
from src.agents.fetcher_agent import FetcherAgent
from datetime import datetime
import json
import logging
from typing import Dict, Any, Optional
from src.agents.orchestrator_agent import OrchestratorAgent, NewsProcessingParams

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Available categories with descriptions
CATEGORIES = {
    'general': 'Top headlines and breaking news',
    'technology': 'Tech industry news and innovations',
    'business': 'Business and financial news',
    'politics': 'Political news and government affairs',
    'science': 'Scientific discoveries and research',
    'health': 'Healthcare and medical news',
    'entertainment': 'Entertainment and media news',
    'sports': 'Sports news and updates'
}

def print_menu():
    """Print the main menu options."""
    print("\nNews Processing Demo")
    print("1. Basic news processing (5 general articles)")
    print("2. Category-specific news")
    print("3. Custom news feeds")
    print("4. Exit")

def print_categories():
    """Print available news categories."""
    print("\nAvailable Categories:")
    print("1. General: Top headlines from various categories")
    print("2. Technology: Tech news and updates")
    print("3. Business: Business and financial news")
    print("4. Science: Scientific discoveries and research")
    print("5. Health: Health and medical news")
    print("6. Entertainment: Entertainment and celebrity news")
    print("7. Sports: Sports news and updates")

def get_category_name(choice: int) -> str:
    """Get the category name from user choice."""
    categories = {
        1: 'general',
        2: 'technology',
        3: 'business',
        4: 'science',
        5: 'health',
        6: 'entertainment',
        7: 'sports'
    }
    return categories.get(choice, 'general')

def save_traces(result: dict):
    """Save traces to a JSON file."""
    if not result.get('trace'):
        return
        
    # Create traces directory if it doesn't exist
    os.makedirs("traces", exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"traces/trace_{timestamp}.json"
    
    # Export traces to JSON
    with open(filename, "w") as f:
        json.dump(result['trace'], f, indent=2)
    print(f"\nTraces saved to: {filename}")

def save_results(results: Dict[str, Any], category: str) -> None:
    """Save processing results to a JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"results_{category}_{timestamp}.json"
    
    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")

async def process_news(category: str, count: int = 5, max_summary_length: int = 200) -> Optional[Dict[str, Any]]:
    """Process news articles for a given category."""
    try:
        orchestrator = OrchestratorAgent()
        params = NewsProcessingParams(
            category=category,
            count=count,
            max_summary_length=max_summary_length
        )
        
        logger.info(f"Processing news for category: {category}")
        result = await orchestrator.process_news(params)
        
        # Convert ProcessingResult to dict for saving
        result_dict = result.model_dump()
        save_results(result_dict, category)
        return result_dict
            
    except Exception as e:
        logger.error(f"Error in process_news: {str(e)}")
        return None

async def main():
    """Main function to run the news processing demo."""
    load_dotenv()
    
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY not found in environment variables")
        return
        
    if not os.getenv('NEWS_API_KEY'):
        print("Error: NEWS_API_KEY not found in environment variables")
        return
    
    fetcher = FetcherAgent()
    
    while True:
        print_menu()
        try:
            choice = int(input("\nEnter your choice (1-4): "))
            
            if choice == 4:
                print("Exiting...")
                break
                
            elif choice == 1:
                # Basic news processing
                results = await process_news('general')
                if results:
                    print("\nProcessed general news articles:")
                    for summary in results['summaries']:
                        print(f"\nTitle: {summary['title']}")
                        print(f"Summary: {summary['summary']}")
                        print(f"Source: {summary['source']}")
                        print(f"URL: {summary['url']}")
                    print(f"\nStats: {results['total_fetched']} fetched, {results['total_verified']} verified, {results['total_rejected']} rejected")
                    print(f"Average summary length: {results['avg_summary_length']:.1f} characters")
                
            elif choice == 2:
                # Category-specific news
                print_categories()
                category_choice = int(input("\nSelect a category (1-7): "))
                category = get_category_name(category_choice)
                results = await process_news(category)
                if results:
                    print(f"\nProcessed {category} news articles:")
                    for summary in results['summaries']:
                        print(f"\nTitle: {summary['title']}")
                        print(f"Summary: {summary['summary']}")
                        print(f"Source: {summary['source']}")
                        print(f"URL: {summary['url']}")
                    print(f"\nStats: {results['total_fetched']} fetched, {results['total_verified']} verified, {results['total_rejected']} rejected")
                    print(f"Average summary length: {results['avg_summary_length']:.1f} characters")
                
            elif choice == 3:
                # Custom news feeds
                print_categories()
                print("Enter category numbers separated by commas (e.g., 1,3,5)")
                category_choices = input("\nSelect categories: ").split(',')
                
                categories = [get_category_name(int(c)) for c in category_choices]
                count_per_category = int(input("Enter number of articles per category: "))
                
                for category in categories:
                    results = await process_news(category, count_per_category)
                    if results:
                        print(f"\nProcessed {category} news articles:")
                        for summary in results['summaries']:
                            print(f"\nTitle: {summary['title']}")
                            print(f"Summary: {summary['summary']}")
                            print(f"Source: {summary['source']}")
                            print(f"URL: {summary['url']}")
                        print(f"\nStats: {results['total_fetched']} fetched, {results['total_verified']} verified, {results['total_rejected']} rejected")
                        print(f"Average summary length: {results['avg_summary_length']:.1f} characters")
            
        except ValueError:
            print("Invalid input. Please enter a number.")
        except Exception as e:
            print(f"Error in news processing: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation interrupted by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print("\nAn unexpected error occurred. Please check the logs for details.") 