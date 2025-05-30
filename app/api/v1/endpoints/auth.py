from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.base import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserInDB
import httpx
import secrets
import base64
import hashlib
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlencode

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

@router.post("/twitter/authorize")
async def twitter_authorize():
    """
    Initiate Twitter OAuth 2.0 flow with PKCE
    """
    # Generate PKCE values
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    
    # Store code_verifier in session or database for later use
    # For now, we'll store it in memory (in production, use secure session storage)
    state = secrets.token_urlsafe(16)
    
    # Construct authorization URL
    params = {
        'response_type': 'code',
        'client_id': settings.TWITTER_API_KEY,
        'redirect_uri': settings.TWITTER_CALLBACK_URL,
        'scope': 'tweet.read tweet.write users.read offline.access',
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    
    auth_url = f"https://twitter.com/i/oauth2/authorize?{urlencode(params)}"
    
    return {
        "authorization_url": auth_url,
        "code_verifier": code_verifier,  # In production, store this securely
        "state": state
    }

@router.get("/twitter/callback")
async def twitter_callback(
    code: str,
    state: str,
    code_verifier: str,
    db: Session = Depends(get_db)
):
    """
    Handle Twitter OAuth 2.0 callback
    """
    try:
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://api.twitter.com/2/oauth2/token",
                data={
                    "code": code,
                    "grant_type": "authorization_code",
                    "client_id": settings.TWITTER_API_KEY,
                    "redirect_uri": settings.TWITTER_CALLBACK_URL,
                    "code_verifier": code_verifier
                }
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get access token"
                )
            
            token_data = token_response.json()
            
            # Get user info
            user_response = await client.get(
                "https://api.twitter.com/2/users/me",
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )
            
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info"
                )
            
            user_data = user_response.json()
            
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
                db_user.access_token = token_data['access_token']
                db_user.refresh_token = token_data.get('refresh_token')
                db_user.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
            
            db.commit()
            
            return {
                "message": "Successfully authenticated with Twitter",
                "user": {
                    "id": db_user.id,
                    "twitter_id": db_user.twitter_id
                }
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to authenticate with Twitter: {str(e)}"
        )

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
            response = await client.post(
                "https://api.twitter.com/2/oauth2/token",
                data={
                    "refresh_token": user.refresh_token,
                    "grant_type": "refresh_token",
                    "client_id": settings.TWITTER_API_KEY
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