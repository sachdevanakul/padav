from typing import Optional
from app.schemas.base import ORMModel


class AnalyticsOverview(ORMModel):
    total_tests_taken: int
    average_score: float
    overall_accuracy: float
    total_study_hours: float
    current_streak: int
    total_questions_attempted: int
    active_dates: list[str] = []  # ISO dates with study activity in the last 7 days


class SubjectPerformance(ORMModel):
    subject_id: str
    subject_name: str
    subject_name_hi: Optional[str] = None
    questions_attempted: int
    correct_answers: int
    accuracy: float
    average_time_per_question: float


class TopicPerformance(ORMModel):
    topic_id: str
    topic_name: str
    questions_attempted: int
    correct_answers: int
    accuracy: float


class TrendPoint(ORMModel):
    date: str
    score: float
    accuracy: float
    questions_attempted: int