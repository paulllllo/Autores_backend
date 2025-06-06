from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
import httpx
import base64
import secrets
import hashlib
import urllib.parse
from config import get_settings
import uvicorn
import time

app = FastAPI(title="Twitter OAuth2 Direct Demo")
settings = get_settings()

# Store state and code verifier in memory (in production, use proper session management)
oauth_state = None
code_verifier = None
access_token = None
refresh_token = None
token_expiry = None

def generate_code_verifier():
    """Generate a code verifier for PKCE"""
    return secrets.token_urlsafe(32)

def generate_code_challenge(verifier):
    """Generate a code challenge from the verifier"""
    sha256_hash = hashlib.sha256(verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(sha256_hash).decode('utf-8').rstrip('=')

async def refresh_access_token():
    """Refresh the access token using the refresh token"""
    global access_token, refresh_token, token_expiry
    
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token available")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://api.twitter.com/2/oauth2/token',
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': refresh_token,
                    'client_id': settings.TWITTER_CLIENT_ID,
                },
                auth=(settings.TWITTER_CLIENT_ID, settings.TWITTER_CLIENT_SECRET)
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Token refresh failed: {response.text}"
                )
            
            token_data = response.json()
            access_token = token_data.get('access_token')
            refresh_token = token_data.get('refresh_token')
            token_expiry = time.time() + token_data.get('expires_in', 7200)
            
            print(f"Tokens refreshed successfully")
            return True
            
    except Exception as e:
        print(f"Token refresh error: {str(e)}")
        return False

async def ensure_valid_token():
    """Ensure we have a valid access token, refresh if necessary"""
    global access_token, token_expiry
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated. Please login first.")
    
    # Check if token is expired or about to expire (within 5 minutes)
    if not token_expiry or time.time() > (token_expiry - 300):
        success = await refresh_access_token()
        if not success:
            raise HTTPException(status_code=401, detail="Token refresh failed. Please login again.")

@app.get("/")
async def root():
    return {"message": "Welcome to Twitter OAuth2 Direct Demo. Go to /login to start"}

@app.get("/login")
async def login():
    global oauth_state, code_verifier
    
    # Generate PKCE values
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    oauth_state = secrets.token_urlsafe(16)
    
    # Construct authorization URL
    params = {
        'response_type': 'code',
        'client_id': settings.TWITTER_CLIENT_ID,
        'redirect_uri': settings.TWITTER_REDIRECT_URI,
        'scope': ' '.join(settings.TWITTER_SCOPES),
        'state': oauth_state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    
    auth_url = f"https://twitter.com/i/oauth2/authorize?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=auth_url)

@app.get("/callback")
async def callback(request: Request):
    global oauth_state, code_verifier, access_token, refresh_token, token_expiry
    
    # Get query parameters
    params = dict(request.query_params)
    code = params.get('code')
    state = params.get('state')
    
    if not code or not state or state != oauth_state:
        raise HTTPException(status_code=400, detail="Invalid callback parameters")
    
    try:
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                'https://api.twitter.com/2/oauth2/token',
                data={
                    'code': code,
                    'grant_type': 'authorization_code',
                    'client_id': settings.TWITTER_CLIENT_ID,
                    'redirect_uri': settings.TWITTER_REDIRECT_URI,
                    'code_verifier': code_verifier
                },
                auth=(settings.TWITTER_CLIENT_ID, settings.TWITTER_CLIENT_SECRET)
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Token request failed: {token_response.text}"
                )
            
            token_data = token_response.json()
            access_token = token_data.get('access_token')
            refresh_token = token_data.get('refresh_token')
            token_expiry = time.time() + token_data.get('expires_in', 7200)
            
            print(f'Tokens received successfully')
            
            # Get user information
            user_response = await client.get(
                'https://api.twitter.com/2/users/me',
                headers={'Authorization': f'Bearer {access_token}'},
                params={'user.fields': 'profile_image_url,description,public_metrics'}
            )

            print(f'user_response: {user_response}')
            
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"User info request failed: {user_response.text}"
                )
            
            user_data = user_response.json()
            
            return {
                "message": "Successfully authenticated!",
                "user": user_data,
                "access_token": token_data
            }
            
    except Exception as e:
        print(f"Detailed error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tweet")
async def post_tweet(request: Request):
    try:
        # Ensure we have a valid token
        await ensure_valid_token()
        
        # Get tweet text from request body
        tweet_text = "Hello world, My first tweet"
        
        if not tweet_text:
            raise HTTPException(status_code=400, detail="Tweet text is required")
        
        # Post tweet using Twitter API v2
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://api.twitter.com/2/tweets',
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                },
                json={'text': tweet_text}
            )
            
            if response.status_code != 201:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tweet request failed: {response.text}"
                )
            
            tweet_data = response.json()
            
            return {
                "message": "Tweet posted successfully!",
                "tweet_id": tweet_data['data']['id']
            }
            
    except Exception as e:
        print(f"Tweet error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main_direct:app", host="0.0.0.0", port=8000, reload=True)