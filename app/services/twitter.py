from datetime import datetime, timedelta
import httpx
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.message import Message
from app.models.user import User
import uuid


class TwitterService:
    def __init__(self, db: Session):
        self.db = db
    
    async def verify_token(self, access_token: str, token_expires_at: datetime) -> bool:
        """
        Verify if the access token is still valid
        """
        try:
            # Check if token is expired based on expiration time
            if datetime.utcnow() >= token_expires_at:
                return False

            # Verify token with Twitter API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.twitter.com/2/users/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                return response.status_code == 200
        except Exception:
            return False
    
    async def refresh_token(self, user: User) -> bool:
        """
        Refresh the user's Twitter access token
        """
        try:
            print('refreshing token...')
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.twitter.com/2/oauth2/token",
                    data={
                        "refresh_token": user.refresh_token,
                        "grant_type": "refresh_token",
                        "client_id": settings.TWITTER_CLIENT_ID,
                        "client_secret": settings.TWITTER_CLIENT_SECRET
                    }
                )

                print('response in refresh_token: ', response.json())
                
                if response.status_code != 200:
                    return False
                
                token_data = response.json()
                
                # Update user's tokens with expiration based on time from twitter
                user.access_token = token_data['access_token']
                user.refresh_token = token_data.get('refresh_token', user.refresh_token)
                user.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
                # user.token_expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                
                self.db.commit()
                return True
                
        except Exception:
            return False
    
    async def fetch_mentions(self, user: User) -> list[Message]:
        """
        Fetch new mentions for a user and store them in the database
        """
        try:
            # Verify token and refresh if needed
            if not await self.verify_token(user.access_token, user.token_expires_at):
                if not await self.refresh_token(user):
                    raise Exception("Failed to refresh token")


            print('user.twitter_id: ', user.twitter_id)
            print('user.access_token: ', user.access_token)
            
            async with httpx.AsyncClient() as client:
                # Get user's mentions
                response = await client.get(
                    f"https://api.twitter.com/2/users/{user.twitter_id}/mentions",
                    headers={"Authorization": f"Bearer {user.access_token}"},
                    params={
                        "max_results": 100,
                        "tweet.fields": "created_at,author_id,text"
                    }
                )

                print('response: ', response.json())
                
                if response.status_code != 200:
                    raise Exception("Failed to fetch mentions", response.json())
                
                mentions_data = response.json()
                new_messages = []
                
                for mention in mentions_data.get('data', []):
                    # Check if message already exists
                    existing_message = self.db.query(Message).filter(
                        Message.id == str(mention['id'])
                    ).first()
                    
                    if not existing_message:
                        # Create new message
                        message = Message(
                            id=str(mention['id']),
                            timestamp=datetime.fromisoformat(mention['created_at'].replace('Z', '+00:00')),
                            user=str(mention['author_id']),
                            text=mention['text'],
                            status="pending"
                        )
                        self.db.add(message)
                        new_messages.append(message)
                
                self.db.commit()
                return new_messages
                
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to fetch mentions: {str(e)}")
    
    async def reply_to_tweet(self, access_token: str, tweet_id: str, text: str) -> dict:
        """
        Reply to a tweet using the Twitter API
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.twitter.com/2/tweets",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={
                        "text": text,
                        "reply": {
                            "in_reply_to_tweet_id": tweet_id
                        }
                    }
                )
                
                if response.status_code != 201:
                    raise Exception("Failed to create tweet")
                
                return response.json()
                
        except Exception as e:
            raise Exception(f"Failed to reply to tweet: {str(e)}") 