from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime

from app.core.dependencies import DbSession, CurrentUser
from app.models.test import Test
from app.models.test_answer import TestAnswer
from app.models.test_attempt import TestAttempt
from app.models.question import Question
from app.schemas.test import TestOut, TestStartResponse

router = APIRouter(prefix="/tests", tags=["tests"])


@router.get("", response_model=List[TestOut])
@router.get("/", response_model=List[TestOut], include_in_schema=False)
def list_tests(db: DbSession, exam_id: str | None = None):
    """List all active tests, optionally filtered by exam."""
    query = db.query(Test).filter(Test.is_active == True)
    if exam_id:
        query = query.filter(Test.exam_id == exam_id)
    return query.all()


@router.get("/{test_id}", response_model=TestOut)
def get_test(test_id: str, db: DbSession):
    """Get a single test by ID."""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test


@router.post("/{test_id}/start", response_model=TestStartResponse)
def start_test(test_id: str, current_user: CurrentUser, db: DbSession):
    """Start a new test attempt."""
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    attempt = TestAttempt(
        user_id=current_user.id,
        test_id=test_id,
        status="in_progress",
        total_questions=test.total_questions,
        max_score=test.total_marks,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return TestStartResponse(
        attempt_id=str(attempt.id),
        test_id=str(test.id),
        total_questions=test.total_questions,
        duration_minutes=test.duration_minutes,
        marks_per_question=test.marks_per_question,
        negative_marks_per_question=test.negative_marks_per_question,
    )


@router.put("/attempts/{attempt_id}/answers")
def save_answer(attempt_id: str, question_id: str, selected_option_key: str | None, current_user: CurrentUser, db: DbSession):
    """Save or update an answer for a test attempt."""
    attempt = (
        db.query(TestAttempt)
        .filter(TestAttempt.id == attempt_id, TestAttempt.user_id == current_user.id)
        .first()
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.is_submitted:
        raise HTTPException(status_code=400, detail="Test already submitted")

    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    is_correct = selected_option_key == question.correct_option_key
    marks = question.marks if is_correct else -question.negative_marks

    existing = (
        db.query(TestAnswer)
        .filter(TestAnswer.attempt_id == attempt_id, TestAnswer.question_id == question_id)
        .first()
    )
    if existing:
        existing.selected_option_key = selected_option_key
        existing.is_correct = is_correct
        existing.marks_obtained = marks
        existing.answered_at = datetime.utcnow()
    else:
        answer_record = TestAnswer(
            attempt_id=attempt_id,
            question_id=question_id,
            selected_option_key=selected_option_key,
            is_correct=is_correct,
            marks_obtained=marks,
            answered_at=datetime.utcnow(),
        )
        db.add(answer_record)

    db.commit()
    return {"message": "Answer saved"}


@router.post("/attempts/{attempt_id}/submit")
def submit_test(attempt_id: str, current_user: CurrentUser, db: DbSession):
    """Submit a test attempt and compute final score."""
    attempt = (
        db.query(TestAttempt)
        .filter(TestAttempt.id == attempt_id, TestAttempt.user_id == current_user.id)
        .first()
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.is_submitted:
        raise HTTPException(status_code=400, detail="Test already submitted")

    answers = db.query(TestAnswer).filter(TestAnswer.attempt_id == attempt_id).all()
    correct = sum(1 for a in answers if a.is_correct)
    incorrect = sum(1 for a in answers if a.selected_option_key is not None and not a.is_correct)
    unanswered = sum(1 for a in answers if a.selected_option_key is None)
    score = sum(a.marks_obtained for a in answers)

    attempt.status = "completed"
    attempt.is_submitted = True
    attempt.completed_at = datetime.utcnow()
    attempt.attempted_questions = len(answers)
    attempt.correct_answers = correct
    attempt.incorrect_answers = incorrect
    attempt.unanswered_questions = unanswered
    attempt.score_obtained = score
    attempt.accuracy = (correct / len(answers) * 100) if answers else 0.0

    db.commit()
    db.refresh(attempt)

    return {
        "attempt_id": str(attempt.id),
        "score_obtained": attempt.score_obtained,
        "max_score": attempt.max_score,
        "correct": correct,
        "incorrect": incorrect,
        "unanswered": unanswered,
        "accuracy": attempt.accuracy,
        "status": attempt.status,
    }


@router.get("/attempts")
def list_my_attempts(current_user: CurrentUser, db: DbSession):
    """List current user's test attempts."""
    return db.query(TestAttempt).filter(TestAttempt.user_id == current_user.id).order_by(TestAttempt.started_at.desc()).all()


@router.get("/attempts/{attempt_id}")
def get_attempt(attempt_id: str, current_user: CurrentUser, db: DbSession):
    """Get a single test attempt with answers."""
    attempt = (
        db.query(TestAttempt)
        .filter(TestAttempt.id == attempt_id, TestAttempt.user_id == current_user.id)
        .first()
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return attempt
