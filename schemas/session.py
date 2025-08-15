from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class SessionData(BaseModel):
    session_name: str

class ChatMessage(BaseModel):
    session_id: UUID
    message: str
    question : str
    timestamp: datetime

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None