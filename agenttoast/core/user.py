"""
User configuration and management module for AgentToast.
Handles user preferences, digest history, and user-specific settings.
"""

from pathlib import Path
from typing import Dict, List, Optional
import json
import yaml
from datetime import datetime
from pydantic import BaseModel, Field

class UserPreferences(BaseModel):
    """User preferences for news digests."""
    categories: List[str] = Field(default=["technology", "science"])
    sources: List[str] = Field(default=["reuters", "associated-press"])
    max_stories: int = Field(default=5, ge=1, le=10)
    voice_id: str = Field(default="alloy")  # OpenAI TTS voice
    delivery_time: str = Field(default="06:00")  # 24-hour format
    language: str = Field(default="en")

class DigestHistory(BaseModel):
    """Record of a generated digest."""
    digest_id: str
    timestamp: datetime
    audio_path: Path
    summary_path: Path
    stories: List[str]
    duration: float  # in seconds

class User(BaseModel):
    """User configuration and history."""
    user_id: str
    name: str
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    digests: List[DigestHistory] = Field(default_factory=list)

class UserManager:
    """Manages user configurations and digest history."""
    
    def __init__(self, config_dir: Path = Path("config/users")):
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.users: Dict[str, User] = {}
        self._load_users()

    def _load_users(self) -> None:
        """Load all user configurations from disk."""
        for config_file in self.config_dir.glob("*.yaml"):
            try:
                with open(config_file, "r") as f:
                    data = yaml.safe_load(f)
                    user = User.model_validate(data)
                    self.users[user.user_id] = user
            except Exception as e:
                print(f"Error loading user config {config_file}: {e}")

    def save_user(self, user: User) -> None:
        """Save user configuration to disk."""
        config_path = self.config_dir / f"{user.user_id}.yaml"
        try:
            with open(config_path, "w") as f:
                yaml.safe_dump(json.loads(user.model_dump_json()), f)
        except Exception as e:
            print(f"Error saving user config {config_path}: {e}")

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)

    def create_user(self, user_id: str, name: str) -> User:
        """Create a new user with default preferences."""
        if user_id in self.users:
            raise ValueError(f"User {user_id} already exists")
        
        user = User(user_id=user_id, name=name)
        self.users[user_id] = user
        self.save_user(user)
        return user

    def update_preferences(self, user_id: str, preferences: UserPreferences) -> None:
        """Update user preferences."""
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        self.users[user_id].preferences = preferences
        self.save_user(self.users[user_id])

    def add_digest_history(self, user_id: str, digest: DigestHistory) -> None:
        """Add a digest to user's history."""
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        self.users[user_id].digests.append(digest)
        self.save_user(self.users[user_id])

    def get_user_digests(self, user_id: str, limit: int = 10) -> List[DigestHistory]:
        """Get user's recent digests."""
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        return sorted(
            self.users[user_id].digests,
            key=lambda x: x.timestamp,
            reverse=True
        )[:limit] 