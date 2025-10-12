from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.config import settings
from app.db.base import get_db
from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageCreate, MessageUpdate, MessageInDB
from app.services.twitter import TwitterService
from datetime import datetime
from sqlalchemy import desc

router = APIRouter()


@router.get("/", response_model=List[MessageInDB])
async def get_messages(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all messages from the database, sorted by timestamp (newest first)
    """
    messages = db.query(Message).order_by(desc(Message.timestamp)).offset(skip).limit(limit).all()
    return messages


@router.get("/{message_id}", response_model=MessageInDB)
async def get_message(
    message_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific message by ID
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    return message


@router.post("/{message_id}/reply")
async def reply_to_message(
    message_id: str,
    response: str,
    db: Session = Depends(get_db)
):
    """
    Reply to a Twitter mention
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    try:
        # Get user's access token
        user = db.query(User).first()  # In a real app, you'd get the specific user
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        # Create Twitter service
        twitter_service = TwitterService(db)
        
        # Verify token and refresh if needed
        if not await twitter_service.verify_token(user.access_token, user.token_expires_at):
            if not await twitter_service.refresh_token(user):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to refresh token"
                )
        
        # Reply to the tweet
        reply = await twitter_service.reply_to_tweet(user.access_token, message_id, response)
        
        # Update message in database
        message.status = "replied"
        message.public_response = response
        db.commit()
        db.refresh(message)
        
        return message
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to reply to tweet: {str(e)}"
        )

@router.patch("/{message_id}", response_model=MessageInDB)
async def update_message(
    message_id: str,
    message_update: MessageUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a message's status, public response, or DM response
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Update message fields if provided
    if message_update.status is not None:
        message.status = message_update.status
    if message_update.public_response is not None:
        message.public_response = message_update.public_response
    if message_update.dm_response is not None:
        message.dm_response = message_update.dm_response
    
    db.commit()
    db.refresh(message)
    return message

@router.post("/{message_id}/dm-reply")
async def reply_to_dm(
    message_id: str,
    response: str,
    db: Session = Depends(get_db)
):
    """
    Send a DM response to a user
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    try:
        # Get user's access token
        user = db.query(User).first()  # In a real app, you'd get the specific user
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        # Create Twitter service
        twitter_service = TwitterService(db)
        
        # Verify token and refresh if needed
        if not await twitter_service.verify_token(user.access_token, user.token_expires_at):
            if not await twitter_service.refresh_token(user):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to refresh token"
                )
        
        print('sending DM...')
        
        # Send DM to the user who sent the original message
        dm_response = await twitter_service.send_dm(
            user.access_token,
            message.user,  # This is the author_id from the original tweet
            response
        )

        print('dm_response', dm_response)
        
        # Update message in database
        message.dm_response = response
        db.commit()
        db.refresh(message)
        
        return message
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send DM: {str(e)}"
        )

@router.delete("/{message_id}")
async def delete_message(
    message_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a message
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    db.delete(message)
    db.commit()
    
    return {"message": "Message successfully deleted"} 