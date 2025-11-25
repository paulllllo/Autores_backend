# How to Add a Twitter Account for Tracking

## Overview

Adding a Twitter account requires **OAuth 2.0 authorization** through Twitter. This ensures secure access to the user's Twitter account and automatically obtains the necessary access tokens.

## Architecture Decision

**Why no direct POST /accounts/ endpoint?**
- Twitter accounts require OAuth tokens (access_token, refresh_token) that can only be obtained through Twitter's official OAuth flow
- Direct account creation would be insecure and wouldn't provide valid tokens
- The OAuth flow is split between `/auth/twitter/authorize` (initiation) and `/auth/twitter/callback` (completion)

## Complete Flow to Add a Twitter Account

### Step 1: User Authentication (JWT)

First, the user must be logged into your application:

```http
POST /api/v1/users/login
Content-Type: application/x-www-form-urlencoded

username=johndoe&password=securepass123
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Store this token for subsequent requests.

### Step 2: Request Twitter Authorization URL

**Changed from GET to POST** - Now returns JSON instead of redirecting

```http
POST /api/v1/auth/twitter/authorize
Authorization: Bearer <your_jwt_token>
```

**Response:**
```json
{
  "authorization_url": "https://twitter.com/i/oauth2/authorize?response_type=code&client_id=...",
  "message": "Redirect user to this URL to authorize their Twitter account"
}
```

**What happens behind the scenes:**
1. Validates your JWT token
2. Generates PKCE values (code_verifier, code_challenge) for security
3. Creates an `OAuthState` document with:
   - Random `state` parameter
   - `code_verifier` (for PKCE)
   - `app_user_id` (your user ID from JWT) ✨
4. Returns the Twitter authorization URL

### Step 3: Redirect User to Twitter

The frontend redirects the user to the `authorization_url`:

```javascript
const response = await fetch('http://localhost:8000/api/v1/auth/twitter/authorize', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const data = await response.json();

// Redirect user to Twitter
window.location.href = data.authorization_url;
```

The user will see Twitter's authorization page:
> "Authorize [Your App Name] to access your Twitter account?"

### Step 4: User Authorizes on Twitter

User clicks **"Authorize"** on Twitter's page.

### Step 5: Twitter Redirects Back (Automatic)

Twitter redirects to your callback URL with a code:

```
GET http://your-app.com/api/v1/auth/twitter/callback?code=ABC123&state=XYZ789
```

**No JWT token needed here** - authentication is validated via the `state` parameter!

### Step 6: Callback Creates the Account (Automatic)

The callback endpoint (`/auth/twitter/callback`) automatically:

1. **Validates the state** parameter (prevents CSRF attacks)
2. **Looks up the OAuthState** document by state
3. **Exchanges the code for tokens** using PKCE verification
4. **Fetches Twitter user info** (id, username, display name, profile image)
5. **Creates a new Account document**:
   ```json
   {
     "id": "uuid",
     "twitter_id": "1234567890",
     "twitter_username": "elonmusk",
     "display_name": "Elon Musk",
     "profile_image_url": "https://...",
     "access_token": "...",
     "refresh_token": "...",
     "token_expires_at": "2024-12-01T...",
     "is_active": true,
     "sync_status": "active",
     "added_by": "<app_user_id_from_oauth_state>",  // Linked to you! ✨
     "added_at": "2024-11-25T...",
     "total_mentions_tracked": 0
   }
   ```
6. **Cleans up** the OAuthState document
7. **Redirects or returns** success message

### Step 7: Verify the Account Was Added

List your Twitter accounts:

```http
GET /api/v1/accounts/
Authorization: Bearer <your_jwt_token>
```

**Response:**
```json
{
  "accounts": [
    {
      "id": "uuid",
      "twitter_username": "elonmusk",
      "display_name": "Elon Musk",
      "profile_image_url": "https://...",
      "is_active": true,
      "sync_status": "active",
      "total_mentions_tracked": 0,
      "last_synced_at": null
    }
  ],
  "total": 1,
  "active_count": 1,
  "paused_count": 0
}
```

## Security Features

### User Isolation ✅
- Each account is linked to a specific user via `added_by` field
- Users can only see/manage their own accounts
- All `/accounts/*` endpoints require JWT authentication
- All endpoints filter by `Account.added_by == current_user.id`

### OAuth Security ✅
- **PKCE (Proof Key for Code Exchange)**: Prevents authorization code interception
- **State Parameter**: Prevents CSRF attacks
- **Token Expiration**: Access tokens expire and can be refreshed
- **No Password Storage**: Never store Twitter passwords, only OAuth tokens

### JWT Authentication ✅
- Stateless authentication using JWT tokens
- Configurable token expiration (default: 120 minutes)
- Passwords hashed with bcrypt

## Frontend Implementation Example

### React/Next.js Example

```javascript
// 1. User logs in (already done, token stored)
const accessToken = localStorage.getItem('access_token');

// 2. Button to add Twitter account
async function handleAddTwitterAccount() {
  try {
    // Request authorization URL
    const response = await fetch('http://localhost:8000/api/v1/auth/twitter/authorize', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to get authorization URL');
    }
    
    const data = await response.json();
    
    // Redirect to Twitter
    window.location.href = data.authorization_url;
    
  } catch (error) {
    console.error('Error:', error);
    alert('Failed to initiate Twitter authorization');
  }
}

// 3. After Twitter redirects back to your callback URL,
// the backend automatically creates the account.
// Your frontend should detect the redirect and show a success message.

// Example callback page (e.g., /twitter-callback):
function TwitterCallbackPage() {
  useEffect(() => {
    // Check URL params for success/error
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    
    if (code) {
      // Success! Show message and redirect to accounts page
      setTimeout(() => {
        router.push('/accounts');
      }, 2000);
    }
  }, []);
  
  return <div>Connecting your Twitter account...</div>;
}
```

### cURL Example (for testing)

```bash
# 1. Login
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123" | jq -r '.access_token')

# 2. Get authorization URL
AUTH_URL=$(curl -s -X POST "http://localhost:8000/api/v1/auth/twitter/authorize" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.authorization_url')

echo "Visit this URL in your browser:"
echo $AUTH_URL

# 3. After authorizing on Twitter and getting redirected back,
# check your accounts:
curl -X GET "http://localhost:8000/api/v1/accounts/" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## Managing Accounts After Adding

Once an account is added, you can:

### List All Accounts
```http
GET /api/v1/accounts/
Authorization: Bearer <jwt_token>
```

### Get Specific Account Details
```http
GET /api/v1/accounts/{account_id}
Authorization: Bearer <jwt_token>
```

### Pause/Resume Tracking
```http
PATCH /api/v1/accounts/{account_id}
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "is_active": false,  // or true to resume
  "sync_status": "paused"  // optional
}
```

### Get Account Statistics
```http
GET /api/v1/accounts/{account_id}/stats
Authorization: Bearer <jwt_token>
```

### Reauthorize Account (if tokens expire)
```http
POST /api/v1/accounts/{account_id}/reauthorize
Authorization: Bearer <jwt_token>
```

Returns a new authorization URL to refresh tokens.

### Delete Account
```http
DELETE /api/v1/accounts/{account_id}?delete_messages=true
Authorization: Bearer <jwt_token>
```

## Common Issues & Solutions

### Issue: "Could not validate credentials"
**Solution:** Your JWT token expired. Login again to get a new token.

### Issue: "Account not found" when accessing existing account
**Solution:** You're trying to access an account that belongs to another user. Each user can only access their own accounts.

### Issue: Twitter callback fails
**Solution:** 
1. Check that `TWITTER_CALLBACK_URL` in `.env` matches the URL registered in Twitter Developer Portal
2. Ensure the callback URL is publicly accessible (use ngrok for local development)

### Issue: "Invalid OAuth state"
**Solution:** 
1. OAuth states expire - start the flow again
2. Don't refresh the page after clicking "Authorize" on Twitter
3. The state parameter might have been used already

## Database Schema

The `Account` document structure:

```javascript
{
  // Identity
  id: string (UUID),
  twitter_id: string (unique, indexed),
  twitter_username: string (indexed),
  display_name: string,
  profile_image_url: string,
  
  // OAuth Tokens
  access_token: string,
  refresh_token: string,
  token_expires_at: datetime,
  
  // Status & Management
  is_active: boolean,
  sync_status: "active" | "paused" | "error" | "token_expired" | "rate_limited",
  error_message: string,
  
  // Ownership & Tracking
  added_by: string,  // App user ID who added this account ✨
  added_at: datetime,
  last_synced_at: datetime,
  total_mentions_tracked: integer,
  
  // Timestamps
  created_at: datetime,
  updated_at: datetime
}
```

## Testing in Swagger UI

1. Visit: `http://localhost:8000/docs`
2. Register/Login to get a JWT token
3. Click **"Authorize"** button (top right, lock icon)
4. Enter: `Bearer <your_token>`
5. Try **POST /api/v1/auth/twitter/authorize**
6. Copy the `authorization_url` from response
7. Visit that URL in a new browser tab
8. Authorize on Twitter
9. After redirect, check **GET /api/v1/accounts/**

## Summary

**There IS a way to add accounts** - it's just a secure OAuth flow rather than a direct POST:

1. ✅ Login → Get JWT token
2. ✅ POST `/auth/twitter/authorize` (with JWT) → Get auth URL
3. ✅ Redirect user to Twitter
4. ✅ User authorizes
5. ✅ Callback creates account automatically (linked to user via OAuth state)
6. ✅ Account appears in user's account list

The account is automatically linked to the authenticated user through the `OAuthState` record! 🎉

