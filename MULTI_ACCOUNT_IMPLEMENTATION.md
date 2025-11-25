# Multi-Account Twitter Tracking Implementation

## ✅ Implementation Complete

This document summarizes the changes made to enable tracking mentions from multiple Twitter accounts.

---

## 🎯 What Changed

### 1. **User Model → Account Model**

The `User` model has been replaced with `Account` to avoid confusion with future authentication users.

**New Account Model Features:**
- **Twitter Information**: `twitter_username`, `display_name`, `profile_image_url`
- **Account Management**: `is_active` flag to pause/resume tracking
- **Sync Status**: Enum-based status (`active`, `paused`, `error`, `token_expired`, `rate_limited`)
- **Error Tracking**: `error_message` field for troubleshooting
- **Metadata**: `added_at`, `last_synced_at`, `total_mentions_tracked`

**Location**: `app/models/account.py`

---

### 2. **Enhanced Message Model**

Messages now include detailed information about both sender and recipient.

**New Structure:**
```python
{
    "tweet_id": "123...",  # Twitter's tweet ID
    "sender": {  # Who mentioned the account
        "twitter_id": "...",
        "username": "@user",
        "display_name": "User Name",
        "profile_image_url": "..."
    },
    "sent_to": {  # Which tracked account received it
        "account_id": "uuid",
        "twitter_id": "...",
        "username": "@tracked_account",
        "display_name": "Account Name"
    },
    "status": "pending",  # Now an enum
    ...
}
```

**Location**: `app/models/message.py`

---

### 3. **Enum-Based Status Fields**

Status fields now use enums for better type safety and OpenAPI documentation.

**Account Sync Status:**
- `active` - Normal operation
- `paused` - Temporarily disabled
- `error` - Failed to sync
- `token_expired` - Needs reauthorization
- `rate_limited` - Hit Twitter rate limits

**Message Status:**
- `pending` - Awaiting response
- `processing` - Being processed
- `replied` - Response sent
- `ignored` - Intentionally skipped
- `error` - Processing failed

**Location**: `app/models/enums.py`

---

### 4. **New Account Management API**

Complete CRUD operations for managing tracked accounts.

#### **Endpoints:**

##### `GET /api/v1/accounts/`
List all tracked accounts with filtering
- Query params: `include_inactive` (default: false)
- Returns: Account summaries with stats

##### `GET /api/v1/accounts/{account_id}`
Get detailed account information

##### `PATCH /api/v1/accounts/{account_id}`
Update account status (pause/resume)
```json
{
    "is_active": false,  // Pause tracking
    "sync_status": "paused"
}
```

##### `DELETE /api/v1/accounts/{account_id}`
Remove an account
- Query param: `delete_messages` - Also delete associated messages

##### `GET /api/v1/accounts/{account_id}/stats`
Get account statistics
- Total mentions
- Pending/replied counts
- Average mentions per day
- Last sync time

##### `POST /api/v1/accounts/{account_id}/reauthorize`
Generate OAuth URL for reauthorization

**Location**: `app/api/v1/endpoints/accounts.py`

---

### 5. **Enhanced Message Endpoints**

Message endpoints now support filtering by account.

#### **Updated Endpoints:**

##### `GET /api/v1/mentions/`
Now supports filtering:
- `?account_id=uuid` - Filter by specific account
- `?status=pending` - Filter by status (with enum validation)

##### `POST /api/v1/mentions/fetch-new`
Fetch new mentions:
- `?account_id=uuid` - Fetch for specific account only
- No param = Fetch for all active accounts

##### All reply endpoints
Automatically use the correct account's credentials based on which account received the mention.

**Location**: `app/api/v1/endpoints/messages.py`

---

### 6. **Updated Services**

#### **TwitterService** (`app/services/twitter.py`)
- Now fetches expanded user data for mentions
- Creates structured sender/recipient objects
- Updates account mention counts automatically

#### **SchedulerService** (`app/services/scheduler.py`)
- Polls only **active** accounts
- Updates sync status for each account
- Handles errors per-account without stopping other accounts
- Automatic token refresh with status tracking

---

### 7. **Enhanced Auth Flow**

The OAuth callback now:
1. Extracts full Twitter profile info (username, display name, image)
2. Creates new accounts with all metadata
3. Updates existing accounts on reauthorization
4. Returns account details instead of generic user info

**Location**: `app/api/v1/endpoints/auth.py`

---

## 📊 Data Migration

All existing data has been migrated:
- ✅ **1 user** → **1 account** (with new fields)
- ✅ **22 messages** updated with sender/recipient structure
- ✅ Mention counts calculated and stored

**Migration Script**: `scripts/migrate_users_to_accounts.py`

---

## 🚀 How to Add New Accounts

### Option 1: Via OAuth Flow (Recommended)

1. **Frontend**: Call `GET /api/v1/auth/login`
   - Returns `authorization_url`
   
2. **User**: Visits authorization URL and approves

3. **Twitter**: Redirects to callback with code

4. **Backend**: `GET /api/v1/auth/callback?code=...&state=...`
   - Creates new account automatically
   - Returns account details

### Option 2: Reauthorize Existing Account

1. `POST /api/v1/accounts/{account_id}/reauthorize`
   - Returns new authorization URL
   - User follows OAuth flow
   - Tokens refreshed automatically

---

## 🎮 Usage Examples

### List All Active Accounts
```bash
GET /api/v1/accounts/
```

Response:
```json
{
    "accounts": [
        {
            "id": "uuid",
            "twitter_username": "elonmusk",
            "display_name": "Elon Musk",
            "is_active": true,
            "sync_status": "active",
            "total_mentions_tracked": 42,
            "last_synced_at": "2025-11-17T..."
        }
    ],
    "total": 1,
    "active_count": 1,
    "paused_count": 0
}
```

### Pause Account Tracking
```bash
PATCH /api/v1/accounts/{account_id}
{
    "is_active": false
}
```

### Get Mentions for Specific Account
```bash
GET /api/v1/mentions/?account_id={account_id}&status=pending
```

### Get Account Statistics
```bash
GET /api/v1/accounts/{account_id}/stats
```

Response:
```json
{
    "account_id": "uuid",
    "username": "elonmusk",
    "total_mentions": 42,
    "pending_mentions": 5,
    "replied_mentions": 37,
    "days_tracked": 7,
    "avg_mentions_per_day": 6.0,
    "last_synced": "2025-11-17T...",
    "sync_status": "active",
    "is_active": true
}
```

---

## 🔧 Technical Details

### Database Collections

#### `accounts` (formerly `users`)
```javascript
{
    _id: ObjectId,
    id: "uuid",
    twitter_id: "123...",
    twitter_username: "handle",
    display_name: "Full Name",
    profile_image_url: "https://...",
    access_token: "...",
    refresh_token: "...",
    token_expires_at: ISODate,
    is_active: true,
    sync_status: "active",
    error_message: null,
    added_at: ISODate,
    last_synced_at: ISODate,
    total_mentions_tracked: 42,
    created_at: ISODate,
    updated_at: ISODate
}
```

#### `messages`
```javascript
{
    _id: ObjectId,
    id: "uuid",
    tweet_id: "twitter_tweet_id",
    timestamp: ISODate,
    text: "mention text",
    sender: {
        twitter_id: "...",
        username: "@sender",
        display_name: "Sender Name",
        profile_image_url: "..."
    },
    sent_to: {
        account_id: "uuid",
        twitter_id: "...",
        username: "@tracked",
        display_name: "Tracked Account"
    },
    status: "pending",
    public_response: null,
    dm_response: null,
    created_at: ISODate,
    updated_at: ISODate
}
```

### Indexes
- `accounts.twitter_id` (unique)
- `accounts.twitter_username`
- `accounts.is_active`
- `accounts.sync_status`
- `messages.tweet_id`
- `messages.sender.twitter_id`
- `messages.sent_to.account_id`
- `messages.status`

---

## 🎨 Frontend Integration

### Account Management UI Recommendations

1. **Account List Page**
   - Show all tracked accounts with cards/table
   - Display sync status with color coding
   - Show mention counts and last sync time
   - Add/pause/remove actions

2. **Add Account Button**
   - Triggers OAuth flow
   - Shows "Connecting to Twitter..." modal
   - Redirects to Twitter authorization
   - Shows success/error after callback

3. **Mention Feed**
   - Filter dropdown for accounts
   - Show sender and recipient info on each mention
   - Account avatar/badge on mentions

4. **Account Detail Page**
   - Full stats dashboard
   - Recent mentions
   - Pause/resume toggle
   - Reauthorize button (if token expired)

---

## ✨ Key Benefits

1. **Multi-Account Support**: Track unlimited Twitter accounts
2. **Type Safety**: Enum-based statuses prevent typos
3. **Better UX**: Pause accounts without deletion
4. **Detailed Info**: Full sender/recipient data on mentions
5. **Error Handling**: Per-account error tracking
6. **Scalability**: Scheduler handles multiple accounts efficiently
7. **OpenAPI Docs**: Enums show in Swagger UI for frontend devs

---

## 🔮 Future Enhancements

Possible additions:
- Account groups/tags
- Per-account response templates
- Account-level analytics dashboard
- Account permissions (who can manage which accounts)
- Bulk operations (pause all, fetch all)
- Account health monitoring

---

## 📝 Notes

- **OAuth Credentials**: Still use the single set from `.env`
- **Users don't need their own Twitter App**: Your app's credentials handle all OAuth flows
- **Backward Compatibility**: Old `user` field kept in messages for transition
- **Migration**: Run once, automatic and safe

---

## Testing Checklist

- [x] Add new account via OAuth
- [ ] Pause/resume account tracking
- [ ] Filter mentions by account
- [ ] Reply using correct account credentials
- [ ] Remove account (with/without messages)
- [ ] View account statistics
- [ ] Automatic polling for multiple accounts
- [ ] Error handling (rate limits, token expiry)
- [ ] Reauthorize expired account

---

**Implementation Date**: November 17, 2025  
**Migration Status**: ✅ Complete (1 account, 22 messages)  
**Backward Compatibility**: ✅ Maintained

