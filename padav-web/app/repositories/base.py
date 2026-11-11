"""Generic data-access base classes.

Every query that used to be copy-pasted in the routers
(``db.query(X).filter(X.id == id, X.user_id == user.id).first()`` + 404) lives here once.
Ownership scoping in ``OwnedRepository`` is what prevents cross-user access (IDOR).
"""
from __future__ import annotations

from typing import ClassVar, Generic, Sequence, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    model: ClassVar[type]
    resource_name: ClassVar[str] = "Resource"

    def __init__(self, db: Session) -> None:
        self.db = db

    # -- reads ---------------------------------------------------------------
    def get(self, entity_id: str) -> ModelT | None:
        return self.db.get(self.model, entity_id)

    def require(self, entity_id: str) -> ModelT:
        entity = self.get(entity_id)
        if entity is None:
            raise NotFoundError.for_resource(self.resource_name)
        return entity

    def list_all(self) -> Sequence[ModelT]:
        return self.db.scalars(select(self.model)).all()

    # -- writes (the caller / service owns the transaction) -----------------
    def add(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        return entity

    def delete(self, entity: ModelT) -> None:
        self.db.delete(entity)

    def flush(self) -> None:
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, entity: ModelT) -> ModelT:
        self.db.refresh(entity)
        return entity


class ActiveMixin:
    """For models with an ``is_active`` flag: inactive rows are invisible to callers."""

    def get_active(self: "BaseRepository", entity_id: str):  # type: ignore[misc]
        entity = self.get(entity_id)
        if entity is None or not entity.is_active:
            return None
        return entity

    def require_active(self: "BaseRepository", entity_id: str):  # type: ignore[misc]
        entity = self.get_active(entity_id)  # type: ignore[attr-defined]
        if entity is None:
            raise NotFoundError.for_resource(self.resource_name)
        return entity

    def list_active(self: "BaseRepository"):  # type: ignore[misc]
        return self.db.scalars(select(self.model).where(self.model.is_active.is_(True))).all()


class OwnedRepository(BaseRepository[ModelT]):
    """Repository for rows that belong to a user; every lookup is scoped by ``user_id``."""

    def get_owned(self, entity_id: str, user_id: str) -> ModelT | None:
        return self.db.scalars(
            select(self.model).where(self.model.id == entity_id, self.model.user_id == user_id)
        ).first()

    def require_owned(self, entity_id: str, user_id: str) -> ModelT:
        entity = self.get_owned(entity_id, user_id)
        if entity is None:
            # Same response whether the row is missing or belongs to someone else.
            raise NotFoundError.for_resource(self.resource_name)
        return entity

    def list_for_user(self, user_id: str) -> Sequence[ModelT]:
        return self.db.scalars(select(self.model).where(self.model.user_id == user_id)).all()
