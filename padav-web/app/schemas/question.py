from datetime import datetime
from typing import List, Optional

from pydantic import Field

from app.schemas.base import ORMModel


class QuestionOptionPublic(ORMModel):
    """What a candidate may see. Never includes correctness."""

    id: str
    key: str
    text: str
    text_hi: Optional[str] = None


class QuestionPublic(ORMModel):
    id: str
    lesson_id: Optional[str] = None
    subject_id: str
    text: str
    text_hi: Optional[str] = None
    difficulty: str = "easy"
    marks: float = 1.0
    negative_marks: float = 0.0
    options: List[QuestionOptionPublic] = Field(default_factory=list)


class QuestionOptionAdmin(QuestionOptionPublic):
    is_correct: bool


class QuestionAdminOut(QuestionPublic):
    """Reveals answers and explanations. For authoring/review endpoints only."""

    explanation: Optional[str] = None
    explanation_hi: Optional[str] = None
    correct_option_key: str
    options: List[QuestionOptionAdmin] = Field(default_factory=list)  # type: ignore[assignment]
    is_active: bool
    created_at: datetime
