from sqlalchemy.orm import Session


class BaseService:
    """Services own the unit of work: they call ``commit`` once per use case."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def commit(self) -> None:
        self.db.commit()
