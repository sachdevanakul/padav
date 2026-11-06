from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class QuestionOptionBase(BaseModel):
    key: str
    text: str
    text_hi: Optional[str] = None


class QuestionOptionOut(QuestionOptionBase):
    id: str
    is_correct: bool

    class Config:
        from_attributes = True


class QuestionBase(BaseModel):
    lesson_id: Optional[str] = None
    subject_id: str
    text: str
    text_hi: Optional[str] = None
    explanation: Optional[str] = None
    explanation_hi: Optional[str] = None
    difficulty: str = "easy"
    marks: float = 1.0
    negative_marks: float = 0.0
    correct_option_key: str


class QuestionOut(QuestionBase):
    id: str
    options: List[QuestionOptionOut] = Field(default_factory=list)
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
