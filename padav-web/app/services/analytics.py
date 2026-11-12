from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.clock import utcnow

from app.models.user import User
from app.repositories import PlannerBlockRepository, StudySessionRepository, TestAttemptRepository
from app.schemas.analytics import AnalyticsOverview, SubjectPerformance, TrendPoint
from app.services.base import BaseService


class AnalyticsService(BaseService):
    def __init__(self, db: Session) -> None:
        super().__init__(db)
        self.attempts = TestAttemptRepository(db)
        self.sessions = StudySessionRepository(db)
        self.planner = PlannerBlockRepository(db)

    def _active_dates(self, user: User, attempts, tz_offset: int) -> set[date]:
        """Days with a finished test or a completed planner session, in the user's local time."""
        shift = timedelta(minutes=tz_offset)
        days = {(a.completed_at + shift).date() for a in attempts if a.status == "completed" and a.completed_at}
        return days | self.planner.completed_dates(user.id)  # planner dates are already local

    @staticmethod
    def _streak(days: set[date], today: date) -> int:
        # A streak stays alive until the end of the day after the last activity.
        cursor = today if today in days else today - timedelta(days=1)
        count = 0
        while cursor in days:
            count += 1
            cursor -= timedelta(days=1)
        return count

    def overview(self, user: User, tz_offset: int = 0) -> AnalyticsOverview:
        attempts = self.attempts.list_recent_for_user(user.id)
        completed = [a for a in attempts if a.status == "completed"]
        asked = sum(a.attempted_questions for a in attempts)
        correct = sum(a.correct_answers for a in attempts)
        n = len(completed)
        today = (utcnow() + timedelta(minutes=tz_offset)).date()
        days = self._active_dates(user, attempts, tz_offset)
        return AnalyticsOverview(
            total_tests_taken=len(attempts),
            average_score=round(sum(a.score_obtained for a in completed) / n, 2) if n else 0,
            overall_accuracy=round(correct / asked * 100, 2) if asked else 0,
            total_study_hours=round(self.sessions.total_minutes(user.id) / 60, 2),
            current_streak=self._streak(days, today),
            total_questions_attempted=asked,
            active_dates=sorted(d.isoformat() for d in days if today - timedelta(days=6) <= d <= today),
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
