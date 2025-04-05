"""User model for storing user preferences and settings."""
from datetime import time
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class User(Base):
    """User model with preferences and settings."""
    
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    
    # Preferences
    preferred_categories: Mapped[List[str]] = mapped_column(
        JSON, default=lambda: ["politics", "economy", "technology"]
    )
    preferred_sources: Mapped[List[str]] = mapped_column(
        JSON, default=list
    )
    story_count: Mapped[int] = mapped_column(default=5)
    preferred_voice: Mapped[str] = mapped_column(String(50), default="alloy")
    
    # Delivery Settings
    delivery_time: Mapped[time] = mapped_column(Time, default=time(7, 0))  # 7:00 AM
    delivery_method: Mapped[str] = mapped_column(
        String(20), default="app"  # Options: app, email, both
    )
    
    # Relationships
    digests: Mapped[List["NewsDigest"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User {self.email}>" 