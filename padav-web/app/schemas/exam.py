from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ExamBase(BaseModel):
    name: str
    name_hi: Optional[str] = None
    code: str
    description: Optional[str] = None
    description_hi: Optional[str] = None
    category: str


class ExamOut(ExamBase):
    id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserExamCreate(BaseModel):
    exam_id: str
    is_primary: bool = False