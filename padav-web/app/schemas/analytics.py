from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AnalyticsOverview(BaseModel):
    total_tests_taken: int
    average_score: float
    overall_accuracy: float
    total_study_hours: float
    current_streak: int
    total_questions_attempted: int


class SubjectPerformance(BaseModel):
    subject_id: str
    subject_name: str
    subject_name_hi: Optional[str] = None
    questions_attempted: int
    correct_answers: int
    accuracy: float
    average_time_per_question: float


class TopicPerformance(BaseModel):
    topic_id: str
    topic_name: str
    questions_attempted: int
    correct_answers: int
    accuracy: float


class TrendPoint(BaseModel):
    date: str
    score: float
    accuracy: float
    questions_attempted: int