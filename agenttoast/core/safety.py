"""Safety module for managing API usage, costs, storage, and monitoring.

This module provides classes and utilities for:
- Tracking API usage and costs
- Managing storage limits and cleanup
- Setting and enforcing safety thresholds
- Monitoring system health
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import json
import os
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class UsageStats(BaseModel):
    """Tracks daily API and resource usage."""
    date: datetime
    openai_tokens: int = 0
    audio_chars: int = 0
    newsapi_calls: int = 0
    estimated_cost: float = 0.0
    storage_used: int = 0  # bytes

class SafetyLimits(BaseModel):
    """System-wide safety limits and thresholds."""
    # API Limits
    max_articles_per_day: int = Field(default=50, ge=1)
    max_summary_tokens: int = Field(default=2000, ge=100)
    max_audio_chars: int = Field(default=5000, ge=100)
    
    # Cost Limits
    max_daily_cost: float = Field(default=5.0, ge=0.0)
    cost_alert_threshold: float = Field(default=4.0, ge=0.0)
    
    # Storage Limits
    max_storage_size: int = Field(default=1024*1024*1024, ge=1024*1024)  # 1GB minimum
    max_file_age_days: int = Field(default=7, ge=1)
    storage_alert_threshold: float = Field(default=0.8, ge=0.0, le=1.0)  # 80% of max
    
    # Error Handling
    max_retries: int = Field(default=3, ge=1)
    backoff_factor: int = Field(default=2, ge=1)
    
    class Config:
        arbitrary_types_allowed = True

class SafetyManager:
    """Manages safety limits and monitoring."""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.stats_file = config_dir / "usage_stats.json"
        self.limits_file = config_dir / "safety_limits.json"
        
        # Load or create safety limits
        self.limits = self._load_or_create_limits()
        
        # Load or create usage stats
        self.stats = self._load_or_create_stats()
    
    def _load_or_create_limits(self) -> SafetyLimits:
        """Load existing safety limits or create defaults."""
        if self.limits_file.exists():
            try:
                with open(self.limits_file) as f:
                    return SafetyLimits(**json.load(f))
            except Exception as e:
                logger.error(f"Error loading safety limits: {e}")
        
        # Create default limits
        limits = SafetyLimits()
        self._save_limits(limits)
        return limits
    
    def _load_or_create_stats(self) -> UsageStats:
        """Load existing usage stats or create new ones."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if self.stats_file.exists():
            try:
                with open(self.stats_file) as f:
                    data = json.load(f)
                    stats = UsageStats(**data)
                    # Reset if stats are from a previous day
                    if stats.date.date() < today.date():
                        stats = UsageStats(date=today)
                    return stats
            except Exception as e:
                logger.error(f"Error loading usage stats: {e}")
        
        # Create new stats for today
        stats = UsageStats(date=today)
        self._save_stats(stats)
        return stats
    
    def _save_limits(self, limits: SafetyLimits):
        """Save safety limits to file."""
        try:
            with open(self.limits_file, 'w') as f:
                json.dump(limits.dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving safety limits: {e}")
    
    def _save_stats(self, stats: UsageStats):
        """Save usage stats to file."""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(stats.dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving usage stats: {e}")
    
    def check_api_limits(self) -> bool:
        """Check if API usage is within limits."""
        if self.stats.newsapi_calls >= self.limits.max_articles_per_day:
            logger.warning("Daily article limit reached")
            return False
        return True
    
    def check_cost_limits(self) -> bool:
        """Check if cost is within limits."""
        if self.stats.estimated_cost >= self.limits.max_daily_cost:
            logger.warning("Daily cost limit reached")
            return False
        if self.stats.estimated_cost >= self.limits.cost_alert_threshold:
            logger.warning("Cost alert threshold reached")
        return True
    
    def check_storage_limits(self, storage_dir: Path) -> bool:
        """Check if storage is within limits."""
        total_size = sum(f.stat().st_size for f in storage_dir.rglob('*') if f.is_file())
        if total_size >= self.limits.max_storage_size:
            logger.warning("Storage limit reached")
            return False
        if total_size >= self.limits.max_storage_size * self.limits.storage_alert_threshold:
            logger.warning("Storage alert threshold reached")
        return True
    
    def cleanup_old_files(self, storage_dir: Path):
        """Remove files older than max_file_age_days."""
        cutoff = datetime.now() - timedelta(days=self.limits.max_file_age_days)
        for file_path in storage_dir.rglob('*'):
            if file_path.is_file():
                if datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff:
                    try:
                        file_path.unlink()
                        logger.info(f"Removed old file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error removing file {file_path}: {e}")
    
    def update_usage(self, tokens: int = 0, chars: int = 0, api_calls: int = 0, cost: float = 0.0):
        """Update usage statistics."""
        self.stats.openai_tokens += tokens
        self.stats.audio_chars += chars
        self.stats.newsapi_calls += api_calls
        self.stats.estimated_cost += cost
        self._save_stats(self.stats)
    
    def get_current_usage(self) -> Dict:
        """Get current usage statistics."""
        return {
            "date": self.stats.date.strftime("%Y-%m-%d"),
            "openai_tokens": self.stats.openai_tokens,
            "audio_chars": self.stats.audio_chars,
            "newsapi_calls": self.stats.newsapi_calls,
            "estimated_cost": round(self.stats.estimated_cost, 2),
            "storage_used": self.stats.storage_used
        } 