# User Authentication System Guide

## Overview

A complete username/password authentication system has been added to the application. This allows multiple users to manage their own Twitter accounts for mention tracking.

## What's New

### 1. **Application User Model** (`app/models/app_user.py`)
- Users can register with username, email, and password
- Passwords are securely hashed using bcrypt
- Each user has their own Twitter accounts collection

### 2. **Authentication Endpoints** (`/api/v1/users/`)

#### Register a New User
```http
POST /api/v1/users/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"  // optional
}
```

#### Login (Get Access Token)
```http
POST /api/v1/users/login
Content-Type: application/x-www-form-urlencoded

username=johndoe&password=securepassword123
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Get Current User Info
```http
GET /api/v1/users/me
Authorization: Bearer <your_access_token>
```

#### Update Profile
```http
PATCH /api/v1/users/me
Authorization: Bearer <your_access_token>
Content-Type: application/json

{
  "email": "newemail@example.com",
  "full_name": "John Updated Doe",
  "password": "newpassword123"  // optional
}
```

#### Change Password
```http
POST /api/v1/users/me/change-password
Authorization: Bearer <your_access_token>
Content-Type: application/json

{
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

#### Delete Account
```http
DELETE /api/v1/users/me
Authorization: Bearer <your_access_token>
```

### 3. **Protected Endpoints**

All account and message management endpoints now require authentication:

- **Twitter OAuth**: `/api/v1/auth/twitter/authorize` (requires login)
- **Account Management**: `/api/v1/accounts/*` (all endpoints)
- **Messages**: `/api/v1/mentions/*` (all endpoints)

### 4. **Twitter Account Linking**

Twitter accounts are now linked to the logged-in user:

1. User logs in with username/password
2. User visits `/api/v1/auth/twitter/authorize` (with Bearer token)
3. Completes Twitter OAuth
4. Twitter account is linked to their user profile

Each user can only see and manage their own Twitter accounts.

## Usage Flow

### From Frontend

1. **User Registration/Login**:
```javascript
// Register
const registerResponse = await fetch('http://localhost:8000/api/v1/users/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'johndoe',
    email: 'john@example.com',
    password: 'securepass123'
  })
});

// Login
const formData = new URLSearchParams();
formData.append('username', 'johndoe');
formData.append('password', 'securepass123');

const loginResponse = await fetch('http://localhost:8000/api/v1/users/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: formData
});

const { access_token } = await loginResponse.json();
// Store this token for subsequent requests
localStorage.setItem('access_token', access_token);
```

2. **Add Twitter Account**:
```javascript
const token = localStorage.getItem('access_token');

// This will redirect to Twitter OAuth
window.location.href = `http://localhost:8000/api/v1/auth/twitter/authorize?token=${token}`;
```

3. **List User's Twitter Accounts**:
```javascript
const token = localStorage.getItem('access_token');

const accountsResponse = await fetch('http://localhost:8000/api/v1/accounts/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const accounts = await accountsResponse.json();
```

## Security Features

- **Password Hashing**: Using bcrypt (industry standard)
- **JWT Tokens**: Secure, stateless authentication
- **Token Expiration**: Configurable (default: 120 minutes)
- **User Isolation**: Each user can only access their own data
- **OAuth State Security**: Twitter accounts linked to authenticated users

## Configuration

All settings in `.env`:

```env
# Security (REQUIRED)
SECRET_KEY=your-secret-key-here  # Already exists

# JWT Configuration (optional, has defaults)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
```

## Database Collections

- `app_users`: Application users (username/password auth)
- `accounts`: Twitter accounts (linked to app users via `added_by` field)
- `messages`: Mentions (includes sender and recipient info)
- `oauth_states`: Temporary OAuth state (includes `app_user_id`)

## Migration Notes

### Existing Data

If you have existing Twitter accounts in the database without `added_by`, you'll need to either:

1. **Delete old accounts** and have users re-add them after registering
2. **Run a migration script** to assign existing accounts to a user

Example migration (if needed):
```python
# Assign all existing accounts to a specific user
async def assign_orphaned_accounts(user_id: str):
    accounts = await Account.find(Account.added_by == None).to_list()
    for account in accounts:
        account.added_by = user_id
        await account.save()
```

## Testing

### Interactive API Docs

Visit: `http://localhost:8000/docs`

1. Register a new user via `/api/v1/users/register`
2. Login via `/api/v1/users/login` to get a token
3. Click "Authorize" button (top right)
4. Enter: `Bearer <your_token>`
5. Now you can test all protected endpoints

### cURL Examples

```bash
# Register
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123"}'

# Login
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"

# Get current user (replace TOKEN with actual token)
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer TOKEN"

# List my Twitter accounts
curl -X GET "http://localhost:8000/api/v1/accounts/" \
  -H "Authorization: Bearer TOKEN"
```

## Next Steps

1. **Frontend Integration**: Update your frontend to handle user registration/login
2. **Token Storage**: Store JWT tokens securely (localStorage or httpOnly cookies)
3. **Token Refresh**: Consider implementing refresh tokens for longer sessions
4. **Email Verification**: Optional: Add email verification for new users
5. **Password Reset**: Optional: Add password reset via email

## Support

All files created:
- `app/models/app_user.py` - User model
- `app/core/security.py` - Password & JWT utilities
- `app/core/deps.py` - Authentication dependencies
- `app/schemas/app_user.py` - User schemas
- `app/api/v1/endpoints/users.py` - User endpoints

All files updated:
- `app/db/mongodb.py` - Added AppUser to Beanie
- `app/models/oauth_state.py` - Added app_user_id field
- `app/models/account.py` - Updated added_by documentation
- `app/api/v1/api.py` - Added users router
- `app/api/v1/endpoints/auth.py` - Link Twitter accounts to users
- `app/api/v1/endpoints/accounts.py` - Protected with auth

