"""
Enums for model fields to ensure type safety and OpenAPI documentation
"""
from enum import Enum


class AccountSyncStatus(str, Enum):
    """Status of account synchronization"""
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    TOKEN_EXPIRED = "token_expired"
    RATE_LIMITED = "rate_limited"


class MessageStatus(str, Enum):
    """Status of message processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    REPLIED = "replied"
    IGNORED = "ignored"
    ERROR = "error"



