"""Local storage management for audio files and summaries."""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .config import get_settings
from .logger import logger

settings = get_settings()

# Ensure storage directories exist
Path(settings.storage_path).mkdir(parents=True, exist_ok=True)
Path(settings.audio_path).mkdir(parents=True, exist_ok=True)
Path(settings.summaries_path).mkdir(parents=True, exist_ok=True)


def get_storage_size(directory: str) -> int:
    """Calculate total size of files in a directory.
    
    Args:
        directory: Path to the directory
        
    Returns:
        int: Total size in bytes
    """
    total_size = 0
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)
    return total_size


def save_audio(user_id: str, audio_data: bytes, metadata: Dict) -> str:
    """Save audio file locally.
    
    Args:
        user_id: User identifier
        audio_data: Audio file content
        metadata: Audio metadata (duration, format, etc.)
    
    Returns:
        str: Path to the saved audio file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{user_id}_{timestamp}.mp3"
    filepath = os.path.join(settings.audio_path, filename)
    
    # Save audio file
    with open(filepath, "wb") as f:
        f.write(audio_data)
    
    # Save metadata
    meta_path = f"{filepath}.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f)
    
    logger.info(f"Saved audio file: {filepath}")
    return filepath


def save_summary(user_id: str, stories: List[Dict]) -> str:
    """Save news summary as markdown.
    
    Args:
        user_id: User identifier
        stories: List of news stories with title, summary, and source
    
    Returns:
        str: Path to the saved markdown file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{user_id}_{timestamp}.md"
    filepath = os.path.join(settings.summaries_path, filename)
    
    with open(filepath, "w") as f:
        f.write(f"# News Digest for {datetime.now().strftime('%Y-%m-%d')}\n\n")
        
        for story in stories:
            f.write(f"## {story['title']}\n")
            f.write(f"Source: {story['source']}\n\n")
            f.write(f"{story['summary']}\n\n")
            if story.get('original_url'):
                f.write(f"[Read more]({story['original_url']})\n\n")
            f.write("---\n\n")
    
    logger.info(f"Saved summary file: {filepath}")
    return filepath


def get_user_digests(user_id: str) -> List[Dict]:
    """Get all digests for a user.
    
    Args:
        user_id: User identifier
    
    Returns:
        List[Dict]: List of digest metadata
    """
    digests = []
    
    # Get audio files
    audio_pattern = f"{user_id}_*.mp3"
    for audio_file in Path(settings.audio_path).glob(audio_pattern):
        meta_file = Path(f"{audio_file}.json")
        if meta_file.exists():
            with open(meta_file) as f:
                metadata = json.load(f)
                digests.append({
                    "audio_path": str(audio_file),
                    "created_at": metadata.get("created_at"),
                    "duration": metadata.get("duration"),
                    "summary_path": next(
                        Path(settings.summaries_path).glob(
                            f"{user_id}_{audio_file.stem.split('_')[1]}*.md"
                        ),
                        None
                    )
                })
    
    return sorted(digests, key=lambda x: x["created_at"], reverse=True) 