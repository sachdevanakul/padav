from datetime import datetime

from sqlalchemy import func, select, update

from app.core.clock import utcnow
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.models.user_exam import UserExam
from app.models.user_profile import UserProfile
from app.repositories.base import BaseRepository, OwnedRepository


class UserRepository(BaseRepository[User]):
    model = User
    resource_name = "User"

    def get_by_email(self, email: str) -> User | None:
        # Case-insensitive so "A@x.com" and "a@x.com" can never be two accounts.
        return self.db.scalars(select(User).where(func.lower(User.email) == email.lower())).first()


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    model = RefreshToken
    resource_name = "Refresh token"

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        return self.db.scalars(select(RefreshToken).where(RefreshToken.token_hash == token_hash)).first()

    def store(self, user_id: str, token_hash: str, expires_at: datetime) -> RefreshToken:
        return self.add(RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at))

    def revoke_all_for_user(self, user_id: str) -> None:
        self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=utcnow())
        )


class UserProfileRepository(BaseRepository[UserProfile]):
    model = UserProfile
    resource_name = "Profile"

    def get_for_user(self, user_id: str) -> UserProfile | None:
        return self.db.scalars(select(UserProfile).where(UserProfile.user_id == user_id)).first()


class UserExamRepository(OwnedRepository[UserExam]):
    model = UserExam
    resource_name = "Exam"

    def get_for_exam(self, user_id: str, exam_id: str) -> UserExam | None:
        return self.db.scalars(
            select(UserExam).where(UserExam.user_id == user_id, UserExam.exam_id == exam_id)
        ).first()
