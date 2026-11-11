from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.user import User
from app.models.user_exam import UserExam
from app.models.user_profile import UserProfile
from app.repositories import ExamRepository, UserExamRepository, UserProfileRepository
from app.schemas.auth import UserUpdate
from app.schemas.user import UserExamCreate, UserProfileUpdate
from app.services.base import BaseService


class UserService(BaseService):
    def __init__(self, db: Session) -> None:
        super().__init__(db)
        self.profiles = UserProfileRepository(db)
        self.user_exams = UserExamRepository(db)
        self.exams = ExamRepository(db)

    @staticmethod
    def _apply(target, values: dict) -> None:
        for field, value in values.items():
            setattr(target, field, value)

    def update_me(self, user: User, data: UserUpdate) -> User:
        self._apply(user, data.model_dump(exclude_unset=True))
        self.commit()
        return user

    def get_profile(self, user: User) -> UserProfile:
        profile = self.profiles.get_for_user(user.id)
        if profile is None:
            raise NotFoundError.for_resource("Profile")
        return profile

    def update_profile(self, user: User, data: UserProfileUpdate) -> UserProfile:
        profile = self.profiles.get_for_user(user.id) or self.profiles.add(UserProfile(user_id=user.id))
        self._apply(profile, data.model_dump(exclude_unset=True))
        self.commit()
        return profile

    def list_exams(self, user: User):
        return self.user_exams.list_for_user(user.id)

    def add_exam(self, user: User, data: UserExamCreate) -> UserExam:
        self.exams.require_active(data.exam_id)
        if self.user_exams.get_for_exam(user.id, data.exam_id):
            raise BadRequestError("Exam already added")
        user_exam = self.user_exams.add(UserExam(user_id=user.id, exam_id=data.exam_id, is_primary=data.is_primary))
        self.commit()
        return user_exam

    def remove_exam(self, user: User, exam_id: str) -> None:
        user_exam = self.user_exams.get_for_exam(user.id, exam_id)
        if user_exam is None:
            raise NotFoundError.for_resource("Exam")
        self.user_exams.delete(user_exam)
        self.commit()
