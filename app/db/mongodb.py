from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class MongoDB:
    client: AsyncIOMotorClient = None


mongodb = MongoDB()


async def connect_to_mongodb():
    """Initialize MongoDB connection and Beanie ODM"""
    try:
        logger.info("Connecting to MongoDB...")
        mongodb.client = AsyncIOMotorClient(settings.MONGODB_URL)
        
        # Import all document models
        from app.models.account import Account  # Twitter accounts being tracked
        from app.models.message import Message
        from app.models.oauth_state import OAuthState
        from app.models.app_user import AppUser  # Application users
        
        # Initialize Beanie with document models
        await init_beanie(
            database=mongodb.client[settings.MONGODB_DB_NAME],
            document_models=[AppUser, Account, Message, OAuthState]
        )
        
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        raise


async def close_mongodb_connection():
    """Close MongoDB connection"""
    try:
        if mongodb.client:
            mongodb.client.close()
            logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")

