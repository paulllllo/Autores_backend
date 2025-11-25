#!/usr/bin/env python3
"""
Migration script: User collection → Account collection
Also updates Message documents with new structure

This migrates:
1. Users collection → Accounts collection (with new fields)
2. Messages.user field → Messages.sender and Messages.sent_to objects
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_users_to_accounts():
    """Migrate User documents to Account documents"""
    logger.info("="*60)
    logger.info("Migrating Users → Accounts")
    logger.info("="*60)
    
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    try:
        # Get old users collection
        users_collection = db["users"]
        accounts_collection = db["accounts"]
        
        users = await users_collection.find({}).to_list(length=None)
        logger.info(f"Found {len(users)} users to migrate")
        
        if not users:
            logger.info("No users to migrate")
            return 0
        
        migrated = 0
        for user in users:
            # Check if already migrated
            existing = await accounts_collection.find_one({"twitter_id": user["twitter_id"]})
            if existing:
                logger.info(f"Account {user.get('twitter_id')} already exists, skipping")
                continue
            
            # Create account document with new fields
            # Generate new UUID for id field if it doesn't exist
            import uuid
            user_id = user.get("id", str(uuid.uuid4()))
            
            account = {
                "_id": user["_id"],  # Keep same MongoDB ID
                "id": user_id,
                "twitter_id": user["twitter_id"],
                "twitter_username": user.get("twitter_username", f"user_{user['twitter_id']}"),  # Use existing or generate
                "display_name": user.get("display_name"),
                "profile_image_url": user.get("profile_image_url"),
                "access_token": user["access_token"],
                "refresh_token": user["refresh_token"],
                "token_expires_at": user["token_expires_at"],
                "is_active": True,  # New field
                "sync_status": "active",  # New field
                "error_message": None,  # New field
                "added_at": user.get("created_at", datetime.utcnow()),  # New field
                "added_by": None,  # New field
                "last_synced_at": None,  # New field
                "total_mentions_tracked": 0,  # New field - will be calculated
                "created_at": user.get("created_at", datetime.utcnow()),
                "updated_at": user.get("updated_at", datetime.utcnow()),
            }
            
            await accounts_collection.insert_one(account)
            migrated += 1
            logger.info(f"Migrated user {user['twitter_id']} → account {account['twitter_username']}")
        
        logger.info(f"✅ Migrated {migrated} users to accounts")
        return migrated
        
    except Exception as e:
        logger.error(f"Error migrating users: {e}")
        raise
    finally:
        client.close()


async def migrate_messages():
    """Update Message documents with new sender/sent_to structure"""
    logger.info("="*60)
    logger.info("Migrating Message documents")
    logger.info("="*60)
    
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    try:
        messages_collection = db["messages"]
        accounts_collection = db["accounts"]
        
        # Get all messages
        messages = await messages_collection.find({}).to_list(length=None)
        logger.info(f"Found {len(messages)} messages to update")
        
        if not messages:
            logger.info("No messages to migrate")
            return 0
        
        # Build account lookup
        accounts = await accounts_collection.find({}).to_list(length=None)
        account_by_twitter_id = {acc["twitter_id"]: acc for acc in accounts}
        
        updated = 0
        skipped = 0
        
        for msg in messages:
            # Skip if already has new structure
            if "sender" in msg and "sent_to" in msg:
                skipped += 1
                continue
            
            # Get the old user field (this was the author_id of the mention sender)
            author_twitter_id = msg.get("user")
            if not author_twitter_id:
                msg_id = msg.get("id") or msg.get("_id")
                logger.warning(f"Message {msg_id} has no user field, skipping")
                skipped += 1
                continue
            
            # Since we don't have info about the sender stored, create minimal sender object
            sender = {
                "twitter_id": author_twitter_id,
                "username": f"user_{author_twitter_id}",  # We don't have the username
                "display_name": None,
                "profile_image_url": None
            }
            
            # The message was sent to one of our tracked accounts
            # We need to figure out which one - for now, use the first active account
            # In production, you'd have this relationship stored
            if accounts:
                # Use first account as default (you may need better logic here)
                account = accounts[0]
                sent_to = {
                    "account_id": account["id"],
                    "twitter_id": account["twitter_id"],
                    "username": account.get("twitter_username", f"user_{account['twitter_id']}"),
                    "display_name": account.get("display_name")
                }
            else:
                msg_id = msg.get("id") or msg.get("_id")
                logger.warning(f"No accounts found, cannot determine sent_to for message {msg_id}")
                skipped += 1
                continue
            
            # Update message
            # Get tweet_id - try "tweet_id" first, then "id", fallback to _id
            tweet_id = msg.get("tweet_id") or msg.get("id") or str(msg["_id"])
            
            update_result = await messages_collection.update_one(
                {"_id": msg["_id"]},
                {
                    "$set": {
                        "tweet_id": tweet_id,
                        "sender": sender,
                        "sent_to": sent_to,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if update_result.modified_count > 0:
                updated += 1
                if updated % 10 == 0:
                    logger.info(f"Updated {updated} messages...")
        
        logger.info(f"✅ Updated {updated} messages, skipped {skipped}")
        
        # Update mention counts for accounts
        logger.info("Updating mention counts for accounts...")
        for account in accounts:
            count = await messages_collection.count_documents({"sent_to.account_id": account["id"]})
            await accounts_collection.update_one(
                {"_id": account["_id"]},
                {"$set": {"total_mentions_tracked": count}}
            )
        logger.info("✅ Updated mention counts")
        
        return updated
        
    except Exception as e:
        logger.error(f"Error migrating messages: {e}")
        raise
    finally:
        client.close()


async def main():
    """Run all migrations"""
    logger.info("\n" + "="*60)
    logger.info("MIGRATION: Users → Accounts + Message Updates")
    logger.info("="*60 + "\n")
    
    try:
        # Migrate users to accounts
        users_migrated = await migrate_users_to_accounts()
        logger.info("")
        
        # Update messages with new structure
        messages_updated = await migrate_messages()
        logger.info("")
        
        logger.info("="*60)
        logger.info("✅ Migration Complete!")
        logger.info(f"   - Users migrated: {users_migrated}")
        logger.info(f"   - Messages updated: {messages_updated}")
        logger.info("="*60)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Update app/db/mongodb.py to import Account instead of User")
        logger.info("2. Update all endpoints to use Account model")
        logger.info("3. Test the application")
        logger.info("")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate User collection to Account collection')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()
    
    if not args.yes:
        print("\n⚠️  This will migrate User collection → Account collection")
        print("   and update Message documents with new structure.\n")
        response = input("Continue? (yes/no): ")
        
        if response.lower() not in ['yes', 'y']:
            print("Migration cancelled.")
            sys.exit(0)
    
    print("")
    asyncio.run(main())

