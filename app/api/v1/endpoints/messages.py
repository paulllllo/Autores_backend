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

router = APIRouter()


@router.get("/", response_model=List[MessageInDB])
async def get_messages(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all messages from the database
    """
    messages = db.query(Message).offset(skip).limit(limit).all()
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
        
        return {
            "message": "Successfully replied to tweet",
            "tweet_id": reply["data"]["id"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to reply to tweet: {str(e)}"
        ) 