from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: str
    username: str
    content: str
    timestamp: datetime
    room_id: str

    class Config:
        from_attributes = True