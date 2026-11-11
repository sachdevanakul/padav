from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload

from app.models.question import Question
from app.models.question_option import QuestionOption
from app.models.study_session import StudySession
from app.models.test import Test
from app.models.test_answer import TestAnswer
from app.models.test_attempt import TestAttempt
from app.models.test_question import TestQuestion
from app.models.test_section import TestSection
from app.repositories.base import ActiveMixin, BaseRepository, OwnedRepository


class TestRepository(ActiveMixin, BaseRepository[Test]):
    model = Test
    resource_name = "Test"
    __test__ = False  # not a pytest class

    def list_active_for_exam(self, exam_id: str | None):
        stmt = select(Test).where(Test.is_active.is_(True))
        if exam_id:
            stmt = stmt.where(Test.exam_id == exam_id)
        return self.db.scalars(stmt).all()

    def question_ids(self, test_id: str) -> set[str]:
        return set(self.db.scalars(select(TestQuestion.question_id).where(TestQuestion.test_id == test_id)))

    def ordered_questions(self, test_id: str):
        """Active questions of a test in display order, with their options loaded."""
        return self.db.scalars(
            select(Question)
            .join(TestQuestion, TestQuestion.question_id == Question.id)
            .where(TestQuestion.test_id == test_id, Question.is_active.is_(True))
            .options(selectinload(Question.options))
            .order_by(TestQuestion.sort_order)
        ).all()

    def section_subject_ids(self, test_id: str) -> set[str]:
        rows = self.db.scalars(
            select(TestSection.subject_id).where(
                TestSection.test_id == test_id,
                TestSection.is_active.is_(True),
                TestSection.subject_id.is_not(None),
            )
        )
        return set(rows)


class QuestionRepository(ActiveMixin, BaseRepository[Question]):
    model = Question
    resource_name = "Question"

    def option_keys(self, question_id: str) -> set[str]:
        return set(self.db.scalars(select(QuestionOption.key).where(QuestionOption.question_id == question_id)))


class TestAttemptRepository(OwnedRepository[TestAttempt]):
    model = TestAttempt
    resource_name = "Attempt"
    __test__ = False

    def list_recent_for_user(self, user_id: str):
        return self.db.scalars(
            select(TestAttempt).where(TestAttempt.user_id == user_id).order_by(TestAttempt.started_at.desc())
        ).all()

    def list_completed_with_tests(self, user_id: str, *, chronological: bool = False):
        stmt = (
            select(TestAttempt)
            .where(TestAttempt.user_id == user_id, TestAttempt.status == "completed")
            .options(joinedload(TestAttempt.test))  # avoids one query per attempt
        )
        stmt = stmt.order_by(TestAttempt.completed_at if chronological else TestAttempt.started_at.desc())
        return self.db.scalars(stmt).all()

    def with_answers(self, attempt_id: str, user_id: str) -> TestAttempt | None:
        return self.db.scalars(
            select(TestAttempt)
            .where(TestAttempt.id == attempt_id, TestAttempt.user_id == user_id)
            .options(joinedload(TestAttempt.answers))
        ).unique().first()


class TestAnswerRepository(BaseRepository[TestAnswer]):
    model = TestAnswer
    resource_name = "Answer"
    __test__ = False

    def for_attempt_question(self, attempt_id: str, question_id: str) -> TestAnswer | None:
        return self.db.scalars(
            select(TestAnswer).where(TestAnswer.attempt_id == attempt_id, TestAnswer.question_id == question_id)
        ).first()

    def list_for_attempt(self, attempt_id: str):
        return self.db.scalars(select(TestAnswer).where(TestAnswer.attempt_id == attempt_id)).all()

    def count_for_attempt(self, attempt_id: str) -> int:
        return self.db.scalar(select(func.count()).select_from(TestAnswer).where(TestAnswer.attempt_id == attempt_id)) or 0


class StudySessionRepository(OwnedRepository[StudySession]):
    model = StudySession
    resource_name = "Study session"

    def total_minutes(self, user_id: str) -> int:
        return self.db.scalar(
            select(func.coalesce(func.sum(StudySession.minutes_spent), 0)).where(StudySession.user_id == user_id)
        ) or 0
