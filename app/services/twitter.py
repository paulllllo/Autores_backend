from datetime import datetime, timedelta
import httpx
from app.core.config import settings
from app.models.message import Message, TwitterUser, TrackedAccount
from app.models.account import Account  # Changed from User
from app.models.enums import AccountSyncStatus, MessageStatus
import uuid
import base64


class TwitterService:
    def __init__(self):
        pass
    
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
    
    async def refresh_token(self, account: Account) -> bool:
        """
        Refresh the account's Twitter access token
        """
        try:
            print('refreshing token...')
            async with httpx.AsyncClient() as client:
                # Create Basic Auth header with client credentials
                auth_header = f"Basic {base64.b64encode(f'{settings.TWITTER_CLIENT_ID}:{settings.TWITTER_CLIENT_SECRET}'.encode()).decode()}"
                
                response = await client.post(
                    "https://api.twitter.com/2/oauth2/token",
                    headers={"Authorization": auth_header},
                    data={
                        "refresh_token": account.refresh_token,
                        "grant_type": "refresh_token"
                    }
                )

                print('response in refresh_token: ', response.json())
                
                if response.status_code != 200:
                    return False
                
                token_data = response.json()
                
                # Update account's tokens with expiration based on time from twitter
                account.access_token = token_data['access_token']
                account.refresh_token = token_data.get('refresh_token', account.refresh_token)
                account.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
                account.sync_status = AccountSyncStatus.ACTIVE
                account.error_message = None
                
                await account.save()
                return True
                
        except Exception:
            return False
    
    async def fetch_mentions(self, account: Account) -> list[Message]:
        """
        Fetch new mentions for an account and store them in the database
        """
        try:
            # Verify token and refresh if needed
            if not await self.verify_token(account.access_token, account.token_expires_at):
                if not await self.refresh_token(account):
                    raise Exception("Failed to refresh token")


            print('account.twitter_id: ', account.twitter_id)
            print('account.access_token: ', account.access_token)
            
            async with httpx.AsyncClient() as client:
                # Get account's mentions with user data
                response = await client.get(
                    f"https://api.twitter.com/2/users/{account.twitter_id}/mentions",
                    headers={"Authorization": f"Bearer {account.access_token}"},
                    params={
                        "max_results": 100,
                        "tweet.fields": "created_at,author_id,text",
                        "expansions": "author_id",
                        "user.fields": "username,name,profile_image_url"
                    }
                )

                print('response: ', response.json())
                
                if response.status_code != 200:
                    raise Exception("Failed to fetch mentions", response.json())
                
                mentions_data = response.json()
                new_messages = []
                
                # Build user lookup from includes
                users_data = {u['id']: u for u in mentions_data.get('includes', {}).get('users', [])}
                
                for mention in mentions_data.get('data', []):
                    # Check if message already exists
                    tweet_id = str(mention['id'])
                    existing_message = await Message.find_one(Message.tweet_id == tweet_id)
                    
                    if not existing_message:
                        # Get author info
                        author_id = str(mention['author_id'])
                        author_data = users_data.get(author_id, {})
                        
                        # Create sender object
                        sender = TwitterUser(
                            twitter_id=author_id,
                            username=author_data.get('username', f'user_{author_id}'),
                            display_name=author_data.get('name'),
                            profile_image_url=author_data.get('profile_image_url')
                        )
                        
                        # Create sent_to object (tracked account)
                        sent_to = TrackedAccount(
                            account_id=account.id,
                            twitter_id=account.twitter_id,
                            username=account.twitter_username,
                            display_name=account.display_name
                        )
                        
                        # Create new message with updated structure
                        message = Message(
                            id=str(uuid.uuid4()),  # Generate new UUID for MongoDB _id
                            tweet_id=tweet_id,
                            timestamp=datetime.fromisoformat(mention['created_at'].replace('Z', '+00:00')),
                            text=mention['text'],
                            sender=sender,
                            sent_to=sent_to,
                            status=MessageStatus.PENDING,
                            user=author_id  # Keep for backward compatibility
                        )
                        await message.insert()
                        new_messages.append(message)
                
                # Update account's mention count
                account.total_mentions_tracked += len(new_messages)
                await account.save()
                
                return new_messages
                
        except Exception as e:
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

    async def send_dm(self, access_token: str, recipient_id: str, text: str) -> dict:
        """
        Send a direct message to a Twitter user using Twitter API v2
        """
        try:
            async with httpx.AsyncClient() as client:
                # First, create a DM conversation
                response = await client.post(
                    f"https://api.twitter.com/2/dm_conversations/with/{recipient_id}/messages",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": text
                    }
                )

                print('response in send_dm', response.json())
                
                if response.status_code != 201:
                    error_msg = response.json().get('detail', 'Unknown error')
                    raise Exception(f"Failed to send DM: {error_msg}")
                
                return response.json()
                
        except Exception as e:
            raise Exception(f"Failed to send DM: {str(e)}") 