from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Optional

from app.models.app_user import AppUser
from app.schemas.app_user import (
    UserRegister,
    UserLogin,
    Token,
    UserInDB,
    UserUpdate,
    PasswordChange
)
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token
)
from app.core.deps import get_current_user, get_current_superuser
from app.core.config import settings


router = APIRouter()


@router.post("/register", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister):
    """
    Register a new user with username and password
    """
    # Check if username already exists
    existing_user = await AppUser.find_one(AppUser.username == user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = await AppUser.find_one(AppUser.email == user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = AppUser(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
        is_superuser=False
    )
    
    await new_user.insert()
    
    return UserInDB.model_validate(new_user)


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login with username and password to get access token
    OAuth2 compatible token login, get an access token for future requests
    """
    # Find user by username
    user = await AppUser.find_one(AppUser.username == form_data.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await user.save()
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserInDB)
async def get_current_user_info(current_user: AppUser = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    return UserInDB.model_validate(current_user)


@router.patch("/me", response_model=UserInDB)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: AppUser = Depends(get_current_user)
):
    """
    Update current user's profile
    """
    # Update fields if provided
    if user_update.email is not None:
        # Check if email is already taken by another user
        existing_email = await AppUser.find_one(
            AppUser.email == user_update.email,
            AppUser.id != current_user.id
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email
    
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    if user_update.password is not None:
        current_user.hashed_password = get_password_hash(user_update.password)
    
    current_user.updated_at = datetime.utcnow()
    await current_user.save()
    
    return UserInDB.model_validate(current_user)


@router.post("/me/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: AppUser = Depends(get_current_user)
):
    """
    Change current user's password
    """
    # Verify current password
    if not verify_password(password_change.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_change.new_password)
    current_user.updated_at = datetime.utcnow()
    await current_user.save()
    
    return {"message": "Password changed successfully"}


@router.delete("/me")
async def delete_account(current_user: AppUser = Depends(get_current_user)):
    """
    Delete current user's account
    """
    await current_user.delete()
    return {"message": "Account deleted successfully"}

