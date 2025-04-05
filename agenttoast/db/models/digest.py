"""NewsDigest model for storing generated news digests."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class NewsDigest(Base):
    """NewsDigest model for storing generated news digests."""
    
    __tablename__ = "news_digests"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    
    # Audio file information
    audio_url: Mapped[str] = mapped_column(String(500))  # S3 URL
    duration_seconds: Mapped[int]
    
    # Metadata
    story_count: Mapped[int]
    categories: Mapped[List[str]] = mapped_column(JSON)
    sources: Mapped[List[str]] = mapped_column(JSON)
    
    # Status
    is_delivered: Mapped[bool] = mapped_column(default=False)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="digests")
    stories: Mapped[List["NewsStory"]] = relationship(
        back_populates="digest", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of the digest."""
        return f"<NewsDigest {self.id} for user {self.user_id}>"


class NewsStory(Base):
    """NewsStory model for storing individual news stories within a digest."""
    
    __tablename__ = "news_stories"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    digest_id: Mapped[UUID] = mapped_column(ForeignKey("news_digests.id"))
    
    # Story content
    title: Mapped[str] = mapped_column(String(500))
    original_url: Mapped[str] = mapped_column(String(500))
    category: Mapped[str] = mapped_column(String(100))
    source: Mapped[str] = mapped_column(String(100))
    
    # Generated content
    summary: Mapped[str] = mapped_column(Text)
    audio_start_time: Mapped[float]  # Start time in seconds within the digest
    audio_duration: Mapped[float]  # Duration in seconds
    
    # Relationship
    digest: Mapped["NewsDigest"] = relationship(back_populates="stories")
    
    def __repr__(self) -> str:
        """String representation of the story."""
        return f"<NewsStory {self.title[:30]}...>" 