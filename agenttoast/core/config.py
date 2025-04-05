"""Configuration management for AgentToast."""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str
    openai_org_id: str
    
    # News API Configuration
    news_api_key: str
    
    # Application Configuration
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str
    app_port: int = 8000
    
    # Scheduler Configuration
    scraping_start_time: str = "06:00"
    delivery_deadline: str = "07:00"
    
    # Audio Configuration
    audio_quality_bitrate: int = 128
    default_voice: str = "alloy"
    
    # Storage Configuration
    storage_path: str = "./storage"
    audio_path: str = "./storage/audio"
    summaries_path: str = "./storage/summaries"
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    # Test Configuration
    test_mode: bool = False
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings() 