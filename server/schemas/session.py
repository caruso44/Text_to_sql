from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class SessionData(BaseModel):
    session_id: UUID
    username: str

class ChatMessage(BaseModel):
    session_id: UUID
    message: str
    question : str
    timestamp: datetime
