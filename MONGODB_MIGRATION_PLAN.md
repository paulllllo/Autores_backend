# MongoDB Migration Plan
## Fast-Track Migration: SQLAlchemy/MySQL to MongoDB Atlas

**Project**: Autores Backend  
**Date Created**: October 29, 2025  
**Last Updated**: October 29, 2025  
**Status**: Planning Phase  
**Migration Method**: Fast-Track (Complete Replacement)

---

## 📋 Executive Summary

### Current State
- **Database**: MySQL with SQLAlchemy ORM
- **Models**: 3 models (User, Message, OAuthState)
- **Operations**: Simple CRUD operations with no complex joins
- **Architecture**: Async FastAPI application
- **Migrations**: Managed by Alembic

### Target State
- **Database**: MongoDB Atlas
- **ODM**: Beanie (Pydantic-based, async)
- **Driver**: Motor (async MongoDB driver)
- **Migrations**: Schema-less, no migration tool needed

### Why This Migration?
- Better scalability for document-based data
- Native JSON/BSON support
- Flexible schema evolution
- Improved performance for read-heavy operations
- Better alignment with modern async Python ecosystem

### Migration Approach
**Fast-Track Complete Replacement** - Given that downtime is acceptable at this development stage, we'll perform a complete replacement of MySQL/SQLAlchemy with MongoDB/Beanie in one go. No parallel systems, no dual-write complexity.

**Estimated Timeline**: 3-5 days  
**Downtime**: 1-2 hours (for data migration and deployment)  
**Risk Level**: Low (given development stage and good backups)

---

## 🎯 Recommended Technology Stack

### Primary Recommendation: Beanie ODM

**Why Beanie?**
1. **Minimal Code Changes**: Syntax very similar to SQLAlchemy
2. **Pydantic Integration**: Works seamlessly with existing schemas
3. **Async by Default**: Perfect match for FastAPI
4. **Type Safety**: Full type hinting support
5. **Active Development**: Well-maintained and documented

**Dependencies:**
```
motor==3.3.2          # Async MongoDB driver
beanie==1.23.6        # ODM for MongoDB
pymongo==4.6.1        # MongoDB driver
```

---

## 🗺️ Fast-Track Migration Strategy: Three-Phase Approach

**Total Duration**: 3-5 days  
**Complexity**: Low to Medium  
**Rollback Plan**: Restore MySQL from backup and revert code

### Phase 1: Setup MongoDB & Create Models 🚀 (Day 1-2)
**Goal**: Set up MongoDB Atlas and create Beanie document models

**Duration**: 1-2 days

**Actions**:
1. **Set up MongoDB Atlas cluster**
   - Create free tier (M0) or appropriate paid tier
   - Configure network access (IP whitelist or 0.0.0.0/0 for dev)
   - Create database user with read/write permissions
   - Get connection string
   
2. **Install MongoDB dependencies**
   - Add motor, beanie, pymongo to requirements.txt
   - Remove sqlalchemy, alembic, pymysql
   - Run `pip install -r requirements.txt`
   
3. **Update configuration**
   - Add MONGODB_URL and MONGODB_DB_NAME to settings
   - Remove DATABASE_URL validation for MySQL
   - Update .env file
   
4. **Create MongoDB connection module**
   - Create `app/db/mongodb.py`
   - Initialize Beanie with document models
   
5. **Convert all models to Beanie documents**
   - Replace `app/models/user.py` with Beanie version
   - Replace `app/models/message.py` with Beanie version
   - Replace `app/models/oauth_state.py` with Beanie version
   
6. **Test MongoDB connection**
   - Test connection in isolation
   - Verify models are correctly initialized

**Impact**: No runtime impact yet, just setup

**Rollback**: Git revert if issues found

---

### Phase 2: Update Application Code 🔧 (Day 2-3)
**Goal**: Replace all SQLAlchemy code with Beanie/MongoDB code

**Duration**: 1-2 days

**Actions**:
1. **Remove old database files**
   - Delete `app/db/base.py`
   - Delete `app/db/base_class.py`
   
2. **Update main.py**
   - Replace SQLAlchemy session management with MongoDB connection
   - Initialize Beanie in lifespan context
   
3. **Update all endpoint files**
   - `app/api/v1/endpoints/auth.py` - Remove Session dependency, use Beanie queries
   - `app/api/v1/endpoints/messages.py` - Replace all SQLAlchemy queries
   
4. **Update service files**
   - `app/services/twitter.py` - Replace Session with direct Beanie calls
   - `app/services/scheduler.py` - Replace SessionLocal with Beanie
   
5. **Remove Alembic**
   - Delete `alembic/` directory
   - Delete `alembic.ini` file
   
6. **Update schemas if needed**
   - Verify Pydantic schemas work with Beanie models
   - Make any necessary adjustments

**Impact**: Complete replacement of database layer

**Rollback**: Git revert to previous commit

**Testing**: Extensive local testing before migration

---

### Phase 3: Data Migration & Deployment 🎯 (Day 4-5)
**Goal**: Migrate existing data and deploy new version

**Duration**: 1-2 days

**Actions**:
1. **Create data migration script**
   - Script to export data from MySQL
   - Script to import data into MongoDB
   - Verify data integrity
   
2. **Backup MySQL database**
   - Full database dump
   - Store in secure location
   - Document restore procedure
   
3. **Run data migration**
   - Export all users from MySQL
   - Export all messages from MySQL
   - Export all oauth_states from MySQL
   - Import into MongoDB
   - Verify record counts match
   - Spot-check sample data
   
4. **Testing**
   - Run full test suite locally
   - Test all endpoints manually
   - Verify scheduler works
   - Test OAuth flow
   - Test message fetching and replies
   
5. **Deployment** (1-2 hour downtime window)
   - Put application in maintenance mode (if needed)
   - Deploy new code
   - Verify application starts correctly
   - Test critical flows
   - Monitor logs for errors
   - Bring application back online
   
6. **Post-deployment monitoring**
   - Monitor for 24-48 hours
   - Check error logs
   - Verify data integrity
   - Monitor performance
   - Be ready to rollback if needed

**Impact**: Complete migration to MongoDB

**Rollback**: Revert code + restore MySQL from backup

---

## 📊 Fast-Track Timeline & Risk Assessment

| Phase | Risk Level | Duration | Deliverable |
|-------|-----------|----------|-------------|
| Phase 1 | Low | 1-2 days | MongoDB setup + Beanie models |
| Phase 2 | Medium | 1-2 days | All code updated to use MongoDB |
| Phase 3 | Low-Medium | 1-2 days | Data migrated + deployed |

**Total Time**: 3-5 days  
**Downtime**: 1-2 hours during Phase 3  
**Risk**: Low (dev stage + good backups)

---

## 🔧 Technical Implementation Details

### Architecture Comparison

| Aspect | Current (SQLAlchemy/MySQL) | New (Beanie/MongoDB) |
|--------|---------------------------|----------------------|
| **Driver** | SQLAlchemy + PyMySQL | Motor (async) + Beanie |
| **Models** | SQLAlchemy Models | Beanie Documents (Pydantic-based) |
| **Sessions** | `SessionLocal()` context | Beanie (automatic handling) |
| **Primary Key** | String (UUID) | String (UUID) or ObjectId |
| **Queries** | `db.query(Model).filter()` | `await Model.find_one()` |
| **Inserts** | `db.add()`, `db.commit()` | `await document.insert()` |
| **Updates** | Modify attributes + commit | `await document.save()` |
| **Deletes** | `db.delete()`, `db.commit()` | `await document.delete()` |
| **Migrations** | Alembic | Not needed (schema-less) |
| **Transactions** | `db.begin()` | `await session.start_transaction()` |

---

### Code Transformation Examples

#### Example 1: Query Operations

**Current (SQLAlchemy)**:
```python
# Single record
user = db.query(User).filter(User.twitter_id == twitter_id).first()

# Multiple records
messages = db.query(Message).order_by(desc(Message.timestamp)).offset(skip).limit(limit).all()

# Count
count = db.query(Message).filter(Message.status == "pending").count()
```

**New (Beanie)**:
```python
# Single record
user = await User.find_one(User.twitter_id == twitter_id)

# Multiple records
messages = await Message.find(
    fetch_links=False
).sort(-Message.timestamp).skip(skip).limit(limit).to_list()

# Count
count = await Message.find(Message.status == "pending").count()
```

#### Example 2: Insert Operations

**Current (SQLAlchemy)**:
```python
user = User(
    id=str(uuid.uuid4()),
    twitter_id="123456",
    access_token="token",
    refresh_token="refresh",
    token_expires_at=datetime.utcnow() + timedelta(hours=2)
)
db.add(user)
db.commit()
db.refresh(user)  # To get server-generated fields
```

**New (Beanie)**:
```python
user = User(
    id=str(uuid.uuid4()),
    twitter_id="123456",
    access_token="token",
    refresh_token="refresh",
    token_expires_at=datetime.utcnow() + timedelta(hours=2)
)
await user.insert()
# No need to refresh, all fields are immediately available
```

#### Example 3: Update Operations

**Current (SQLAlchemy)**:
```python
user = db.query(User).filter(User.id == user_id).first()
if user:
    user.access_token = "new_token"
    user.refresh_token = "new_refresh"
    db.commit()
    db.refresh(user)
```

**New (Beanie)**:
```python
user = await User.find_one(User.id == user_id)
if user:
    user.access_token = "new_token"
    user.refresh_token = "new_refresh"
    await user.save()
```

**Or using update query**:
```python
await User.find_one(User.id == user_id).update(Set({
    User.access_token: "new_token",
    User.refresh_token: "new_refresh"
}))
```

#### Example 4: Delete Operations

**Current (SQLAlchemy)**:
```python
message = db.query(Message).filter(Message.id == message_id).first()
if message:
    db.delete(message)
    db.commit()
```

**New (Beanie)**:
```python
message = await Message.find_one(Message.id == message_id)
if message:
    await message.delete()
```

#### Example 5: Dependency Injection

**Current (SQLAlchemy)**:
```python
from sqlalchemy.orm import Session
from app.db.base import get_db

@router.get("/messages")
async def get_messages(db: Session = Depends(get_db)):
    messages = db.query(Message).all()
    return messages
```

**New (Beanie)**:
```python
# No dependency needed! Beanie handles connection automatically

@router.get("/messages")
async def get_messages():
    messages = await Message.find_all().to_list()
    return messages
```

---

### Model Transformation Guide

#### Current User Model (SQLAlchemy)
```python
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.db.base_class import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    twitter_id = Column(String(255), unique=True, nullable=False)
    access_token = Column(String(255), nullable=False)
    refresh_token = Column(String(255), nullable=False)
    token_expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

#### New User Document (Beanie)
```python
from beanie import Document, Indexed
from datetime import datetime
from typing import Optional
from pydantic import Field

class User(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    twitter_id: Indexed(str, unique=True)
    access_token: str
    refresh_token: str
    token_expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"  # Collection name
        indexes = [
            "twitter_id",  # Single field index
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "twitter_id": "1234567890",
                "access_token": "token_here",
                "refresh_token": "refresh_token_here",
                "token_expires_at": "2025-10-29T12:00:00"
            }
        }
```

---

## 📝 Implementation Steps

### Step 1: Install Dependencies

**Update `requirements.txt`:**
```diff
 fastapi==0.104.1
 uvicorn==0.24.0
-sqlalchemy==2.0.23
-alembic==1.12.1
+motor==3.3.2
+beanie==1.23.6
+pymongo==4.6.1
 python-dotenv==1.0.0
 pydantic==2.4.2
 pydantic-settings==2.0.3
 python-jose[cryptography]==3.3.0
 passlib[bcrypt]==1.7.4
 python-multipart==0.0.6
 httpx==0.25.1
 apscheduler==3.10.4
 pytest==7.4.3
 pytest-asyncio==0.21.1
 pytest-cov==4.1.0
 black==23.10.1
 isort==5.12.0
 flake8==6.1.0
 mypy==1.6.1
-pymysql==1.1.0
 cryptography==41.0.5
```

**Install new dependencies:**
```bash
pip install motor==3.3.2 beanie==1.23.6 pymongo==4.6.1
pip uninstall sqlalchemy alembic pymysql -y
```

---

### Step 2: Configuration Changes

**Update `app/core/config.py`:**
```python
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "Twitter Mentions API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # MongoDB Configuration
    MONGODB_URL: str  # e.g., "mongodb+srv://user:pass@cluster.mongodb.net/dbname?retryWrites=true&w=majority"
    MONGODB_DB_NAME: str  # Database name
    
    @validator("MONGODB_URL", pre=True)
    def validate_mongodb_url(cls, v: str) -> str:
        if not v.startswith("mongodb"):
            raise ValueError("MONGODB_URL must start with mongodb:// or mongodb+srv://")
        return v
    
    # Twitter API
    TWITTER_CLIENT_ID: str
    TWITTER_CLIENT_SECRET: str
    TWITTER_CALLBACK_URL: str
    TWITTER_SCOPE: str = 'tweet.read tweet.write users.read offline.access dm.write'
    
    # Twitter API Rate Limits (Essential tier)
    TWITTER_MENTIONS_RATE_LIMIT: int = 50
    TWITTER_MENTIONS_WINDOW: int = 15
    TWITTER_POLLING_INTERVAL: int = 5
    
    # OpenAI API
    OPENAI_API_KEY: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
```

**Update `.env` file:**
```env
# MongoDB Atlas
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=autores_db

# Twitter API
TWITTER_CLIENT_ID=your_client_id
TWITTER_CLIENT_SECRET=your_client_secret
TWITTER_CALLBACK_URL=http://localhost:8000/api/v1/auth/twitter/callback

# OpenAI
OPENAI_API_KEY=your_openai_key

# Security
SECRET_KEY=your_secret_key_here

# ... other settings ...
```

---

### Step 3: Create MongoDB Connection Module

**Create `app/db/mongodb.py`:**
```python
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
        from app.models.user import User
        from app.models.message import Message
        from app.models.oauth_state import OAuthState
        
        # Initialize Beanie with document models
        await init_beanie(
            database=mongodb.client[settings.MONGODB_DB_NAME],
            document_models=[User, Message, OAuthState]
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
```

---

### Step 4: Convert Models to Beanie Documents

**Replace SQLAlchemy models directly in `app/models/` directory**

**`app/models/user.py`:**
```python
from beanie import Document, Indexed
from datetime import datetime
from pydantic import Field
import uuid


class User(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    twitter_id: Indexed(str, unique=True)
    access_token: str
    refresh_token: str
    token_expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"
        indexes = [
            "twitter_id",
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "twitter_id": "1234567890",
                "access_token": "token",
                "refresh_token": "refresh",
                "token_expires_at": "2025-10-29T12:00:00"
            }
        }
```

**`app/models/message.py`:**
```python
from beanie import Document
from datetime import datetime
from typing import Optional
from pydantic import Field
import uuid


class Message(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime
    user: str  # Twitter user ID
    text: str
    status: str = "pending"
    public_response: Optional[str] = None
    dm_response: Optional[str] = None
    credits_used: int = 0
    redirected: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "messages"
        indexes = [
            "timestamp",
            "user",
            "status",
        ]
```

**`app/models/oauth_state.py`:**
```python
from beanie import Document, Indexed
from datetime import datetime
from pydantic import Field


class OAuthState(Document):
    state: Indexed(str, unique=True)
    code_verifier: str
    created_at: datetime
    
    class Settings:
        name = "oauth_states"
        indexes = [
            "state",
            "created_at",
        ]
```

---

### Step 5: Update Main Application

**Update `app/main.py`:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.services.scheduler import scheduler_service
from app.db.mongodb import connect_to_mongodb, close_mongodb_connection
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application...")
    
    # Connect to MongoDB
    await connect_to_mongodb()
    
    # Start scheduler service
    scheduler_service.start_polling()
    logger.info("Scheduler started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    scheduler_service.scheduler.shutdown()
    await close_mongodb_connection()
    logger.info("Application shut down successfully")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# ... rest of main.py ...
```

---

### Step 6: Update Endpoints (Example: Messages)

**Before (SQLAlchemy)**:
```python
from sqlalchemy.orm import Session
from app.db.base import get_db

@router.get("/", response_model=List[MessageInDB])
async def get_messages(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    messages = db.query(Message).order_by(desc(Message.timestamp)).offset(skip).limit(limit).all()
    return messages
```

**After (Beanie)**:
```python
from app.models_mongo.message import Message

@router.get("/", response_model=List[MessageInDB])
async def get_messages(
    skip: int = 0,
    limit: int = 100
):
    messages = await Message.find().sort(-Message.timestamp).skip(skip).limit(limit).to_list()
    return messages
```

---

### Step 7: Data Migration Script

**Create `scripts/migrate_mysql_to_mongodb.py`:**

**Note**: This script should be created BEFORE you replace the SQLAlchemy models, or you'll need to temporarily keep the old models for the migration.

**Option 1: Run migration before replacing models (recommended)**
- Keep SQLAlchemy models temporarily
- Run this script
- Then replace models with Beanie versions

**Option 2: Use raw SQL to extract data**
- Export MySQL data to JSON/CSV
- Import into MongoDB using a simpler script

```python
"""
Data migration script from MySQL to MongoDB
Run this BEFORE replacing SQLAlchemy models with Beanie models
or use raw SQL queries to extract data
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

# For extracting from MySQL - you'll need to temporarily keep SQLAlchemy
# OR use raw SQL queries
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import current Beanie models (after conversion)
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
    
    count = 0
    for row in users:
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
    
    logger.info(f"Migrated {count} users")
    return count


async def migrate_messages(connection):
    """Migrate messages from MySQL to MongoDB using raw SQL"""
    logger.info("Migrating messages...")
    
    # Query MySQL using raw SQL
    result = connection.execute(text("SELECT * FROM messages"))
    messages = result.fetchall()
    
    batch_size = 100
    total = len(messages)
    
    for i in range(0, total, batch_size):
        batch = messages[i:i + batch_size]
        mongo_messages = [
            Message(
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
            for row in batch
        ]
        await Message.insert_many(mongo_messages)
        logger.info(f"Migrated {i + len(batch)}/{total} messages")
    
    logger.info(f"Migrated {total} messages")
    return total


async def migrate_oauth_states(connection):
    """Migrate OAuth states from MySQL to MongoDB using raw SQL"""
    logger.info("Migrating OAuth states...")
    
    # Query MySQL using raw SQL
    result = connection.execute(text("SELECT * FROM oauth_states"))
    states = result.fetchall()
    
    count = 0
    for row in states:
        oauth_state = OAuthState(
            state=row.state,
            code_verifier=row.code_verifier,
            created_at=row.created_at
        )
        await oauth_state.insert()
        count += 1
    
    logger.info(f"Migrated {count} OAuth states")
    return count


async def main():
    """Main migration function"""
    logger.info("Starting migration from MySQL to MongoDB")
    
    # You'll need the old DATABASE_URL - either from backup .env or hardcode temporarily
    MYSQL_DATABASE_URL = os.getenv("MYSQL_DATABASE_URL", "mysql+pymysql://user:pass@localhost/dbname")
    
    # Connect to MySQL
    engine = create_engine(MYSQL_DATABASE_URL)
    connection = engine.connect()
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.MONGODB_DB_NAME],
        document_models=[User, Message, OAuthState]
    )
    
    try:
        logger.info("Connected to both databases")
        
        # Run migrations
        user_count = await migrate_users(connection)
        message_count = await migrate_messages(connection)
        state_count = await migrate_oauth_states(connection)
        
        logger.info("="*50)
        logger.info("Migration completed successfully!")
        logger.info(f"Total migrated: {user_count} users, {message_count} messages, {state_count} oauth_states")
        logger.info("="*50)
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        connection.close()
        client.close()


if __name__ == "__main__":
    # Usage: python scripts/migrate_mysql_to_mongodb.py
    asyncio.run(main())
```

**Run the migration:**
```bash
python scripts/migrate_mysql_to_mongodb.py
```

---

## ⚠️ Potential Challenges & Solutions

### Challenge 1: Auto-increment IDs vs ObjectId
**Issue**: MySQL typically uses auto-increment integers; MongoDB uses ObjectId by default

**Solution**: ✅ Your current code already uses UUID strings for IDs, which works perfectly with both systems. No changes needed.

---

### Challenge 2: Transactions
**Issue**: SQLAlchemy has built-in transaction support; MongoDB requires explicit sessions

**Current Code**:
```python
db.add(user)
db.commit()  # Atomic transaction
db.rollback()  # On error
```

**MongoDB Solution**:
```python
# Simple operations are atomic by default
await user.insert()

# For multi-document transactions:
async with await mongodb.client.start_session() as session:
    async with session.start_transaction():
        await user.insert(session=session)
        await message.insert(session=session)
        # Automatically commits or rolls back
```

**Reality**: Your application doesn't use complex transactions, so this is not a concern.

---

### Challenge 3: DateTime Handling
**Issue**: Potential timezone/format differences

**Solution**: 
- Both MySQL and MongoDB store datetime in UTC
- Beanie automatically handles conversion
- Your code already uses `datetime.utcnow()` ✅

**Best Practice**: Continue using UTC everywhere, convert to local time in frontend

---

### Challenge 4: Unique Constraints
**Issue**: MySQL enforces uniqueness at database level; MongoDB requires indexes

**Solution**: 
```python
# In Beanie model
class User(Document):
    twitter_id: Indexed(str, unique=True)  # ✅ Creates unique index
    
    class Settings:
        indexes = [
            IndexModel([("twitter_id", 1)], unique=True)
        ]
```

**Note**: Beanie creates indexes automatically on application startup

---

### Challenge 5: NULL vs None
**Issue**: MySQL has NULL; MongoDB has null (None in Python)

**Solution**: ✅ Python's `None` maps to both correctly. Use `Optional[]` type hints as you already do.

---

### Challenge 6: Schema Validation
**Issue**: MySQL enforces schema; MongoDB is flexible

**Solution**: 
- Beanie uses Pydantic models for validation
- Actually **better** than MySQL because:
  - Validation happens before database write
  - Can have complex validation logic
  - Better error messages
  - Type safety in code

---

### Challenge 7: Migrations
**Issue**: No Alembic equivalent for MongoDB

**Solution**: 
- Schema changes are just code changes
- If need data transformations:
  ```python
  # Migration script
  async def migrate_add_new_field():
      await Message.find(Message.new_field == None).update(
          Set({Message.new_field: "default_value"})
      )
  ```
- Use versioning pattern if needed:
  ```python
  class Message(Document):
      schema_version: int = 1
  ```

---

### Challenge 8: Foreign Keys
**Issue**: MySQL has foreign key constraints; MongoDB doesn't

**Current State**: Your models don't use foreign keys (good design choice!)

**If Needed in Future**: Use `Link` in Beanie:
```python
from beanie import Link

class Message(Document):
    user: Link[User]  # Reference to User document
```

---

### Challenge 9: Performance Differences
**Issue**: Query performance might differ

**Solutions**:
- **Indexes**: Create appropriate indexes for common queries
- **Projections**: Only fetch needed fields
  ```python
  users = await User.find().project(UserProjection).to_list()
  ```
- **Aggregation Pipeline**: For complex queries
  ```python
  result = await Message.aggregate([
      {"$match": {"status": "pending"}},
      {"$group": {"_id": "$user", "count": {"$sum": 1}}}
  ]).to_list()
  ```

---

### Challenge 10: Connection Pooling
**Issue**: Need to configure connection pooling properly

**Solution**:
```python
client = AsyncIOMotorClient(
    settings.MONGODB_URL,
    maxPoolSize=50,  # Maximum connections
    minPoolSize=10,  # Minimum connections
    maxIdleTimeMS=30000,  # Close idle connections after 30s
    serverSelectionTimeoutMS=5000,  # Timeout for server selection
    connectTimeoutMS=10000,  # Timeout for initial connection
)
```

---

## ✅ Fast-Track Migration Checklist

### Pre-Migration Preparation
- [ ] **Backup MySQL database** (full dump with mysqldump or similar)
- [ ] **Set up MongoDB Atlas cluster**
  - [ ] Choose appropriate tier (M0 free tier for dev/testing)
  - [ ] Configure network access (IP whitelist or 0.0.0.0/0 for dev)
  - [ ] Create database user with read/write permissions
  - [ ] Save connection string
- [ ] **Test MongoDB connection** using connection string
- [ ] **Document current database schema** (for reference)

---

### Phase 1: Setup MongoDB & Create Models (Day 1-2)

**MongoDB Setup:**
- [ ] MongoDB Atlas cluster created and accessible
- [ ] Connection string tested

**Dependencies:**
- [ ] Install motor, beanie, pymongo
- [ ] Uninstall sqlalchemy, alembic, pymysql
- [ ] Update requirements.txt
- [ ] Verify installation with `pip list`

**Configuration:**
- [ ] Update `app/core/config.py`
  - [ ] Add MONGODB_URL setting
  - [ ] Add MONGODB_DB_NAME setting
  - [ ] Remove DATABASE_URL validator
- [ ] Update `.env` file with MongoDB credentials
- [ ] Test config loads correctly

**Database Module:**
- [ ] Create `app/db/mongodb.py`
- [ ] Implement `connect_to_mongodb()` function
- [ ] Implement `close_mongodb_connection()` function
- [ ] Test connection in isolation

**Models Conversion:**
- [ ] Replace `app/models/user.py` with Beanie version
- [ ] Replace `app/models/message.py` with Beanie version
- [ ] Replace `app/models/oauth_state.py` with Beanie version
- [ ] Verify imports work
- [ ] Test model initialization

**Testing:**
- [ ] Test MongoDB connection works
- [ ] Verify Beanie models are correctly defined
- [ ] Test creating a document (in test script)

---

### Phase 2: Update Application Code (Day 2-3)

**Remove Old Files:**
- [ ] Delete `app/db/base.py`
- [ ] Delete `app/db/base_class.py`
- [ ] Delete `alembic/` directory
- [ ] Delete `alembic.ini` file

**Update Main Application:**
- [ ] Update `app/main.py` lifespan
  - [ ] Add MongoDB connection on startup
  - [ ] Add MongoDB close on shutdown
  - [ ] Remove SQLAlchemy references
- [ ] Test application starts without errors

**Update Endpoints:**
- [ ] Update `app/api/v1/endpoints/auth.py`
  - [ ] Remove `Session` dependency
  - [ ] Replace `db.query()` with `await Model.find_one()`
  - [ ] Replace `db.add()` with `await model.insert()`
  - [ ] Replace `db.commit()` with awaits
  - [ ] Replace `db.delete()` with `await model.delete()`
- [ ] Update `app/api/v1/endpoints/messages.py`
  - [ ] Remove `Session` dependency
  - [ ] Replace all queries with Beanie equivalents
  - [ ] Replace `.order_by()` with `.sort()`
  - [ ] Replace `.offset()/.limit()` with `.skip()/.limit()`
  - [ ] Update all create/update/delete operations

**Update Services:**
- [ ] Update `app/services/twitter.py`
  - [ ] Remove Session from __init__
  - [ ] Replace self.db.query() with direct Beanie calls
  - [ ] Replace self.db.add() with await model.insert()
  - [ ] Replace self.db.commit() with await model.save()
  - [ ] Remove self.db.rollback()
- [ ] Update `app/services/scheduler.py`
  - [ ] Remove SessionLocal import
  - [ ] Remove db session creation in jobs
  - [ ] Use Beanie models directly
  - [ ] Remove db.close() calls

**Schemas:**
- [ ] Review `app/schemas/user.py` - verify compatibility
- [ ] Review `app/schemas/message.py` - verify compatibility
- [ ] Make any necessary adjustments

**Code Cleanup:**
- [ ] Remove all SQLAlchemy imports
- [ ] Remove Session type hints
- [ ] Update all db parameter references
- [ ] Run linter and fix issues

**Local Testing:**
- [ ] Test application starts successfully
- [ ] Test MongoDB connection established
- [ ] Manually test each endpoint (Postman/curl)
  - [ ] OAuth authorization flow
  - [ ] OAuth callback
  - [ ] Fetch messages
  - [ ] Get messages list
  - [ ] Get single message
  - [ ] Update message
  - [ ] Delete message
  - [ ] Reply to message
  - [ ] DM reply
  - [ ] Generate AI response
- [ ] Test scheduler jobs run without errors
- [ ] Check logs for any errors

---

### Phase 3: Data Migration & Deployment (Day 4-5)

**Create Migration Script:**
- [ ] Create `scripts/migrate_mysql_to_mongodb.py`
- [ ] Test script in dry-run mode
- [ ] Verify script handles all models

**Backup:**
- [ ] Full MySQL database backup
- [ ] Store backup in secure location
- [ ] Document backup restore procedure
- [ ] Verify backup integrity

**Data Migration (Can be done before or after code deployment):**
- [ ] Run migration script
- [ ] Verify all users migrated (count check)
- [ ] Verify all messages migrated (count check)
- [ ] Verify all oauth_states migrated (count check)
- [ ] Spot-check 10-20 random records for accuracy
- [ ] Verify indexes were created in MongoDB

**Final Testing:**
- [ ] Run full test suite (if exists)
- [ ] Test all critical user flows end-to-end
- [ ] Performance testing
- [ ] Load testing (if needed)

**Deployment:**
- [ ] Commit all changes to git
- [ ] Create deployment tag/release
- [ ] Deploy to server
- [ ] Monitor startup logs
- [ ] Verify application started successfully
- [ ] Test MongoDB connection from production

**Post-Deployment Verification:**
- [ ] Test OAuth flow in production
- [ ] Test fetching messages
- [ ] Test creating/updating/deleting messages
- [ ] Verify scheduler is running
- [ ] Check for any error logs

**Monitoring (First 48 Hours):**
- [ ] Monitor application logs every few hours
- [ ] Check MongoDB Atlas metrics
- [ ] Verify no data corruption
- [ ] Monitor response times
- [ ] Check error rates
- [ ] Verify scheduled jobs run correctly

---

### Post-Migration Cleanup

**After 7 Days of Stable Operation:**
- [ ] Review MongoDB Atlas usage and optimize tier if needed
- [ ] Add any missing indexes based on query patterns
- [ ] Update README.md with new setup instructions
- [ ] Update API documentation (if needed)
- [ ] Archive MySQL database backup
- [ ] Schedule MySQL database decommissioning

**After 30 Days:**
- [ ] Decommission MySQL database (if no issues found)
- [ ] Remove MySQL backup scripts/configs
- [ ] Update deployment documentation
- [ ] Celebrate successful migration! 🎉

---

### Rollback Plan (If Needed)

**If Issues Arise During Testing (Phase 1-2):**
- [ ] `git revert` to previous commit
- [ ] Reinstall old dependencies
- [ ] Restart application
- Low risk, easy rollback

**If Issues Arise After Deployment (Phase 3):**
- [ ] Stop application
- [ ] `git revert` to previous commit
- [ ] Restore MySQL from backup (if data was modified)
- [ ] Reinstall old dependencies
- [ ] Deploy old version
- [ ] Restart application
- [ ] Verify everything works
- Higher risk, but manageable with backup

---

## 📚 Resources & Documentation

### MongoDB Atlas
- Setup guide: https://docs.atlas.mongodb.com/getting-started/
- Connection strings: https://docs.mongodb.com/manual/reference/connection-string/
- Security best practices: https://docs.atlas.mongodb.com/security-best-practices/

### Beanie ODM
- Documentation: https://beanie-odm.dev/
- Tutorial: https://beanie-odm.dev/tutorial/
- API Reference: https://beanie-odm.dev/api/

### Motor (Async Driver)
- Documentation: https://motor.readthedocs.io/
- Tutorial: https://motor.readthedocs.io/en/stable/tutorial-asyncio.html

### MongoDB
- Query operators: https://docs.mongodb.com/manual/reference/operator/query/
- Aggregation: https://docs.mongodb.com/manual/aggregation/
- Indexes: https://docs.mongodb.com/manual/indexes/
- Transactions: https://docs.mongodb.com/manual/core/transactions/

---

## 🎯 Recommended Next Steps

### Getting Started

**Immediate Action Items**:
1. **Set up MongoDB Atlas account** (if not done already)
2. **Create a new branch** in git: `git checkout -b feature/mongodb-migration`
3. **Follow Phase 1** of the checklist
4. **Test thoroughly** before moving to Phase 2

**Best Practices**:
- Commit after each major step
- Test frequently
- Keep the MySQL backup safe until migration is complete
- Document any issues or deviations from the plan

---

## 💡 Final Recommendations

Based on your codebase analysis and fast-track approach:

### 1. **Use Beanie ODM, not PyMongo directly**
   - ✅ Minimal code changes from SQLAlchemy
   - ✅ Type safety with Pydantic
   - ✅ Async-first design
   - ✅ Familiar ORM-like syntax

### 2. **Migration Timeline**
   - **Day 1**: MongoDB setup + Install dependencies + Create models
   - **Day 2**: Update all application code
   - **Day 3**: Testing and bug fixes
   - **Day 4**: Data migration script + Dry run
   - **Day 5**: Final testing + Deployment

### 3. **Testing Strategy**
   - Test each endpoint manually after code changes
   - Create a test checklist (provided in Phase 2)
   - Run the application locally with MongoDB before deploying
   - Keep MySQL running until confident in MongoDB setup

### 4. **Key Success Factors**
   - ✅ **Good MySQL backup** before starting data migration
   - ✅ **Test connection** to MongoDB Atlas first
   - ✅ **Update one file at a time** during Phase 2
   - ✅ **Test after each file change** to catch issues early
   - ✅ **Document any deviations** from the plan
   - ✅ **Monitor closely** for first 48 hours after deployment

### 5. **Risk Mitigation**
   - Work in a feature branch
   - Commit frequently with descriptive messages
   - Test locally before deploying
   - Have rollback plan ready (revert + restore MySQL)
   - Keep MySQL database for 30 days after successful migration

### 6. **Common Pitfalls to Avoid**
   - ❌ Don't forget to update `.env` with MongoDB URL
   - ❌ Don't skip testing after code changes
   - ❌ Don't delete MySQL database immediately after migration
   - ❌ Don't forget to remove `Session` dependencies from endpoints
   - ❌ Don't forget to update `db.commit()` to `await model.save()`
   - ❌ Don't forget indexes (defined in model Settings)

### 7. **When to Ask for Help**
   - MongoDB connection issues → Check Atlas network settings
   - Beanie initialization errors → Verify model imports in mongodb.py
   - Query translation issues → Consult Beanie docs or examples in this plan
   - Performance issues → Review indexes and query patterns

---

## 📞 Support & Questions

If issues arise during migration:

1. **MongoDB Atlas Support**: Available in Atlas console
2. **Beanie GitHub**: https://github.com/roman-right/beanie/issues
3. **Community**: MongoDB community forums
4. **Documentation**: Always check official docs first

---

## 📄 Document Maintenance

- **Created**: October 29, 2025
- **Last Updated**: October 29, 2025
- **Migration Method**: Fast-Track Complete Replacement
- **Status**: Ready for Implementation
- **Next Review**: After each phase completion

---

## ✨ Success Criteria

The migration will be considered successful when:

- [ ] MongoDB Atlas cluster configured and accessible
- [ ] All Beanie models created and tested
- [ ] All application code updated (no SQLAlchemy dependencies)
- [ ] All data migrated correctly (100% data integrity verified)
- [ ] Application starts and runs without errors
- [ ] All endpoints tested and working
- [ ] Scheduler jobs running correctly
- [ ] No critical bugs after 48 hours
- [ ] Performance is equal or better than MySQL
- [ ] Documentation updated (README, deployment guides)
- [ ] MySQL database archived (after 30-day retention)

---

## 📊 Quick Reference

### Fast-Track Migration Summary

**Total Duration**: 3-5 days  
**Phases**: 3 (Setup, Code Update, Migration & Deployment)  
**Downtime**: 1-2 hours during final deployment  
**Risk Level**: Low (with proper backups)  
**Rollback Time**: ~1 hour (revert code + restore MySQL)

### Key Technologies
- **From**: SQLAlchemy + PyMySQL + MySQL
- **To**: Beanie + Motor + MongoDB Atlas

### Files to Create
- `app/db/mongodb.py` (new connection module)
- `scripts/migrate_mysql_to_mongodb.py` (data migration)

### Files to Update
- `app/core/config.py` (configuration)
- `app/main.py` (initialization)
- `app/models/*.py` (3 files: user, message, oauth_state)
- `app/api/v1/endpoints/auth.py` (OAuth endpoints)
- `app/api/v1/endpoints/messages.py` (message endpoints)
- `app/services/twitter.py` (Twitter service)
- `app/services/scheduler.py` (scheduler service)
- `requirements.txt` (dependencies)
- `.env` (environment variables)

### Files to Delete
- `app/db/base.py`
- `app/db/base_class.py`
- `alembic/` (entire directory)
- `alembic.ini`

### Critical Commands
```bash
# Install dependencies
pip install motor==3.3.2 beanie==1.23.6 pymongo==4.6.1

# Uninstall old dependencies
pip uninstall sqlalchemy alembic pymysql -y

# Backup MySQL
mysqldump -u user -p database_name > backup.sql

# Test MongoDB connection
python -c "from pymongo import MongoClient; client = MongoClient('your_connection_string'); print('Connected!')"
```

---

**Ready to start? Follow the checklist step-by-step. Good luck with the migration! 🚀**


