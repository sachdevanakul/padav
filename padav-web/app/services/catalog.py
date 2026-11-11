from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError
from app.models.lesson import Lesson
from app.models.user import User
from app.repositories import CourseRepository, ExamRepository, LessonRepository
from app.services.base import BaseService


class CatalogService(BaseService):
    def __init__(self, db: Session) -> None:
        super().__init__(db)
        self.exams = ExamRepository(db)
        self.courses = CourseRepository(db)
        self.lessons = LessonRepository(db)

    def list_exams(self):
        return self.exams.list_active()

    def get_exam(self, exam_id: str):
        return self.exams.require_active(exam_id)

    def list_courses(self, subject_id: str | None):
        return self.courses.list_active_for_subject(subject_id)

    def get_course(self, course_id: str):
        return self.courses.require_active(course_id)

    def get_chapters(self, course_id: str):
        self.courses.require_active(course_id)
        return self.courses.chapters_with_lessons(course_id)

    def get_lesson(self, lesson_id: str, viewer: User | None) -> Lesson:
        lesson = self.lessons.require_active(lesson_id)
        if not lesson.is_free and viewer is None:
            raise AuthenticationError("Sign in to view this lesson")
        return lesson
