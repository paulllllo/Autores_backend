from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.core.config import settings
from app.core.deps import get_current_user
from app.models.account import Account
from app.models.app_user import AppUser
from app.models.message import Message
from app.models.enums import AccountSyncStatus
from app.schemas.account import (
    AccountSummary, 
    AccountList, 
    AccountStatusUpdate, 
    AccountInDB,
    ReauthorizeResponse
)
from datetime import datetime

router = APIRouter()


@router.get("/", response_model=AccountList)
async def list_accounts(
    include_inactive: bool = Query(False, description="Include inactive accounts"),
    current_user: AppUser = Depends(get_current_user)
):
    """
    List all tracked Twitter accounts for the current user
    """
    try:
        # Build query - filter by current user
        if include_inactive:
            accounts = await Account.find(Account.added_by == current_user.id).to_list()
        else:
            accounts = await Account.find(
                Account.added_by == current_user.id,
                Account.is_active == True
            ).to_list()
        
        # Count active and paused
        active_count = sum(1 for acc in accounts if acc.is_active and acc.sync_status == AccountSyncStatus.ACTIVE)
        paused_count = sum(1 for acc in accounts if not acc.is_active or acc.sync_status == AccountSyncStatus.PAUSED)
        
        # Convert to summaries
        summaries = [
            AccountSummary(
                id=acc.id,
                twitter_username=acc.twitter_username,
                display_name=acc.display_name,
                profile_image_url=acc.profile_image_url,
                is_active=acc.is_active,
                sync_status=acc.sync_status,
                total_mentions_tracked=acc.total_mentions_tracked,
                last_synced_at=acc.last_synced_at
            )
            for acc in accounts
        ]
        
        return AccountList(
            accounts=summaries,
            total=len(summaries),
            active_count=active_count,
            paused_count=paused_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list accounts: {str(e)}"
        )


@router.get("/{account_id}", response_model=AccountInDB)
async def get_account(
    account_id: str,
    current_user: AppUser = Depends(get_current_user)
):
    """
    Get detailed information about a specific account owned by the current user
    """
    account = await Account.find_one(
        Account.id == account_id,
        Account.added_by == current_user.id
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    return AccountInDB(
        id=account.id,
        twitter_id=account.twitter_id,
        twitter_username=account.twitter_username,
        display_name=account.display_name,
        profile_image_url=account.profile_image_url,
        is_active=account.is_active,
        sync_status=account.sync_status,
        error_message=account.error_message,
        token_expires_at=account.token_expires_at,
        total_mentions_tracked=account.total_mentions_tracked,
        added_at=account.added_at,
        last_synced_at=account.last_synced_at,
        created_at=account.created_at,
        updated_at=account.updated_at
    )


@router.patch("/{account_id}", response_model=AccountInDB)
async def update_account_status(
    account_id: str,
    update: AccountStatusUpdate,
    current_user: AppUser = Depends(get_current_user)
):
    """
    Update account status (pause/resume tracking, update sync status)
    """
    account = await Account.find_one(
        Account.id == account_id,
        Account.added_by == current_user.id
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Update fields if provided
    if update.is_active is not None:
        account.is_active = update.is_active
        # If activating, reset sync status
        if update.is_active and account.sync_status in [AccountSyncStatus.PAUSED, AccountSyncStatus.ERROR]:
            account.sync_status = AccountSyncStatus.ACTIVE
        # If deactivating, set to paused
        elif not update.is_active:
            account.sync_status = AccountSyncStatus.PAUSED
    
    if update.sync_status is not None:
        account.sync_status = update.sync_status
    
    account.updated_at = datetime.utcnow()
    await account.save()
    
    return AccountInDB(
        id=account.id,
        twitter_id=account.twitter_id,
        twitter_username=account.twitter_username,
        display_name=account.display_name,
        profile_image_url=account.profile_image_url,
        is_active=account.is_active,
        sync_status=account.sync_status,
        error_message=account.error_message,
        token_expires_at=account.token_expires_at,
        total_mentions_tracked=account.total_mentions_tracked,
        added_at=account.added_at,
        last_synced_at=account.last_synced_at,
        created_at=account.created_at,
        updated_at=account.updated_at
    )


@router.delete("/{account_id}")
async def delete_account(
    account_id: str,
    delete_messages: bool = Query(False, description="Also delete associated messages"),
    current_user: AppUser = Depends(get_current_user)
):
    """
    Remove a tracked account owned by the current user
    Optionally delete all associated messages
    """
    account = await Account.find_one(
        Account.id == account_id,
        Account.added_by == current_user.id
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    try:
        # Count messages before deletion
        message_count = await Message.find({"sent_to.account_id": account_id}).count()
        
        # Delete messages if requested
        if delete_messages:
            await Message.find({"sent_to.account_id": account_id}).delete()
        
        # Delete account
        await account.delete()
        
        return {
            "message": f"Account @{account.twitter_username} deleted successfully",
            "messages_deleted": message_count if delete_messages else 0,
            "messages_retained": message_count if not delete_messages else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )


@router.get("/{account_id}/stats")
async def get_account_stats(
    account_id: str,
    current_user: AppUser = Depends(get_current_user)
):
    """
    Get statistics for an account owned by the current user
    """
    account = await Account.find_one(
        Account.id == account_id,
        Account.added_by == current_user.id
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    try:
        # Get message counts by status
        total_messages = await Message.find({"sent_to.account_id": account_id}).count()
        pending_messages = await Message.find({
            "sent_to.account_id": account_id,
            "status": "pending"
        }).count()
        replied_messages = await Message.find({
            "sent_to.account_id": account_id,
            "status": "replied"
        }).count()
        
        # Days since added
        days_tracked = (datetime.utcnow() - account.added_at).days
        
        # Calculate average mentions per day
        avg_mentions_per_day = total_messages / days_tracked if days_tracked > 0 else total_messages
        
        return {
            "account_id": account_id,
            "username": account.twitter_username,
            "total_mentions": total_messages,
            "pending_mentions": pending_messages,
            "replied_mentions": replied_messages,
            "days_tracked": days_tracked,
            "avg_mentions_per_day": round(avg_mentions_per_day, 2),
            "last_synced": account.last_synced_at,
            "sync_status": account.sync_status,
            "is_active": account.is_active
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get account stats: {str(e)}"
        )


@router.post("/{account_id}/reauthorize", response_model=ReauthorizeResponse)
async def request_account_reauthorization(
    account_id: str,
    current_user: AppUser = Depends(get_current_user)
):
    """
    Request reauthorization for an account owned by the current user (generates new OAuth URL)
    This is used when tokens expire or need to be refreshed
    """
    account = await Account.find_one(
        Account.id == account_id,
        Account.added_by == current_user.id
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Import auth functions
    from app.api.v1.endpoints.auth import twitter_authorize
    
    try:
        # Generate new authorization URL (reuse the twitter_authorize logic)
        auth_url_data = await twitter_authorize(current_user)
        
        return ReauthorizeResponse(
            authorization_url=auth_url_data["authorization_url"],
            account_username=account.twitter_username,
            message=f"Please reauthorize @{account.twitter_username} by visiting the authorization URL"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate reauthorization URL: {str(e)}"
        )



