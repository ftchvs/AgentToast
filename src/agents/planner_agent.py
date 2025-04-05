from typing import Dict, Any, List
from .base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    """Agent responsible for planning news processing strategy."""
    
    def plan_and_act(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Plan the news processing strategy.
        
        Args:
            task: Dictionary containing initial parameters
            
        Returns:
            Dictionary containing the processing plan
        """
        # Get task parameters
        count = task.get('count', 5)
        categories = task.get('categories', [])
        
        # Create a plan using OpenAI
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a news processing planner. Create a strategy for processing "
                    "news articles effectively. Consider article relevance, content quality, "
                    "and audience engagement."
                )
            },
            {
                "role": "user",
                "content": f"Create a plan to process {count} news articles"
                f"{' in categories: ' + ', '.join(categories) if categories else ''}"
            }
        ]
        
        plan = self._call_openai_api(messages)
        
        # Structure the plan
        return {
            'plan': plan,
            'steps': [
                {
                    'step': 1,
                    'action': 'fetch',
                    'params': {'count': count, 'categories': categories}
                },
                {
                    'step': 2,
                    'action': 'analyze',
                    'params': {'check_relevance': True, 'verify_facts': True}
                },
                {
                    'step': 3,
                    'action': 'summarize',
                    'params': {'style': 'concise', 'tone': 'neutral'}
                },
                {
                    'step': 4,
                    'action': 'audio',
                    'params': {'voice': task.get('voice', 'alloy')}
                }
            ]
        } 