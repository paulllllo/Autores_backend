from datetime import datetime, timedelta
import tweepy
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.message import Message
from app.models.user import User
import uuid


class TwitterService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_client(self, access_token: str) -> tweepy.Client:
        """
        Create a Twitter client with the given access token
        """
        return tweepy.Client(access_token)
    
    def fetch_mentions(self, user: User) -> list[Message]:
        """
        Fetch new mentions for a user and store them in the database
        """
        client = self.get_client(user.access_token)
        
        try:
            # Get user's mentions
            mentions = client.get_users_mentions(
                user.twitter_id,
                max_results=100,
                tweet_fields=["created_at", "author_id", "text"]
            )
            
            new_messages = []
            
            for mention in mentions.data or []:
                # Check if message already exists
                existing_message = self.db.query(Message).filter(
                    Message.id == str(mention.id)
                ).first()
                
                if not existing_message:
                    # Create new message
                    message = Message(
                        id=str(mention.id),
                        timestamp=mention.created_at,
                        user=str(mention.author_id),
                        text=mention.text,
                        status="pending"
                    )
                    self.db.add(message)
                    new_messages.append(message)
            
            self.db.commit()
            return new_messages
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to fetch mentions: {str(e)}")
    
    def refresh_token(self, user: User) -> bool:
        """
        Refresh the user's Twitter access token
        """
        try:
            auth = tweepy.OAuth2UserHandler(
                client_id=settings.TWITTER_API_KEY,
                client_secret=settings.TWITTER_API_SECRET,
                redirect_uri=settings.TWITTER_CALLBACK_URL
            )
            
            # Refresh the token
            new_token = auth.refresh_token(user.refresh_token)
            
            # Update user's tokens
            user.access_token = new_token["access_token"]
            user.refresh_token = new_token["refresh_token"]
            user.token_expires_at = datetime.utcnow() + timedelta(seconds=new_token["expires_in"])
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to refresh token: {str(e)}") 