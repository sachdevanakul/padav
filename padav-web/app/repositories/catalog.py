from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.chapter import Chapter
from app.models.course import Course
from app.models.exam import Exam
from app.models.lesson import Lesson
from app.repositories.base import ActiveMixin, BaseRepository


class ExamRepository(ActiveMixin, BaseRepository[Exam]):
    model = Exam
    resource_name = "Exam"


class CourseRepository(ActiveMixin, BaseRepository[Course]):
    model = Course
    resource_name = "Course"

    def list_active_for_subject(self, subject_id: str | None):
        stmt = select(Course).where(Course.is_active.is_(True))
        if subject_id:
            stmt = stmt.where(Course.subject_id == subject_id)
        return self.db.scalars(stmt).all()

    def chapters_with_lessons(self, course_id: str):
        """Active chapters, each with only its *active* lessons."""
        stmt = (
            select(Chapter)
            .where(Chapter.course_id == course_id, Chapter.is_active.is_(True))
            .options(selectinload(Chapter.lessons.and_(Lesson.is_active.is_(True))))
            .order_by(Chapter.sort_order)
        )
        return self.db.scalars(stmt).all()


class LessonRepository(ActiveMixin, BaseRepository[Lesson]):
    model = Lesson
    resource_name = "Lesson"
