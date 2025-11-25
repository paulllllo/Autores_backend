from fastapi import APIRouter
from app.api.v1.endpoints import auth, messages, accounts, users

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(messages.router, prefix="/mentions", tags=["messages"]) 