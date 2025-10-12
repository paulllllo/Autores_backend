from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.base import get_db
from app.models.user import User
from app.models.oauth_state import OAuthState
from app.schemas.user import UserCreate, UserInDB
import httpx
import secrets
import base64
import hashlib
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlencode
import asyncio

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def generate_code_verifier():
    """Generate a random code verifier for PKCE"""
    code_verifier = secrets.token_urlsafe(32)
    return code_verifier

def generate_code_challenge(code_verifier):
    """Generate code challenge from verifier using SHA256"""
    sha256_hash = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(sha256_hash).decode('utf-8').rstrip('=')
    return code_challenge

@router.get("/twitter/authorize")
async def twitter_authorize(db: Session = Depends(get_db)):
    """
    Initiate Twitter OAuth 2.0 flow with PKCE
    """
    # Generate PKCE values
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    
    # Generate and store state
    state = secrets.token_urlsafe(16)
    oauth_state = OAuthState(
        state=state,
        code_verifier=code_verifier,
        created_at=datetime.utcnow()
    )
    db.add(oauth_state)
    db.commit()
    
    # Construct authorization URL
    params = {
        'response_type': 'code',
        'client_id': settings.TWITTER_CLIENT_ID,
        'redirect_uri': settings.TWITTER_CALLBACK_URL,
        'scope': settings.TWITTER_SCOPE,
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    
    auth_url = f"https://twitter.com/i/oauth2/authorize?{urlencode(params)}"
    
    return RedirectResponse(auth_url)

@router.get("/twitter/callback")
async def twitter_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """
    Handle Twitter OAuth 2.0 callback
    """

    print('called back...')
    try:
        # Retrieve stored state and code_verifier
        oauth_state = db.query(OAuthState).filter(
            OAuthState.state == state,
            OAuthState.created_at > datetime.utcnow() - timedelta(minutes=10)
        ).first()
        
        if not oauth_state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state"
            )

        print('code: ', code)
        print('state: ', state)
        print('oauth_state: ', oauth_state)
        
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            # Create Basic Auth header with client credentials
            auth_string = f"{settings.TWITTER_CLIENT_ID}:{settings.TWITTER_CLIENT_SECRET}"
            auth_bytes = auth_string.encode('ascii')
            base64_auth = base64.b64encode(auth_bytes).decode('ascii')
            headers = {
                "Authorization": f"Basic {base64_auth}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            token_response = await client.post(
                "https://api.twitter.com/2/oauth2/token",
                headers=headers,
                data={
                    "code": code,
                    "grant_type": "authorization_code",
                    "client_id": settings.TWITTER_CLIENT_ID,
                    "redirect_uri": settings.TWITTER_CALLBACK_URL,
                    "code_verifier": oauth_state.code_verifier
                }
            )

            print('token_response: ', token_response.json())
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get access token"
                )
            
            token_data = token_response.json()
            
            print('getting user info... ')
            # Get user info with retry
            user_response = await get_user_info_with_retry(client, token_data['access_token'])

            print('user_response: ', user_response)
            
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info"
                )
            
            user_data = user_response.json()

            print('user_data: ', user_data)
            
            # Create or update user in database
            db_user = db.query(User).filter(User.twitter_id == str(user_data['data']['id'])).first()
            if not db_user:
                db_user = User(
                    id=str(uuid.uuid4()),
                    twitter_id=str(user_data['data']['id']),
                    access_token=token_data['access_token'],
                    refresh_token=token_data.get('refresh_token'),
                    token_expires_at=datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
                )
                db.add(db_user)
            else:
                db_user.access_token = token_data.get('access_token')
                db_user.refresh_token = token_data.get('refresh_token')
                db_user.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
            
            # Clean up used state
            db.delete(oauth_state)
            db.commit()
            
            return {
                "message": "Successfully authenticated with Twitter",
                "user": {
                    "id": db_user.id,
                    "twitter_id": db_user.twitter_id
                }
            }
            
    except Exception as e:
        print('Error in twitter_callback:', str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to authenticate with Twitter: {str(e)}"
        )

async def get_user_info_with_retry(client, token, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = await client.get(
                "https://api.twitter.com/2/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )

            print('response in get user info: ', response)

            if response.status_code == 429:
                wait_time = 2 ** attempt  # Exponential backoff
                await asyncio.sleep(wait_time)
                continue
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(2 ** attempt)

@router.post("/refresh")
async def refresh_token(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Refresh Twitter access token
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or no refresh token available"
            )
        
        async with httpx.AsyncClient() as client:
            # Create Basic Auth header with client credentials
            auth_header = f"Basic {base64.b64encode(f'{settings.TWITTER_CLIENT_ID}:{settings.TWITTER_CLIENT_SECRET}'.encode()).decode()}"
            
            response = await client.post(
                "https://api.twitter.com/2/oauth2/token",
                headers={"Authorization": auth_header},
                data={
                    "refresh_token": user.refresh_token,
                    "grant_type": "refresh_token"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to refresh token"
                )
            
            token_data = response.json()
            
            # Update user's tokens
            user.access_token = token_data['access_token']
            user.refresh_token = token_data.get('refresh_token', user.refresh_token)
            user.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
            
            db.commit()
            
            return {
                "message": "Successfully refreshed token",
                "expires_at": user.token_expires_at
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to refresh token: {str(e)}"
        ) 