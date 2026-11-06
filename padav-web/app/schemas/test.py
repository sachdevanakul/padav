from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TestBase(BaseModel):
    exam_id: str
    title: str
    title_hi: Optional[str] = None
    description: Optional[str] = None
    description_hi: Optional[str] = None
    total_questions: int = 0
    duration_minutes: int = 60
    total_marks: float = 0.0
    passing_marks: float = 0.0
    negative_marking: bool = True
    marks_per_question: float = 1.0
    negative_marks_per_question: float = 0.0
    is_free: bool = True


class TestOut(TestBase):
    id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TestStartResponse(BaseModel):
    attempt_id: str
    test_id: str
    total_questions: int
    duration_minutes: int
    marks_per_question: float
    negative_marks_per_question: float


class AnswerSubmit(BaseModel):
    question_id: str
    selected_option_key: Optional[str] = None


class TestSubmit(BaseModel):
    attempt_id: str