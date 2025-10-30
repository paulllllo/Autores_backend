from beanie import Document, Indexed
from datetime import datetime
from pydantic import Field


class OAuthState(Document):
    state: Indexed(str, unique=True)
    code_verifier: str
    created_at: datetime
    
    class Settings:
        name = "oauth_states"
        indexes = [
            "state",
            "created_at",
        ]