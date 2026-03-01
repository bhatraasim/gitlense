from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class User(BaseModel):
    id: Optional[str] = None
    name: str
    email: EmailStr
    hashed_password: str
    created_at: datetime = datetime.utcnow()


class UserResponse(BaseModel):
    """What you return to the frontend — no password"""
    id: str
    name: str
    email: str
    created_at: datetime