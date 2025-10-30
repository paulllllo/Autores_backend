from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.core.config import settings
from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageCreate, MessageUpdate, MessageInDB, FetchMessagesResponse, GenerateResponseRequest, GenerateResponseResponse
from app.services.twitter import TwitterService
from app.services.ai_service import AIService
from datetime import datetime

router = APIRouter()


@router.get("/", response_model=List[MessageInDB])
async def get_messages(
    skip: int = 0,
    limit: int = 100
):
    """
    Get all messages from the database, sorted by timestamp (newest first)
    """
    messages = await Message.find().sort(-Message.timestamp).skip(skip).limit(limit).to_list()
    return messages


@router.get("/{message_id}", response_model=MessageInDB)
async def get_message(
    message_id: str
):
    """
    Get a specific message by ID
    """
    message = await Message.find_one(Message.id == message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    return message


@router.post("/{message_id}/reply")
async def reply_to_message(
    message_id: str,
    response: str
):
    """
    Reply to a Twitter mention
    """
    message = await Message.find_one(Message.id == message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    try:
        # Get user's access token
        user = await User.find_one()  # In a real app, you'd get the specific user
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        # Create Twitter service
        twitter_service = TwitterService()
        
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
        await message.save()
        
        return message
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to reply to tweet: {str(e)}"
        )

@router.patch("/{message_id}", response_model=MessageInDB)
async def update_message(
    message_id: str,
    message_update: MessageUpdate
):
    """
    Update a message's status, public response, or DM response
    """
    message = await Message.find_one(Message.id == message_id)
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
    
    await message.save()
    return message

@router.post("/{message_id}/dm-reply")
async def reply_to_dm(
    message_id: str,
    response: str
):
    """
    Send a DM response to a user
    """
    message = await Message.find_one(Message.id == message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    try:
        # Get user's access token
        user = await User.find_one()  # In a real app, you'd get the specific user
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        # Create Twitter service
        twitter_service = TwitterService()
        
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
        await message.save()
        
        return message
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send DM: {str(e)}"
        )

@router.delete("/{message_id}")
async def delete_message(
    message_id: str
):
    """
    Delete a message
    """
    message = await Message.find_one(Message.id == message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    await message.delete()
    
    return {"message": "Message successfully deleted"}


@router.post("/fetch-new", response_model=FetchMessagesResponse)
async def fetch_new_messages():
    """
    Fetch new mentions from Twitter for the current user
    """
    try:
        # Get the current user
        user = await User.find_one()  # In a real app, you'd get the specific authenticated user
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        # Create Twitter service
        twitter_service = TwitterService()
        
        # Fetch new mentions
        new_messages = await twitter_service.fetch_mentions(user)
        
        return FetchMessagesResponse(
            message=f"Successfully fetched {len(new_messages)} new messages",
            new_messages_count=len(new_messages),
            messages=new_messages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch new messages: {str(e)}"
        )


@router.post("/{message_id}/generate-response", response_model=GenerateResponseResponse)
async def generate_ai_response(
    message_id: str,
    request: GenerateResponseRequest
):
    """
    Generate an AI response for a given message
    """
    message = await Message.find_one(Message.id == message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    try:
        # Create AI service
        ai_service = AIService()
        
        # Generate response
        if request.custom_prompt:
            generated_response = await ai_service.generate_custom_response(message.text, request.custom_prompt)
        else:
            generated_response = await ai_service.generate_response(message)
        
        return GenerateResponseResponse(
            message_id=message_id,
            original_message=message.text,
            generated_response=generated_response,
            custom_prompt_used=request.custom_prompt is not None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate AI response: {str(e)}"
        ) 