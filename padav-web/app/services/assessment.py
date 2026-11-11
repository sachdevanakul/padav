from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.exceptions import BadRequestError, ConflictError
from app.models.question import Question
from app.models.test import Test
from app.models.test_answer import TestAnswer
from app.models.test_attempt import TestAttempt
from app.models.user import User
from app.repositories import (
    QuestionRepository,
    TestAnswerRepository,
    TestAttemptRepository,
    TestRepository,
)
from app.schemas.question import QuestionPublic
from app.schemas.test import (
    AnswerOut,
    AnswerSubmit,
    AttemptDetail,
    AttemptSummary,
    ReviewItem,
    SubmitResult,
    TestStartResponse,
)
from app.services.base import BaseService

TIME_GRACE = timedelta(seconds=60)  # network latency allowance on the last answer


class ScoringPolicy:
    """Single place where marks are decided. Always computed server-side."""

    @staticmethod
    def evaluate(question: Question, selected: str | None) -> tuple[bool, float]:
        if selected is None:  # cleared / skipped: no credit, no penalty
            return False, 0.0
        if selected == question.correct_option_key:
            return True, question.marks
        return False, -question.negative_marks


class TestService(BaseService):
    __test__ = False

    def __init__(self, db: Session, scoring: ScoringPolicy | None = None) -> None:
        super().__init__(db)
        self.tests = TestRepository(db)
        self.questions = QuestionRepository(db)
        self.attempts = TestAttemptRepository(db)
        self.answers = TestAnswerRepository(db)
        self.scoring = scoring or ScoringPolicy()

    # -- catalogue ----------------------------------------------------------------
    def list_tests(self, exam_id: str | None):
        return self.tests.list_active_for_exam(exam_id)

    def get_test(self, test_id: str) -> Test:
        return self.tests.require_active(test_id)

    # -- attempt lifecycle ----------------------------------------------------------
    def start(self, user: User, test_id: str) -> TestStartResponse:
        test = self.tests.require_active(test_id)
        attempt = self.attempts.add(TestAttempt(
            user_id=user.id,
            test_id=test.id,
            status="in_progress",
            total_questions=test.total_questions,
            max_score=test.total_marks,
        ))
        self.commit()
        return TestStartResponse(
            attempt_id=attempt.id,
            test_id=test.id,
            total_questions=test.total_questions,
            duration_minutes=test.duration_minutes,
            marks_per_question=test.marks_per_question,
            negative_marks_per_question=test.negative_marks_per_question,
        )

    def save_answer(self, user: User, attempt_id: str, data: AnswerSubmit) -> None:
        attempt = self.attempts.require_owned(attempt_id, user.id)
        self._ensure_open(attempt)

        question = self.questions.require_active(data.question_id)
        self._ensure_question_belongs(attempt, question)
        if data.selected_option_key is not None and data.selected_option_key not in self.questions.option_keys(question.id):
            raise BadRequestError("Invalid option for this question")

        is_correct, marks = self.scoring.evaluate(question, data.selected_option_key)
        record = self.answers.for_attempt_question(attempt.id, question.id)
        if record is None:
            if self.answers.count_for_attempt(attempt.id) >= attempt.total_questions:
                raise BadRequestError("Too many answers for this attempt")
            record = self.answers.add(TestAnswer(attempt_id=attempt.id, question_id=question.id))
        record.selected_option_key = data.selected_option_key
        record.is_correct = is_correct
        record.marks_obtained = marks
        record.answered_at = utcnow()
        self.commit()

    def submit(self, user: User, attempt_id: str) -> SubmitResult:
        attempt = self.attempts.require_owned(attempt_id, user.id)
        if attempt.is_submitted:
            raise BadRequestError("Test already submitted")  # Late submits are allowed: they only close the attempt.

        answered = [a for a in self.answers.list_for_attempt(attempt.id) if a.selected_option_key is not None]
        correct = sum(1 for a in answered if a.is_correct)
        attempt.status = "completed"
        attempt.is_submitted = True
        attempt.completed_at = utcnow()
        attempt.attempted_questions = len(answered)
        attempt.correct_answers = correct
        attempt.incorrect_answers = len(answered) - correct
        attempt.unanswered_questions = max(attempt.total_questions - len(answered), 0)
        attempt.score_obtained = sum(a.marks_obtained for a in answered)
        attempt.accuracy = (correct / len(answered) * 100) if answered else 0.0
        self.commit()
        return SubmitResult(
            attempt_id=attempt.id,
            score_obtained=attempt.score_obtained,
            max_score=attempt.max_score,
            correct=correct,
            incorrect=attempt.incorrect_answers,
            unanswered=attempt.unanswered_questions,
            accuracy=attempt.accuracy,
            status=attempt.status,
        )

    # -- reads ----------------------------------------------------------------------
    def list_attempts(self, user: User) -> list[AttemptSummary]:
        return [self._summary(a) for a in self.attempts.list_recent_for_user(user.id)]

    @staticmethod
    def _summary(attempt: TestAttempt) -> AttemptSummary:
        title = attempt.test.title if attempt.test else ""
        return AttemptSummary.model_validate(attempt).model_copy(update={"test_title": title})

    def detail(self, user: User, attempt_id: str) -> AttemptDetail:
        attempt = self.attempts.with_answers(attempt_id, user.id) or self.attempts.require_owned(attempt_id, user.id)
        reveal = attempt.is_submitted  # never tell a candidate what is right mid-test
        answers = [
            AnswerOut(
                question_id=a.question_id,
                selected_option_key=a.selected_option_key,
                is_correct=a.is_correct if reveal else None,
                marks_obtained=a.marks_obtained if reveal else None,
            )
            for a in attempt.answers
        ]
        duration = attempt.test.duration_minutes if attempt.test else 0
        remaining = None
        if not attempt.is_submitted:
            deadline = attempt.started_at + timedelta(minutes=duration)
            remaining = max(0, int((deadline - utcnow()).total_seconds()))
        return AttemptDetail(
            **self._summary(attempt).model_dump(),
            duration_minutes=duration,
            seconds_remaining=remaining,
            answers=answers,
        )

    def attempt_questions(self, user: User, attempt_id: str) -> list[QuestionPublic]:
        """Questions for an *open* attempt. Never includes answers or explanations."""
        attempt = self.attempts.require_owned(attempt_id, user.id)
        if attempt.is_submitted:
            raise BadRequestError("Test already submitted")
        return [QuestionPublic.model_validate(q) for q in self.tests.ordered_questions(attempt.test_id)]

    def review(self, user: User, attempt_id: str) -> list[ReviewItem]:
        """Answer key + explanations, only after the attempt is submitted."""
        attempt = self.attempts.require_owned(attempt_id, user.id)
        if not attempt.is_submitted:
            raise BadRequestError("Submit the test to see the review")
        chosen = {a.question_id: a.selected_option_key for a in self.answers.list_for_attempt(attempt.id)}
        return [
            ReviewItem(
                question=QuestionPublic.model_validate(q),
                correct_option_key=q.correct_option_key,
                selected_option_key=chosen.get(q.id),
                explanation=q.explanation,
                explanation_hi=q.explanation_hi,
            )
            for q in self.tests.ordered_questions(attempt.test_id)
        ]

    # -- guards ---------------------------------------------------------------------
    def _ensure_open(self, attempt: TestAttempt) -> None:
        if attempt.is_submitted:
            raise BadRequestError("Test already submitted")
        test = self.tests.get(attempt.test_id)
        if test is not None and utcnow() > attempt.started_at + timedelta(minutes=test.duration_minutes) + TIME_GRACE:
            raise ConflictError("Time limit exceeded; submit the test")

    def _ensure_question_belongs(self, attempt: TestAttempt, question: Question) -> None:
        """A question may only be answered if it is part of the attempt's test."""
        members = self.tests.question_ids(attempt.test_id)
        if members:
            if question.id not in members:
                raise BadRequestError("Question is not part of this test")
            return
        # Legacy tests without explicit membership: fall back to section subjects.
        allowed = self.tests.section_subject_ids(attempt.test_id)
        if allowed and question.subject_id not in allowed:
            raise BadRequestError("Question is not part of this test")
