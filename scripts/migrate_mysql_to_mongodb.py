"""
Data migration script from MySQL to MongoDB
Run this script to migrate existing data from MySQL to MongoDB Atlas

Usage:
    python scripts/migrate_mysql_to_mongodb.py

Prerequisites:
    - MySQL database with existing data
    - MongoDB Atlas cluster set up and accessible
    - MONGODB_URL in .env file
    - MYSQL_DATABASE_URL environment variable set
"""
import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from datetime import datetime
import logging

# For extracting from MySQL using raw SQL
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import Beanie models
from app.models.user import User
from app.models.message import Message
from app.models.oauth_state import OAuthState
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_users(connection):
    """Migrate users from MySQL to MongoDB using raw SQL"""
    logger.info("Migrating users...")
    
    # Query MySQL using raw SQL
    result = connection.execute(text("SELECT * FROM users"))
    users = result.fetchall()
    
    if not users:
        logger.info("No users found in MySQL database")
        return 0
    
    count = 0
    for row in users:
        try:
            user = User(
                id=row.id,
                twitter_id=row.twitter_id,
                access_token=row.access_token,
                refresh_token=row.refresh_token,
                token_expires_at=row.token_expires_at,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            await user.insert()
            count += 1
            logger.info(f"Migrated user: {row.twitter_id}")
        except Exception as e:
            logger.error(f"Error migrating user {row.id}: {e}")
            # Continue with other users even if one fails
            continue
    
    logger.info(f"Successfully migrated {count}/{len(users)} users")
    return count


async def migrate_messages(connection):
    """Migrate messages from MySQL to MongoDB using raw SQL"""
    logger.info("Migrating messages...")
    
    # Query MySQL using raw SQL
    result = connection.execute(text("SELECT * FROM messages"))
    messages = result.fetchall()
    
    if not messages:
        logger.info("No messages found in MySQL database")
        return 0
    
    total = len(messages)
    batch_size = 100
    migrated_count = 0
    
    for i in range(0, total, batch_size):
        batch = messages[i:i + batch_size]
        mongo_messages = []
        
        for row in batch:
            try:
                message = Message(
                    id=row.id,
                    timestamp=row.timestamp,
                    user=row.user,
                    text=row.text,
                    status=row.status,
                    public_response=row.public_response,
                    dm_response=row.dm_response,
                    credits_used=row.credits_used,
                    redirected=row.redirected,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                mongo_messages.append(message)
            except Exception as e:
                logger.error(f"Error preparing message {row.id}: {e}")
                continue
        
        if mongo_messages:
            try:
                await Message.insert_many(mongo_messages)
                migrated_count += len(mongo_messages)
                logger.info(f"Migrated {migrated_count}/{total} messages")
            except Exception as e:
                logger.error(f"Error inserting batch: {e}")
    
    logger.info(f"Successfully migrated {migrated_count}/{total} messages")
    return migrated_count


async def migrate_oauth_states(connection):
    """Migrate OAuth states from MySQL to MongoDB using raw SQL"""
    logger.info("Migrating OAuth states...")
    
    # Query MySQL using raw SQL
    result = connection.execute(text("SELECT * FROM oauth_states"))
    states = result.fetchall()
    
    if not states:
        logger.info("No OAuth states found in MySQL database")
        return 0
    
    count = 0
    for row in states:
        try:
            oauth_state = OAuthState(
                state=row.state,
                code_verifier=row.code_verifier,
                created_at=row.created_at
            )
            await oauth_state.insert()
            count += 1
            logger.info(f"Migrated OAuth state: {row.state[:20]}...")
        except Exception as e:
            logger.error(f"Error migrating OAuth state {row.state}: {e}")
            # Continue with other states even if one fails
            continue
    
    logger.info(f"Successfully migrated {count}/{len(states)} OAuth states")
    return count


async def verify_migration(user_count, message_count, state_count):
    """Verify that data was migrated correctly"""
    logger.info("="*50)
    logger.info("Verifying migration...")
    
    # Count documents in MongoDB
    mongo_user_count = await User.count()
    mongo_message_count = await Message.count()
    mongo_state_count = await OAuthState.count()
    
    logger.info(f"MySQL Users: {user_count} | MongoDB Users: {mongo_user_count}")
    logger.info(f"MySQL Messages: {message_count} | MongoDB Messages: {mongo_message_count}")
    logger.info(f"MySQL OAuth States: {state_count} | MongoDB OAuth States: {mongo_state_count}")
    
    all_match = (user_count == mongo_user_count and 
                 message_count == mongo_message_count and 
                 state_count == mongo_state_count)
    
    if all_match:
        logger.info("✅ All counts match! Migration appears successful.")
    else:
        logger.warning("⚠️  Counts don't match. Please review the logs for errors.")
    
    logger.info("="*50)
    return all_match


async def main():
    """Main migration function"""
    logger.info("="*50)
    logger.info("Starting migration from MySQL to MongoDB")
    logger.info("="*50)
    
    # Get MySQL connection string
    MYSQL_DATABASE_URL = os.getenv("MYSQL_DATABASE_URL")
    
    if not MYSQL_DATABASE_URL:
        logger.error("MYSQL_DATABASE_URL environment variable not set!")
        logger.error("Please set it in your environment or .env file")
        logger.error("Example: MYSQL_DATABASE_URL=mysql+pymysql://user:pass@localhost/dbname")
        sys.exit(1)
    
    if not settings.MONGODB_URL:
        logger.error("MONGODB_URL not found in settings!")
        logger.error("Please ensure it's set in your .env file")
        sys.exit(1)
    
    logger.info(f"MySQL URL: {MYSQL_DATABASE_URL.split('@')[1] if '@' in MYSQL_DATABASE_URL else 'configured'}")
    logger.info(f"MongoDB URL: {settings.MONGODB_URL.split('@')[1] if '@' in settings.MONGODB_URL else 'configured'}")
    logger.info("")
    
    # Connect to MySQL
    logger.info("Connecting to MySQL...")
    try:
        engine = create_engine(MYSQL_DATABASE_URL)
        connection = engine.connect()
        logger.info("✅ Connected to MySQL")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MySQL: {e}")
        sys.exit(1)
    
    # Connect to MongoDB
    logger.info("Connecting to MongoDB...")
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        await init_beanie(
            database=client[settings.MONGODB_DB_NAME],
            document_models=[User, Message, OAuthState]
        )
        logger.info("✅ Connected to MongoDB")
        logger.info("")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        connection.close()
        sys.exit(1)
    
    try:
        # Run migrations
        logger.info("Starting data migration...")
        logger.info("")
        
        user_count = await migrate_users(connection)
        logger.info("")
        
        message_count = await migrate_messages(connection)
        logger.info("")
        
        state_count = await migrate_oauth_states(connection)
        logger.info("")
        
        # Verify migration
        await verify_migration(user_count, message_count, state_count)
        
        logger.info("="*50)
        logger.info("✅ Migration completed!")
        logger.info(f"Total migrated: {user_count} users, {message_count} messages, {state_count} oauth_states")
        logger.info("="*50)
        
    except Exception as e:
        logger.error("="*50)
        logger.error(f"❌ Migration failed: {e}")
        logger.error("="*50)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        connection.close()
        client.close()


if __name__ == "__main__":
    print("\n" + "="*50)
    print("MongoDB Migration Script")
    print("="*50 + "\n")
    
    # Confirm before proceeding
    response = input("⚠️  This will migrate data from MySQL to MongoDB. Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Migration cancelled.")
        sys.exit(0)
    
    print("")
    asyncio.run(main())

