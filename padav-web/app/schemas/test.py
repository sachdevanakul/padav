from datetime import datetime
from typing import List, Optional

from pydantic import Field

from app.schemas.base import ORMModel, StrictInput
from app.schemas.question import QuestionPublic


class TestBase(ORMModel):
    __test__ = False
    exam_id: str
    title: str
    title_hi: Optional[str] = None
    description: Optional[str] = None
    description_hi: Optional[str] = None
    total_questions: int = 0
    duration_minutes: int = 60
    total_marks: float = 0.0
    passing_marks: float = 0.0
    negative_marks_per_question: float = 0.0
    is_free: bool = True


class TestOut(TestBase):
    id: str
    is_active: bool
    created_at: datetime


class TestStartResponse(ORMModel):
    attempt_id: str
    test_id: str
    total_questions: int
    duration_minutes: int
    marks_per_question: float
    negative_marks_per_question: float


class AnswerSubmit(StrictInput):
    question_id: str = Field(min_length=1, max_length=36)
    selected_option_key: Optional[str] = Field(default=None, min_length=1, max_length=10)


class AttemptSummary(ORMModel):
    id: str
    test_id: str
    test_title: str = ""
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_questions: int
    attempted_questions: int
    correct_answers: int
    incorrect_answers: int
    unanswered_questions: int
    score_obtained: float
    max_score: float
    accuracy: float
    is_submitted: bool


class AnswerOut(ORMModel):
    question_id: str
    selected_option_key: Optional[str] = None
    # Correctness is withheld until the attempt is submitted (see TestService.detail).
    is_correct: Optional[bool] = None
    marks_obtained: Optional[float] = None


class AttemptDetail(AttemptSummary):
    duration_minutes: int = 0
    # Computed on the server so the client timer never depends on its own clock.
    seconds_remaining: Optional[int] = None  # None once submitted
    answers: List[AnswerOut] = []


class SubmitResult(ORMModel):
    attempt_id: str
    score_obtained: float
    max_score: float
    correct: int
    incorrect: int
    unanswered: int
    accuracy: float
    status: str


class ReviewItem(ORMModel):
    question: QuestionPublic
    correct_option_key: str
    selected_option_key: Optional[str] = None
    explanation: Optional[str] = None
    explanation_hi: Optional[str] = None
