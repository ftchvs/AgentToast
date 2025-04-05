"""Celery configuration for task scheduling."""
from celery import Celery
from celery.schedules import crontab
from pathlib import Path

from agenttoast.core.config import get_settings
from agenttoast.core.safety import SafetyManager

settings = get_settings()
safety_manager = SafetyManager(Path(settings.config_path))

# Create Celery app
app = Celery(
    "agenttoast",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

# Configure Celery
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Safety-related settings
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
    worker_max_memory_per_child=200000,  # 200MB
    task_reject_on_worker_lost=True,
    task_acks_late=True,  # Only acknowledge after task completion
)

# Configure periodic tasks
app.conf.beat_schedule = {
    "scrape-news": {
        "task": "agenttoast.tasks.workers.scrape_news",
        "schedule": crontab(hour=6, minute=0),  # Run at 6:00 AM UTC
    },
    "generate-digests": {
        "task": "agenttoast.tasks.workers.generate_digests",
        "schedule": crontab(hour=6, minute=30),  # Run at 6:30 AM UTC
    },
    "deliver-digests": {
        "task": "agenttoast.tasks.workers.deliver_digests",
        "schedule": crontab(hour=7, minute=0),  # Run at 7:00 AM UTC
    },
    # Safety-related tasks
    "cleanup-old-files": {
        "task": "agenttoast.tasks.workers.cleanup_old_files",
        "schedule": crontab(hour=0, minute=0),  # Run daily at midnight
    },
    "reset-usage-stats": {
        "task": "agenttoast.tasks.workers.reset_usage_stats",
        "schedule": crontab(hour=0, minute=0),  # Reset stats daily at midnight
    },
}

# Import tasks
from .workers import *  # noqa 