"""Text-to-speech utilities for converting text to audio files."""

import os
import time
from pathlib import Path
from datetime import datetime
import requests
from openai import OpenAI
from src.config import get_logger

logger = get_logger(__name__)

def text_to_speech(text: str, voice: str = "alloy", output_dir: str = None, filename: str = None) -> str:
    """
    Convert text to speech using OpenAI's TTS API and save to an audio file.
    
    Args:
        text: The text to convert to speech
        voice: The voice to use (alloy, echo, fable, onyx, nova, shimmer)
        output_dir: Directory to save the audio file (defaults to 'output/YYYY-MM-DD')
        filename: Custom filename (defaults to 'news_summary_TIMESTAMP.mp3')
        
    Returns:
        The path to the saved audio file
    """
    # Initialize the OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    if not client.api_key:
        logger.error("Cannot generate audio: OPENAI_API_KEY not found")
        return None
    
    # Set up the output directory
    if not output_dir:
        today = datetime.now().strftime("%Y-%m-%d")
        output_dir = os.path.join("output", today)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Set up the filename
    if not filename:
        timestamp = int(time.time())
        filename = f"news_summary_{timestamp}.mp3"
    
    if not filename.endswith(".mp3"):
        filename = f"{filename}.mp3"
    
    output_path = os.path.join(output_dir, filename)
    
    try:
        # Generate the speech
        logger.info(f"Generating speech with voice: {voice}")
        
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        # Save the audio file
        response.stream_to_file(output_path)
        
        logger.info(f"Audio saved to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}")
        return None

def get_playback_command(file_path: str) -> str:
    """
    Get the appropriate command to play an audio file based on the OS.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        The command to play the audio file
    """
    if os.name == "posix":  # macOS or Linux
        return f"afplay \"{file_path}\"" if os.path.exists("/usr/bin/afplay") else f"mpg123 \"{file_path}\""
    else:  # Windows
        return f"start \"{file_path}\"" 