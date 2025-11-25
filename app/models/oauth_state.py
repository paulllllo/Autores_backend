from beanie import Document, Indexed
from datetime import datetime
from pydantic import Field
from typing import Optional


class OAuthState(Document):
    state: Indexed(str, unique=True)
    code_verifier: str
    app_user_id: Optional[str] = None  # Link to app user adding this Twitter account
    created_at: datetime
    
    class Settings:
        name = "oauth_states"
        indexes = [
            "state",
            "created_at",
        ]