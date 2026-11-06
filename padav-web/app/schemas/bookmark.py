from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BookmarkBase(BaseModel):
    question_id: Optional[str] = None
    lesson_id: Optional[str] = None


class BookmarkOut(BookmarkBase):
    id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True