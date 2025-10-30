from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.models.user import User
from app.services.twitter import TwitterService
from app.core.config import settings
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        logger.info("SchedulerService initialized")
    
    def start_polling(self):
        """
        Start the mentions polling job
        """
        logger.info("Starting scheduler polling jobs")
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
        
        # Calculate polling interval based on rate limits
        # We want to stay well under the rate limit
        # For example, if we have 50 requests per 15 minutes, we'll poll every 5 minutes
        # This gives us 3 requests per 15 minutes, well under the limit
        polling_interval = settings.TWITTER_POLLING_INTERVAL
        
        self.scheduler.add_job(
            self.poll_mentions,
            trigger=IntervalTrigger(minutes=polling_interval),
            id="poll_mentions",
            replace_existing=True
        )
        logger.info(f"Added poll_mentions job (interval: {polling_interval} minutes)")
        
        # Token refresh can be less frequent
        self.scheduler.add_job(
            self.refresh_tokens,
            trigger=IntervalTrigger(hours=2),
            id="refresh_tokens",
            replace_existing=True
        )
        logger.info("Added refresh_tokens job")
    
    async def poll_mentions(self):
        """
        Poll for new mentions for all users
        """
        logger.info("Polling for mentions")
        try:
            users = await User.find_all().to_list()
            if not users:
                logger.info("No users found in database")
                return
                
            twitter_service = TwitterService()
            
            for user in users:
                try:
                    # Check if token needs refresh
                    if user.token_expires_at <= datetime.utcnow() + timedelta(minutes=5):
                        await twitter_service.refresh_token(user)
                    
                    # Fetch mentions
                    new_messages = await twitter_service.fetch_mentions(user)
                    if new_messages:
                        logger.info(f"Found {len(new_messages)} new mentions for user {user.twitter_id}")
                
                except Exception as e:
                    logger.error(f"Error polling mentions for user {user.twitter_id}: {str(e)}")
                    # If we hit rate limit, stop polling for this cycle
                    if "Too Many Requests" in str(e):
                        logger.warning("Rate limit reached, stopping polling for this cycle")
                        break
        
        except Exception as e:
            logger.error(f"Error in poll_mentions: {str(e)}")
    
    async def refresh_tokens(self):
        """
        Refresh tokens for all users
        """
        logger.info("Refreshing tokens")
        try:
            users = await User.find_all().to_list()
            if not users:
                logger.info("No users found in database")
                return
                
            twitter_service = TwitterService()
            
            for user in users:
                try:
                    if user.token_expires_at <= datetime.utcnow() + timedelta(hours=1):
                        await twitter_service.refresh_token(user)
                        logger.info(f"Refreshed token for user {user.twitter_id}")
                
                except Exception as e:
                    logger.error(f"Error refreshing token for user {user.twitter_id}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error in refresh_tokens: {str(e)}")


scheduler_service = SchedulerService() 