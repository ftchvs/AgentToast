"""
Celery worker tasks for AgentToast.
Handles news scraping, summarization, and audio generation tasks.
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime
import uuid
from pathlib import Path

from agenttoast.core.user import UserManager, DigestHistory
from agenttoast.core.safety import SafetyManager
from agenttoast.agents.news_scraper import NewsScraperAgent
from agenttoast.agents.summarizer import SummarizerAgent
from agenttoast.agents.audio_gen import AudioGeneratorAgent
from agenttoast.core.storage import save_audio, save_summary
from agenttoast.core.config import get_settings

logger = get_task_logger(__name__)
settings = get_settings()
safety_manager = SafetyManager(Path(settings.config_path))

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
async def scrape_news(self, user_id: str):
    """Scrape news articles based on user preferences."""
    try:
        # Check API limits before proceeding
        if not safety_manager.check_api_limits():
            raise ValueError("Daily API limit reached")

        manager = UserManager()
        user = manager.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        logger.info(f"Scraping news for user {user.name} ({user_id})")
        scraper = NewsScraperAgent()
        articles = await scraper.run(
            categories=user.preferences.categories,
            sources=user.preferences.sources,
            max_articles=min(
                user.preferences.max_stories,
                safety_manager.limits.max_articles_per_day
            )
        )
        
        # Update API usage stats
        safety_manager.update_usage(api_calls=len(articles))
        return articles
        
    except Exception as e:
        logger.error(f"Error scraping news: {e}")
        if self.request.retries >= safety_manager.limits.max_retries:
            logger.error("Max retries reached for scraping news")
            return None
        raise self.retry(
            exc=e,
            countdown=safety_manager.limits.backoff_factor ** self.request.retries
        )

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
async def generate_digests(self, user_id: str, articles: list):
    """Generate summaries and audio digest for articles."""
    try:
        # Check cost and storage limits
        if not safety_manager.check_cost_limits():
            raise ValueError("Daily cost limit reached")
        
        if not safety_manager.check_storage_limits(Path(settings.audio_path)):
            # Attempt cleanup before failing
            safety_manager.cleanup_old_files(Path(settings.audio_path))
            if not safety_manager.check_storage_limits(Path(settings.audio_path)):
                raise ValueError("Storage limit reached")

        manager = UserManager()
        user = manager.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        logger.info(f"Generating digest for user {user.name} ({user_id})")
        
        # Generate summaries
        summarizer = SummarizerAgent()
        summaries = await summarizer.run(articles)
        
        # Update token usage for summaries
        estimated_tokens = sum(len(s.summary.split()) * 1.3 for s in summaries)  # rough estimate
        safety_manager.update_usage(tokens=int(estimated_tokens))
        
        # Generate audio
        audio_gen = AudioGeneratorAgent()
        audio_digest = await audio_gen.run(
            summaries=summaries,
            voice_id=user.preferences.voice_id
        )
        
        # Update character usage for audio
        total_chars = sum(len(s.summary) for s in summaries)
        safety_manager.update_usage(
            chars=total_chars,
            cost=total_chars * 0.000015  # OpenAI TTS cost per character
        )
        
        # Save files
        digest_id = str(uuid.uuid4())[:8]
        audio_path = save_audio(user_id, digest_id, audio_digest.audio_data)
        summary_path = save_summary(user_id, digest_id, summaries)
        
        # Record digest history
        digest = DigestHistory(
            digest_id=digest_id,
            timestamp=datetime.utcnow(),
            audio_path=audio_path,
            summary_path=summary_path,
            stories=[s.title for s in summaries],
            duration=audio_digest.duration
        )
        manager.add_digest_history(user_id, digest)
        
        return digest_id
        
    except Exception as e:
        logger.error(f"Error generating digest: {e}")
        if self.request.retries >= safety_manager.limits.max_retries:
            logger.error("Max retries reached for generating digest")
            return None
        raise self.retry(
            exc=e,
            countdown=safety_manager.limits.backoff_factor ** self.request.retries
        )

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
async def process_user_digest(self, user_id: str):
    """Process complete digest generation for a user."""
    try:
        logger.info(f"Starting digest processing for user {user_id}")
        
        # Chain the tasks
        articles = await scrape_news(user_id)
        if not articles:
            raise ValueError("No articles found")
            
        digest_id = await generate_digests(user_id, articles)
        if not digest_id:
            raise ValueError("Failed to generate digest")
        
        logger.info(f"Completed digest {digest_id} for user {user_id}")
        return digest_id
        
    except Exception as e:
        logger.error(f"Error processing digest: {e}")
        if self.request.retries >= safety_manager.limits.max_retries:
            logger.error("Max retries reached for processing digest")
            return None
        raise self.retry(
            exc=e,
            countdown=safety_manager.limits.backoff_factor ** self.request.retries
        )

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
async def retry_failed_delivery(self, digest_id: str):
    """Retry delivery of a failed digest."""
    try:
        logger.info(f"Retrying delivery for digest {digest_id}")
        # Implement retry logic here
        pass
    except Exception as e:
        logger.error(f"Error retrying delivery: {e}")
        if self.request.retries >= safety_manager.limits.max_retries:
            logger.error("Max retries reached for delivery retry")
            return None
        raise self.retry(
            exc=e,
            countdown=safety_manager.limits.backoff_factor ** self.request.retries
        )

@shared_task
def cleanup_old_files():
    """Clean up old audio and summary files."""
    try:
        logger.info("Starting file cleanup")
        
        # Clean up audio files
        safety_manager.cleanup_old_files(Path(settings.audio_path))
        
        # Clean up summary files
        safety_manager.cleanup_old_files(Path(settings.summaries_path))
        
        logger.info("File cleanup completed")
    except Exception as e:
        logger.error(f"Error during file cleanup: {e}")

@shared_task
def reset_usage_stats():
    """Reset daily usage statistics."""
    try:
        logger.info("Resetting usage stats")
        safety_manager.stats = safety_manager._load_or_create_stats()
        logger.info("Usage stats reset completed")
    except Exception as e:
        logger.error(f"Error resetting usage stats: {e}") 