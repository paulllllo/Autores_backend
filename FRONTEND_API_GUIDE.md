# Frontend API Guide

Quick reference for integrating with the Autores Backend API.

---

## Table of Contents
1. [User Authentication Flow](#user-authentication-flow)
2. [Adding Twitter Accounts](#adding-twitter-accounts)
3. [Account Management Endpoints](#account-management-endpoints)
4. [Message/Mentions Endpoints](#messagementions-endpoints)

---

## User Authentication Flow

### Overview
Users must register and login to manage their Twitter accounts. Authentication uses **JWT tokens** (Bearer tokens).

### 1. Register a New User

```javascript
POST /api/v1/users/register

// Request Body
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepass123",
  "full_name": "John Doe"  // optional
}

// Response (201 Created)
{
  "id": "uuid",
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-11-25T10:00:00",
  "last_login": null
}
```

### 2. Login to Get Access Token

```javascript
POST /api/v1/users/login
Content-Type: application/x-www-form-urlencoded

// Request Body (URL-encoded form data)
username=johndoe&password=securepass123

// Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Important:** Store the `access_token` securely (localStorage, sessionStorage, or httpOnly cookies).

### 3. Use Token for Protected Requests

```javascript
// All subsequent requests to protected endpoints
GET /api/v1/users/me
Authorization: Bearer <access_token>

// Response (200 OK)
{
  "id": "uuid",
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-11-25T10:00:00",
  "last_login": "2024-11-25T10:05:00"
}
```

### Other User Endpoints

```javascript
// Update Profile
PATCH /api/v1/users/me
Authorization: Bearer <token>
Body: { "email": "newemail@example.com", "full_name": "New Name" }

// Change Password
POST /api/v1/users/me/change-password
Authorization: Bearer <token>
Body: { "current_password": "old", "new_password": "new123" }

// Delete Account
DELETE /api/v1/users/me
Authorization: Bearer <token>
```

---

## Adding Twitter Accounts

### The Complete Flow

**Step 1:** User is already logged in (has JWT token)

**Step 2:** Request Twitter authorization URL from backend

```javascript
POST /api/v1/auth/twitter/authorize
Authorization: Bearer <access_token>

// Response (200 OK)
{
  "authorization_url": "https://twitter.com/i/oauth2/authorize?...",
  "message": "Redirect user to this URL to authorize their Twitter account"
}
```

**Step 3:** Redirect user to the `authorization_url`

```javascript
// Frontend code example
async function addTwitterAccount() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:8000/api/v1/auth/twitter/authorize', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  
  // Redirect user to Twitter
  window.location.href = data.authorization_url;
}
```

**Step 4:** User authorizes on Twitter's page

**Step 5:** Twitter redirects back to your callback URL

```
Example: http://your-app.com/api/v1/auth/twitter/callback?code=ABC123&state=XYZ789
```

The backend automatically:
- Validates the authorization
- Exchanges code for tokens
- Creates the Twitter account
- Links it to the logged-in user

**Step 6:** Account is now added! Redirect user to accounts page

```javascript
// In your callback page component
useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  
  if (code) {
    // Success! Show message and redirect
    showSuccessMessage('Twitter account connected!');
    setTimeout(() => {
      router.push('/accounts');
    }, 1500);
  }
}, []);
```

### Why This Flow?

- **Security**: Twitter accounts require OAuth tokens that can only be obtained through Twitter's official flow
- **No passwords**: Your app never handles Twitter credentials
- **Automatic linking**: The account is automatically linked to the authenticated user

---

## Account Management Endpoints

All endpoints require `Authorization: Bearer <token>` header. Users can only access their own accounts.

### List All Twitter Accounts

```javascript
GET /api/v1/accounts/
GET /api/v1/accounts/?include_inactive=true  // Include paused accounts

// Response
{
  "accounts": [
    {
      "id": "uuid",
      "twitter_username": "elonmusk",
      "display_name": "Elon Musk",
      "profile_image_url": "https://...",
      "is_active": true,
      "sync_status": "active",  // active | paused | error | token_expired | rate_limited
      "total_mentions_tracked": 42,
      "last_synced_at": "2024-11-25T10:00:00"
    }
  ],
  "total": 1,
  "active_count": 1,
  "paused_count": 0
}
```

### Get Single Account Details

```javascript
GET /api/v1/accounts/{account_id}

// Response
{
  "id": "uuid",
  "twitter_id": "1234567890",
  "twitter_username": "elonmusk",
  "display_name": "Elon Musk",
  "profile_image_url": "https://...",
  "is_active": true,
  "sync_status": "active",
  "error_message": null,
  "token_expires_at": "2024-12-25T10:00:00",
  "total_mentions_tracked": 42,
  "added_at": "2024-11-01T10:00:00",
  "last_synced_at": "2024-11-25T10:00:00",
  "created_at": "2024-11-01T10:00:00",
  "updated_at": "2024-11-25T10:00:00"
}
```

### Pause/Resume Account Tracking

```javascript
PATCH /api/v1/accounts/{account_id}

// Pause tracking
Body: { "is_active": false }

// Resume tracking
Body: { "is_active": true }

// Response: Same as GET /accounts/{account_id}
```

### Get Account Statistics

```javascript
GET /api/v1/accounts/{account_id}/stats

// Response
{
  "account_id": "uuid",
  "username": "elonmusk",
  "total_mentions": 150,
  "pending_mentions": 5,
  "replied_mentions": 145,
  "days_tracked": 30,
  "avg_mentions_per_day": 5.0,
  "last_synced": "2024-11-25T10:00:00",
  "sync_status": "active",
  "is_active": true
}
```

### Reauthorize Account (Refresh Tokens)

```javascript
POST /api/v1/accounts/{account_id}/reauthorize

// Response
{
  "authorization_url": "https://twitter.com/i/oauth2/authorize?...",
  "account_username": "elonmusk",
  "message": "Please reauthorize @elonmusk by visiting the authorization URL"
}

// Use this when sync_status is "token_expired"
// Redirect user to authorization_url (same flow as adding account)
```

### Delete Account

```javascript
DELETE /api/v1/accounts/{account_id}
DELETE /api/v1/accounts/{account_id}?delete_messages=true  // Also delete messages

// Response
{
  "message": "Account @elonmusk deleted successfully",
  "messages_deleted": 0,
  "messages_retained": 150
}
```

---

## Message/Mentions Endpoints

### Fetch New Mentions

```javascript
POST /api/v1/mentions/fetch-new
POST /api/v1/mentions/fetch-new?account_id=<uuid>  // Fetch for specific account

// Response
{
  "message": "Fetched 5 new messages",
  "new_messages_count": 5,
  "messages": [
    {
      "id": "uuid",
      "tweet_id": "1234567890",
      "timestamp": "2024-11-25T10:00:00",
      "text": "@elonmusk Great work!",
      "sender": {
        "twitter_id": "9876543210",
        "username": "johndoe",
        "display_name": "John Doe",
        "profile_image_url": "https://..."
      },
      "sent_to": {
        "account_id": "uuid",
        "twitter_id": "1234567890",
        "username": "elonmusk",
        "display_name": "Elon Musk"
      },
      "status": "pending",  // pending | processing | replied | ignored | error
      "public_response": null,
      "dm_response": null,
      "credits_used": 0,
      "redirected": false,
      "created_at": "2024-11-25T10:00:00",
      "updated_at": "2024-11-25T10:00:00"
    }
  ]
}
```

### List All Mentions

```javascript
GET /api/v1/mentions/
GET /api/v1/mentions/?status=pending
GET /api/v1/mentions/?account_id=<uuid>
GET /api/v1/mentions/?account_id=<uuid>&status=pending

// Response: Array of messages (same structure as fetch-new)
```

### Get Single Mention

```javascript
GET /api/v1/mentions/{message_id}

// Response: Single message object
```

### Generate AI Response

```javascript
POST /api/v1/mentions/{message_id}/generate-response

// Optional custom prompt
Body: { "custom_prompt": "Be friendly and professional" }

// Response
{
  "message_id": "uuid",
  "original_message": "@elonmusk Great work!",
  "generated_response": "Thank you so much! Really appreciate your support!",
  "custom_prompt_used": true
}
```

### Reply to Mention (Public Tweet)

```javascript
POST /api/v1/mentions/{message_id}/reply

Body: { "response": "Thank you for your message!" }

// Response
{
  "message": "Reply posted successfully",
  "tweet_id": "9999999999",
  "message_id": "uuid"
}
```

### Send DM Reply

```javascript
POST /api/v1/mentions/{message_id}/dm-reply

Body: { "response": "Thanks! I'll get back to you soon." }

// Response
{
  "message": "DM sent successfully",
  "dm_id": "8888888888",
  "message_id": "uuid"
}
```

---

## React/Next.js Example

### Complete Authentication Flow

```javascript
// 1. Register Page
async function handleRegister(formData) {
  const response = await fetch('/api/v1/users/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData)
  });
  
  if (response.ok) {
    router.push('/login');
  }
}

// 2. Login Page
async function handleLogin(username, password) {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);
  
  const response = await fetch('/api/v1/users/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData
  });
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  router.push('/dashboard');
}

// 3. Protected API calls
async function fetchUserAccounts() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('/api/v1/accounts/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return response.json();
}

// 4. Add Twitter Account
async function addTwitterAccount() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('/api/v1/auth/twitter/authorize', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  window.location.href = data.authorization_url;
}
```

### Auth Context Provider (React)

```javascript
import { createContext, useState, useEffect } from 'react';

export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  async function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/v1/users/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        localStorage.removeItem('access_token');
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setLoading(false);
    }
  }

  async function login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await fetch('/api/v1/users/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });
    
    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    await checkAuth();
  }

  function logout() {
    localStorage.removeItem('access_token');
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
```

---

## Important Notes

### Token Expiration
- JWT tokens expire after **120 minutes** (configurable)
- When you get a 401 response, redirect user to login page
- Consider implementing token refresh mechanism

### Error Handling
All error responses follow this format:
```json
{
  "detail": "Error message here"
}
```

Common status codes:
- `200` - Success
- `201` - Created (e.g., user registered)
- `400` - Bad request (validation error)
- `401` - Unauthorized (invalid/expired token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not found
- `500` - Server error

### Base URL
```javascript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

### CORS
The backend allows CORS from all origins by default (development). Configure appropriately for production.

---

## Quick Reference

### Authentication Flow
1. `POST /users/register` → Register
2. `POST /users/login` → Get token
3. Use token in `Authorization: Bearer <token>` header

### Add Twitter Account Flow
1. `POST /auth/twitter/authorize` (with token) → Get URL
2. Redirect to URL → User authorizes on Twitter
3. Twitter redirects back → Account created automatically
4. `GET /accounts/` → See new account

### Manage Accounts
- `GET /accounts/` → List all
- `GET /accounts/{id}` → Get details
- `PATCH /accounts/{id}` → Pause/resume
- `DELETE /accounts/{id}` → Remove

### Handle Mentions
- `POST /mentions/fetch-new` → Poll Twitter
- `GET /mentions/` → List all
- `POST /mentions/{id}/generate-response` → AI response
- `POST /mentions/{id}/reply` → Reply publicly
- `POST /mentions/{id}/dm-reply` → Reply via DM

