from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    post_id: int
    reply_delay: Optional[int] = Field(default=0, description="Delay in seconds before the auto-reply")


class Comment(CommentBase):
    id: int
    created_at: datetime
    post_id: int

    class Config:
        from_attributes = True


class PostBase(BaseModel):
    title: str
    content: str


class PostCreate(PostBase):
    pass


class Post(PostBase):
    id: int
    created_at: datetime
    owner_id: int
    comments: List[Comment] = []

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    posts: List[Post] = []

    class Config:
        from_attributes = True


class CommentsBreakdown(BaseModel):
    date: str
    total_comments: int
    blocked_comments: int
