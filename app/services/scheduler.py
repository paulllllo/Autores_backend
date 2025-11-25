from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.models.account import Account  # Changed from User
from app.models.enums import AccountSyncStatus
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
        Poll for new mentions for all ACTIVE accounts
        """
        logger.info("Polling for mentions")
        try:
            # Only fetch active accounts
            accounts = await Account.find(Account.is_active == True).to_list()
            if not accounts:
                logger.info("No active accounts found in database")
                return
                
            twitter_service = TwitterService()
            
            for account in accounts:
                try:
                    # Check if token needs refresh
                    if account.token_expires_at <= datetime.utcnow() + timedelta(minutes=5):
                        await twitter_service.refresh_token(account)
                    
                    # Fetch mentions
                    new_messages = await twitter_service.fetch_mentions(account)
                    if new_messages:
                        logger.info(f"Found {len(new_messages)} new mentions for @{account.twitter_username}")
                    
                    # Update sync status
                    account.last_synced_at = datetime.utcnow()
                    account.sync_status = AccountSyncStatus.ACTIVE
                    account.error_message = None
                    await account.save()
                
                except Exception as e:
                    logger.error(f"Error polling mentions for @{account.twitter_username}: {str(e)}")
                    
                    # Update error status
                    account.sync_status = AccountSyncStatus.ERROR
                    account.error_message = str(e)[:500]  # Limit error message length
                    await account.save()
                    
                    # If we hit rate limit, stop polling for this cycle
                    if "Too Many Requests" in str(e):
                        logger.warning("Rate limit reached, stopping polling for this cycle")
                        account.sync_status = AccountSyncStatus.RATE_LIMITED
                        await account.save()
                        break
        
        except Exception as e:
            logger.error(f"Error in poll_mentions: {str(e)}")
    
    async def refresh_tokens(self):
        """
        Refresh tokens for all active accounts
        """
        logger.info("Refreshing tokens")
        try:
            # Only refresh tokens for active accounts
            accounts = await Account.find(Account.is_active == True).to_list()
            if not accounts:
                logger.info("No active accounts found in database")
                return
                
            twitter_service = TwitterService()
            
            for account in accounts:
                try:
                    # Only refresh if token expires within next hour
                    if account.token_expires_at <= datetime.utcnow() + timedelta(hours=1):
                        success = await twitter_service.refresh_token(account)
                        if success:
                            logger.info(f"Refreshed token for @{account.twitter_username}")
                            account.sync_status = AccountSyncStatus.ACTIVE
                            account.error_message = None
                        else:
                            logger.error(f"Failed to refresh token for @{account.twitter_username}")
                            account.sync_status = AccountSyncStatus.TOKEN_EXPIRED
                            account.error_message = "Failed to refresh token"
                        await account.save()
                
                except Exception as e:
                    logger.error(f"Error refreshing token for @{account.twitter_username}: {str(e)}")
                    account.sync_status = AccountSyncStatus.ERROR
                    account.error_message = str(e)[:500]
                    await account.save()
        
        except Exception as e:
            logger.error(f"Error in refresh_tokens: {str(e)}")


scheduler_service = SchedulerService() 