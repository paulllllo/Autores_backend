from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.core.deps import get_current_user
from app.models.account import Account  # Changed from User
from app.models.app_user import AppUser
from app.models.oauth_state import OAuthState
from app.models.enums import AccountSyncStatus
from app.schemas.user import UserCreate, UserInDB  # Keep for backward compatibility
from app.schemas.auth import (
    TwitterAuthorizationResponse,
    TwitterCallbackResponse,
    TokenRefreshResponse
)
import httpx
import secrets
import base64
import hashlib
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlencode
import asyncio
from typing import Optional

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

@router.post("/twitter/authorize", response_model=TwitterAuthorizationResponse)
async def twitter_authorize(current_user: AppUser = Depends(get_current_user)):
    """
    Generate Twitter OAuth 2.0 authorization URL with PKCE
    Requires JWT authentication - links Twitter account to current user
    
    Returns JSON with authorization_url that frontend should redirect user to
    """
    # Generate PKCE values
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    
    # Generate and store state with app user ID
    state = secrets.token_urlsafe(16)
    oauth_state = OAuthState(
        state=state,
        code_verifier=code_verifier,
        app_user_id=current_user.id,  # Link to current user
        created_at=datetime.utcnow()
    )
    await oauth_state.insert()
    
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
    
    return TwitterAuthorizationResponse(
        authorization_url=auth_url,
        message="Redirect user to this URL to authorize their Twitter account"
    )

@router.get("/twitter/callback", response_model=TwitterCallbackResponse)
async def twitter_callback(
    code: str,
    state: str
):
    """
    Handle Twitter OAuth 2.0 callback
    Exchanges authorization code for access tokens and creates/updates Twitter account
    """

    print('called back...')
    try:
        # Retrieve stored state and code_verifier
        oauth_state = await OAuthState.find_one(
            OAuthState.state == state,
            OAuthState.created_at > datetime.utcnow() - timedelta(minutes=10)
        )
        
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
            
            # Extract user information
            twitter_id = str(user_data['data']['id'])
            twitter_username = user_data['data'].get('username', '')
            display_name = user_data['data'].get('name', '')
            profile_image_url = user_data['data'].get('profile_image_url')
            
            # Create or update account in database
            account = await Account.find_one(Account.twitter_id == twitter_id)
            if not account:
                # New account - link to app user from OAuth state
                account = Account(
                    id=str(uuid.uuid4()),
                    twitter_id=twitter_id,
                    twitter_username=twitter_username,
                    display_name=display_name,
                    profile_image_url=profile_image_url,
                    access_token=token_data['access_token'],
                    refresh_token=token_data.get('refresh_token'),
                    token_expires_at=datetime.utcnow() + timedelta(seconds=token_data['expires_in']),
                    is_active=True,
                    sync_status=AccountSyncStatus.ACTIVE,
                    added_by=oauth_state.app_user_id,  # Link to app user
                    added_at=datetime.utcnow()
                )
                await account.insert()
                message = f"Successfully added Twitter account @{twitter_username} for tracking"
            else:
                # Reauthorization - update tokens and info
                account.access_token = token_data.get('access_token')
                account.refresh_token = token_data.get('refresh_token')
                account.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
                account.twitter_username = twitter_username
                account.display_name = display_name
                account.profile_image_url = profile_image_url
                account.sync_status = AccountSyncStatus.ACTIVE
                account.error_message = None
                account.updated_at = datetime.utcnow()
                # Update added_by if it's not set
                if not account.added_by and oauth_state.app_user_id:
                    account.added_by = oauth_state.app_user_id
                await account.save()
                message = f"Successfully reauthorized Twitter account @{twitter_username}"
            
            # Clean up used state
            await oauth_state.delete()
            
            return TwitterCallbackResponse(
                message=message,
                account={
                    "id": account.id,
                    "twitter_id": account.twitter_id,
                    "twitter_username": account.twitter_username,
                    "display_name": account.display_name,
                    "is_active": account.is_active
                }
            )
            
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

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    account_id: str
):
    """
    Refresh Twitter access token for an account
    Returns new token expiration time
    """
    try:
        account = await Account.find_one(Account.id == account_id)
        if not account or not account.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found or no refresh token available"
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
            
            # Update account's tokens
            account.access_token = token_data['access_token']
            account.refresh_token = token_data.get('refresh_token', account.refresh_token)
            account.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
            account.sync_status = AccountSyncStatus.ACTIVE
            account.error_message = None
            account.updated_at = datetime.utcnow()
            
            await account.save()
            
            return TokenRefreshResponse(
                message="Successfully refreshed token",
                expires_at=account.token_expires_at.isoformat(),
                account_username=account.twitter_username
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to refresh token: {str(e)}"
        ) 