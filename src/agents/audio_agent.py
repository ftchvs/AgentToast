from typing import Dict, Any, List
from .base_agent import BaseAgent
import openai

class AudioAgent(BaseAgent):
    """Agent responsible for generating audio from text."""
    
    def generate_audio(self, text: str, voice: str = "alloy") -> Dict[str, Any]:
        """Generate audio from text using OpenAI's text-to-speech.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (default: alloy)
            
        Returns:
            Dictionary containing audio data and metadata
        """
        try:
            with openai.trace(
                name=f"{self.__class__.__name__}.generate_audio",
                extra={
                    'text_length': len(text),
                    'voice': voice
                }
            ) as trace:
                response = self.openai_client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=text
                )
                
                result = {
                    'audio_data': response.content,
                    'format': 'mp3',
                    'voice': voice
                }
                
                trace.add_data({
                    'audio_generated': True,
                    'audio_size': len(response.content)
                })
                return result
                
        except Exception as e:
            if 'trace' in locals():
                trace.add_data({
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                })
            print(f"Error generating audio: {str(e)}")
            return {
                'error': str(e),
                'audio_data': None
            }
            
    def generate_audio_for_summaries(self, summaries: List[Dict[str, Any]], voice: str = "alloy") -> List[Dict[str, Any]]:
        """Generate audio for multiple summaries.
        
        Args:
            summaries: List of summary dictionaries
            voice: Voice to use (default: alloy)
            
        Returns:
            List of dictionaries containing audio data
        """
        try:
            with openai.trace(
                name=f"{self.__class__.__name__}.generate_audio_for_summaries",
                extra={
                    'summary_count': len(summaries),
                    'voice': voice
                }
            ) as trace:
                results = []
                for summary in summaries:
                    audio = self.generate_audio(summary['summary'], voice)
                    results.append({
                        'summary_id': summary.get('article_id', ''),
                        'audio_data': audio
                    })
                
                trace.add_data({
                    'audio_files_generated': len(results)
                })
                return results
                
        except Exception as e:
            if 'trace' in locals():
                trace.add_data({
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                })
            print(f"Error in batch audio generation: {str(e)}")
            return []
            
    def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the audio generation task.
        
        Args:
            task: Dictionary containing task parameters
            
        Returns:
            Dictionary containing audio results
        """
        with openai.trace(
            name=f"{self.__class__.__name__}._execute_task",
            extra=task
        ) as trace:
            summaries = task.get('summaries', [])
            voice = task.get('voice', 'alloy')
            
            results = self.generate_audio_for_summaries(summaries, voice)
            
            result = {
                'audio_results': results,
                'summaries_processed': len(results)
            }
            
            trace.add_data(result)
            return result 