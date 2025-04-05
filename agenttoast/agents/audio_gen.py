"""Audio generation agent for converting summaries to speech."""
from typing import Dict, List, Tuple

import openai
from pydantic import BaseModel

from ..core.config import get_settings
from ..core.logger import logger
from .summarizer import Summary
from ..core.agent import Agent

settings = get_settings()


class AudioDigest(BaseModel):
    """Audio digest data model."""
    audio_data: bytes
    duration: float
    format: str = "mp3"
    bitrate: int = settings.audio_quality_bitrate
    stories: List[Summary]


class AudioGeneratorAgent(Agent):
    """Agent for generating audio digests from summaries."""

    def __init__(self):
        super().__init__()
        self.client = openai.OpenAI(
            api_key=settings.openai_api_key,
            organization=settings.openai_org_id
        )
        self.voice = settings.default_voice

    def _prepare_script(self, summaries: List[Summary]) -> str:
        """Prepare the script for text-to-speech conversion.
        
        Args:
            summaries: List of article summaries
        
        Returns:
            str: Formatted script for TTS
        """
        script_parts = [
            "Welcome to your personalized news digest.",
            "Here are today's top stories:\n",
        ]
        
        for i, summary in enumerate(summaries, 1):
            script_parts.extend([
                f"Story {i}: {summary.title}",
                f"From {summary.source}.",
                f"{summary.summary}\n",
            ])
        
        script_parts.append(
            "That's all for today's digest. Thank you for listening."
        )
        
        return "\n\n".join(script_parts)

    async def generate_audio(self, script: str) -> Tuple[bytes, float]:
        """Generate audio from script using OpenAI TTS.
        
        Args:
            script: Text to convert to speech
        
        Returns:
            Tuple[bytes, float]: Audio data and duration
        """
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=self.voice,
                input=script
            )
            
            # Get audio data
            audio_data = response.content
            
            # Calculate approximate duration (assuming average speaking rate)
            # This is a rough estimate; actual duration would need audio analysis
            word_count = len(script.split())
            estimated_duration = word_count / 2.5  # Assuming ~150 words per minute
            
            return audio_data, estimated_duration
        
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            return None, 0

    async def run(self, summaries: List[Summary]) -> AudioDigest:
        """Run the audio generation agent.
        
        Args:
            summaries: List of article summaries
        
        Returns:
            AudioDigest: Generated audio digest
        """
        logger.info("Starting audio generation")
        
        # Prepare the script
        script = self._prepare_script(summaries)
        
        # Generate audio
        audio_data, duration = await self.generate_audio(script)
        
        if not audio_data:
            logger.error("Failed to generate audio digest")
            return None
        
        # Create audio digest
        digest = AudioDigest(
            audio_data=audio_data,
            duration=duration,
            stories=summaries
        )
        
        logger.info(
            f"Generated audio digest",
            extra={
                "duration": duration,
                "stories": len(summaries)
            }
        )
        
        return digest 