from typing import Optional

from pydantic import BaseModel
from datetime import datetime


class CommentCreate(BaseModel):
    content: str
    reply_delay: Optional[int] = None


class CommentResponse(BaseModel):
    id: int
    content: str
    post_id: int
    owner_id: int
    is_blocked: bool
    created_at: datetime


class CommentDataForTest(BaseModel):
    content: str
    post_id: int
    owner_id: int
    reply_delay: Optional[int] = None

    class Config:
        from_attributes = True
