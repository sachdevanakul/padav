from fastapi import APIRouter
from typing import List

from app.core.dependencies import DbSession, CurrentUser
from app.models.test_attempt import TestAttempt
from app.schemas.analytics import AnalyticsOverview, SubjectPerformance, TrendPoint

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def get_overview(current_user: CurrentUser, db: DbSession):
    """Get overall analytics overview for the user."""
    attempts = db.query(TestAttempt).filter(TestAttempt.user_id == current_user.id).all()
    total_tests = len(attempts)
    completed = [a for a in attempts if a.status == "completed"]
    avg_score = sum(a.score_obtained for a in completed) / len(completed) if completed else 0
    avg_accuracy = sum(a.accuracy for a in completed) / len(completed) if completed else 0
    total_questions = sum(a.attempted_questions for a in attempts)
    total_correct = sum(a.correct_answers for a in attempts)
    overall_accuracy = (total_correct / total_questions * 100) if total_questions else 0

    # Study hours from study_sessions
    from app.models.study_session import StudySession
    sessions = db.query(StudySession).filter(StudySession.user_id == current_user.id).all()
    total_hours = sum(s.minutes_spent for s in sessions) / 60

    return AnalyticsOverview(
        total_tests_taken=total_tests,
        average_score=round(avg_score, 2),
        overall_accuracy=round(overall_accuracy, 2),
        total_study_hours=round(total_hours, 2),
        current_streak=0,  # Simplified
        total_questions_attempted=total_questions,
    )


@router.get("/subjects", response_model=List[SubjectPerformance])
def get_subject_performance(current_user: CurrentUser, db: DbSession):
    """Get subject-wise performance."""
    attempts = (
        db.query(TestAttempt)
        .filter(TestAttempt.user_id == current_user.id, TestAttempt.status == "completed")
        .all()
    )
    # Simplified: group by test -> subject via test relationship
    results = []
    for attempt in attempts:
        test = attempt.test
        if test:
            results.append(
                SubjectPerformance(
                    subject_id=test.exam_id,
                    subject_name=test.title,
                    questions_attempted=attempt.attempted_questions,
                    correct_answers=attempt.correct_answers,
                    accuracy=attempt.accuracy,
                    average_time_per_question=0.0,
                )
            )
    return results


@router.get("/trends", response_model=List[TrendPoint])
def get_trends(current_user: CurrentUser, db: DbSession):
    """Get performance trends over time."""
    attempts = (
        db.query(TestAttempt)
        .filter(TestAttempt.user_id == current_user.id, TestAttempt.status == "completed")
        .order_by(TestAttempt.completed_at)
        .all()
    )
    return [
        TrendPoint(
            date=a.completed_at.isoformat() if a.completed_at else "",
            score=a.score_obtained,
            accuracy=a.accuracy,
            questions_attempted=a.attempted_questions,
        )
        for a in attempts
    ]
