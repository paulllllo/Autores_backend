from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.models.user import User
from app.services.twitter import TwitterService
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
    
    def start_polling(self):
        """
        Start the mentions polling job
        """
        self.scheduler.add_job(
            self.poll_mentions,
            trigger=IntervalTrigger(minutes=5),
            id="poll_mentions",
            replace_existing=True
        )
        
        self.scheduler.add_job(
            self.refresh_tokens,
            trigger=IntervalTrigger(hours=1),
            id="refresh_tokens",
            replace_existing=True
        )
    
    async def poll_mentions(self):
        """
        Poll for new mentions for all users
        """
        db = SessionLocal()
        try:
            users = db.query(User).all()
            twitter_service = TwitterService(db)
            
            for user in users:
                try:
                    # Check if token needs refresh
                    if user.token_expires_at <= datetime.utcnow() + timedelta(minutes=5):
                        twitter_service.refresh_token(user)
                    
                    # Fetch mentions
                    new_messages = twitter_service.fetch_mentions(user)
                    if new_messages:
                        logger.info(f"Found {len(new_messages)} new mentions for user {user.twitter_id}")
                
                except Exception as e:
                    logger.error(f"Error polling mentions for user {user.twitter_id}: {str(e)}")
        
        finally:
            db.close()
    
    async def refresh_tokens(self):
        """
        Refresh tokens for all users
        """
        db = SessionLocal()
        try:
            users = db.query(User).all()
            twitter_service = TwitterService(db)
            
            for user in users:
                try:
                    if user.token_expires_at <= datetime.utcnow() + timedelta(hours=1):
                        twitter_service.refresh_token(user)
                        logger.info(f"Refreshed token for user {user.twitter_id}")
                
                except Exception as e:
                    logger.error(f"Error refreshing token for user {user.twitter_id}: {str(e)}")
        
        finally:
            db.close()


scheduler_service = SchedulerService() 