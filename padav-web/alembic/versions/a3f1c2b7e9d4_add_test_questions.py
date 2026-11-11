"""link tests to questions

Revision ID: a3f1c2b7e9d4
Revises: d81bdb070fda
Create Date: 2026-11-11 12:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a3f1c2b7e9d4"
down_revision: Union[str, None] = "d81bdb070fda"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "test_questions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("test_id", sa.String(length=36), nullable=False),
        sa.Column("question_id", sa.String(length=36), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["test_id"], ["tests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("test_id", "question_id", name="uq_test_question"),
    )
    op.create_index("ix_test_questions_test_id", "test_questions", ["test_id"])
    op.create_index("ix_test_questions_question_id", "test_questions", ["question_id"])


def downgrade() -> None:
    op.drop_index("ix_test_questions_question_id", table_name="test_questions")
    op.drop_index("ix_test_questions_test_id", table_name="test_questions")
    op.drop_table("test_questions")
