from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Document(BaseModel):
    id: str
    filename: str
    created_at: datetime
    content_type: str
    size: int

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None