from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "Twitter Mentions API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith("mysql+pymysql://"):
            raise ValueError("DATABASE_URL must start with mysql+pymysql://")
        return v
    
    # Twitter API
    TWITTER_CLIENT_ID: str
    TWITTER_CLIENT_SECRET: str
    TWITTER_CALLBACK_URL: str
    TWITTER_SCOPE: str = 'tweet.read tweet.write users.read offline.access'
    
    # Twitter API Rate Limits (Essential tier)
    TWITTER_MENTIONS_RATE_LIMIT: int = 50  # requests per window
    TWITTER_MENTIONS_WINDOW: int = 15  # minutes
    TWITTER_POLLING_INTERVAL: int = 5  # minutes between polls
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings() 