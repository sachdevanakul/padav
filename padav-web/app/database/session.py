from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_and_tables():
    # Import all models to ensure relationships are resolved
    from app.models import (
        user,
        user_profile,
        exam,
        user_exam,
        subject,
        course,
        chapter,
        lesson,
        question,
        question_option,
        test,
        test_section,
        test_attempt,
        test_answer,
        bookmark,
        study_session,
        achievement,
        notification,
        planner_block,
        refresh_token,
    )
    Base.metadata.create_all(bind=engine)
