import os
from pathlib import Path
from datetime import datetime
from agents.orchestrator_agent import OrchestratorAgent

def create_output_directory() -> Path:
    """Create and return the output directory for audio files."""
    output_dir = Path("output") / datetime.now().strftime("%Y-%m-%d")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def main():
    """Main function to process news and generate audio summaries."""
    try:
        # Initialize the orchestrator agent
        agent = OrchestratorAgent()
        
        # Define the task parameters
        task = {
            'count': 5,  # Number of articles to process
            'categories': None,  # Optional list of categories
            'voice': 'alloy'  # Voice to use for audio
        }
        
        # Execute the processing pipeline
        result = agent.plan_and_act(task)
        
        if result['status'] == 'error':
            print(f"Error: {result['message']}")
            return
            
        # Print results
        print(f"\nProcessing Summary:")
        print(f"- Articles processed: {result['processed_count']} out of {result['total_count']}")
        print(f"\nDetailed Results:")
        
        for item in result['results']:
            print("\n" + "="*50)
            print(f"Title: {item['title']}")
            print(f"Quality Score: {item['quality_score']:.2f}")
            print(f"\nVerification Notes:")
            print(item['verification_notes'])
            print(f"\nSummary: {item['summary']}")
            print(f"\nAudio saved to: {item['audio_path']}")
            
        print("\nProcessing complete!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 