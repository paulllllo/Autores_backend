#!/usr/bin/env python3
"""
Quick test script to verify MongoDB connection
Usage: python scripts/test_connection.py
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.mongodb import connect_to_mongodb, close_mongodb_connection
from app.core.config import settings


async def test_mongodb_connection():
    """Test MongoDB connection and model initialization"""
    print("="*60)
    print("MongoDB Connection Test")
    print("="*60)
    print()
    
    # Show configuration
    print("📋 Configuration:")
    print(f"   MongoDB URL: {settings.MONGODB_URL[:30]}..." if len(settings.MONGODB_URL) > 30 else f"   MongoDB URL: {settings.MONGODB_URL}")
    print(f"   Database Name: {settings.MONGODB_DB_NAME}")
    print()
    
    # Test connection
    print("🔌 Testing connection...")
    try:
        await connect_to_mongodb()
        print("✅ Successfully connected to MongoDB!")
        print("✅ All models initialized successfully!")
        print()
        
        # Test a simple query
        print("🧪 Testing database operations...")
        from app.models.user import User
        from app.models.message import Message
        from app.models.oauth_state import OAuthState
        
        # Count documents
        user_count = await User.count()
        message_count = await Message.count()
        oauth_count = await OAuthState.count()
        
        print(f"   Users: {user_count}")
        print(f"   Messages: {message_count}")
        print(f"   OAuth States: {oauth_count}")
        print()
        
        print("="*60)
        print("✅ All tests passed! MongoDB is ready to use.")
        print("="*60)
        
        await close_mongodb_connection()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed!")
        print()
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print()
        
        # Provide helpful hints
        if "authentication failed" in str(e).lower():
            print("💡 Hint: Check your username and password in MONGODB_URL")
        elif "network" in str(e).lower() or "timeout" in str(e).lower():
            print("💡 Hint: Check MongoDB Atlas network access settings")
        elif "rfc 3986" in str(e).lower() or "escape" in str(e).lower():
            print("💡 Hint: Your MongoDB URL format is incorrect")
            print("   See FIX_MONGODB_URL.md for help")
        
        print()
        print("="*60)
        print("❌ Tests failed. Please fix the issues above.")
        print("="*60)
        
        return False


if __name__ == "__main__":
    print()
    success = asyncio.run(test_mongodb_connection())
    print()
    
    if success:
        print("🎉 You're ready to start the application!")
        print()
        print("Next steps:")
        print("  1. python app/main.py")
        print("  2. Open http://localhost:8000")
        print("  3. Run migration: python scripts/migrate_mysql_to_mongodb.py")
        print()
    else:
        print("⚠️  Please fix the connection issues before proceeding.")
        print()
        print("See these files for help:")
        print("  - FIX_MONGODB_URL.md")
        print("  - CURRENT_STATUS.md")
        print()
    
    sys.exit(0 if success else 1)

