from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import StudySessionRepository, TestAttemptRepository
from app.schemas.analytics import AnalyticsOverview, SubjectPerformance, TrendPoint
from app.services.base import BaseService


class AnalyticsService(BaseService):
    def __init__(self, db: Session) -> None:
        super().__init__(db)
        self.attempts = TestAttemptRepository(db)
        self.sessions = StudySessionRepository(db)

    def overview(self, user: User) -> AnalyticsOverview:
        attempts = self.attempts.list_recent_for_user(user.id)
        completed = [a for a in attempts if a.status == "completed"]
        asked = sum(a.attempted_questions for a in attempts)
        correct = sum(a.correct_answers for a in attempts)
        n = len(completed)
        return AnalyticsOverview(
            total_tests_taken=len(attempts),
            average_score=round(sum(a.score_obtained for a in completed) / n, 2) if n else 0,
            overall_accuracy=round(correct / asked * 100, 2) if asked else 0,
            total_study_hours=round(self.sessions.total_minutes(user.id) / 60, 2),
            current_streak=0,  # not implemented yet
            total_questions_attempted=asked,
        )

    def subjects(self, user: User) -> list[SubjectPerformance]:
        return [
            SubjectPerformance(
                subject_id=a.test.exam_id,
                subject_name=a.test.title,
                questions_attempted=a.attempted_questions,
                correct_answers=a.correct_answers,
                accuracy=a.accuracy,
                average_time_per_question=0.0,
            )
            for a in self.attempts.list_completed_with_tests(user.id)
            if a.test
        ]

    def trends(self, user: User) -> list[TrendPoint]:
        return [
            TrendPoint(
                date=a.completed_at.isoformat() if a.completed_at else "",
                score=a.score_obtained,
                accuracy=a.accuracy,
                questions_attempted=a.attempted_questions,
            )
            for a in self.attempts.list_completed_with_tests(user.id, chronological=True)
        ]
