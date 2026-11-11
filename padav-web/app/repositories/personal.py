from datetime import date, time

from sqlalchemy import select

from app.models.bookmark import Bookmark
from app.models.planner_block import PlannerBlock
from app.repositories.base import OwnedRepository


class BookmarkRepository(OwnedRepository[Bookmark]):
    model = Bookmark
    resource_name = "Bookmark"

    def find_existing(self, user_id: str, question_id: str | None, lesson_id: str | None) -> Bookmark | None:
        stmt = select(Bookmark).where(Bookmark.user_id == user_id)
        stmt = stmt.where(Bookmark.question_id == question_id if question_id else Bookmark.question_id.is_(None))
        stmt = stmt.where(Bookmark.lesson_id == lesson_id if lesson_id else Bookmark.lesson_id.is_(None))
        return self.db.scalars(stmt).first()


class PlannerBlockRepository(OwnedRepository[PlannerBlock]):
    model = PlannerBlock
    resource_name = "Planned session"

    def in_range(self, user_id: str, start: date, end: date):
        return self.db.scalars(
            select(PlannerBlock)
            .where(PlannerBlock.user_id == user_id, PlannerBlock.study_date >= start, PlannerBlock.study_date <= end)
            .order_by(PlannerBlock.study_date, PlannerBlock.start_time)
        ).all()

    def has_overlap(self, user_id: str, day: date, start: time, end: time) -> bool:
        return self.db.scalars(
            select(PlannerBlock.id).where(
                PlannerBlock.user_id == user_id,
                PlannerBlock.study_date == day,
                PlannerBlock.start_time < end,
                PlannerBlock.end_time > start,
            )
        ).first() is not None
