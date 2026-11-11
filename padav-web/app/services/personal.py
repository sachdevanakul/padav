from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ConflictError
from app.models.bookmark import Bookmark
from app.models.planner_block import PlannerBlock
from app.models.user import User
from app.repositories import BookmarkRepository, LessonRepository, PlannerBlockRepository, QuestionRepository
from app.schemas.bookmark import BookmarkCreate
from app.schemas.planner import PlannerBlockCreate
from app.services.base import BaseService

MAX_PLANNER_RANGE_DAYS = 41


class BookmarkService(BaseService):
    def __init__(self, db: Session) -> None:
        super().__init__(db)
        self.bookmarks = BookmarkRepository(db)
        self.questions = QuestionRepository(db)
        self.lessons = LessonRepository(db)

    def list(self, user: User):
        return self.bookmarks.list_for_user(user.id)

    def create(self, user: User, data: BookmarkCreate) -> Bookmark:
        # The target must exist and be visible; otherwise users could probe ids / hit FK errors.
        if data.question_id:
            self.questions.require_active(data.question_id)
        else:
            self.lessons.require_active(data.lesson_id)  # type: ignore[arg-type]
        if self.bookmarks.find_existing(user.id, data.question_id, data.lesson_id):
            raise ConflictError("Already bookmarked")
        bookmark = self.bookmarks.add(Bookmark(user_id=user.id, **data.model_dump()))
        self.commit()
        return bookmark

    def delete(self, user: User, bookmark_id: str) -> None:
        self.bookmarks.delete(self.bookmarks.require_owned(bookmark_id, user.id))
        self.commit()


class PlannerService(BaseService):
    def __init__(self, db: Session) -> None:
        super().__init__(db)
        self.blocks = PlannerBlockRepository(db)

    def list_range(self, user: User, start: date, end: date):
        if end < start or (end - start).days > MAX_PLANNER_RANGE_DAYS:
            raise BadRequestError("Date range must be ordered and no longer than six weeks")
        return self.blocks.in_range(user.id, start, end)

    def create(self, user: User, data: PlannerBlockCreate) -> PlannerBlock:
        if self.blocks.has_overlap(user.id, data.study_date, data.start_time, data.end_time):
            raise ConflictError("This session overlaps another planned session")
        block = self.blocks.add(PlannerBlock(user_id=user.id, **data.model_dump()))
        self.commit()
        return block

    def set_completed(self, user: User, block_id: str, completed: bool) -> PlannerBlock:
        block = self.blocks.require_owned(block_id, user.id)
        block.completed = completed
        self.commit()
        return block

    def delete(self, user: User, block_id: str) -> None:
        self.blocks.delete(self.blocks.require_owned(block_id, user.id))
        self.commit()
