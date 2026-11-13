"""Padav Intelligence Assessment (PIA) tables.

``PiaResponse`` and ``PiaEvent`` are append-only: the ORM refuses to update or delete them, so the
session record can always reproduce a score exactly.
"""
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.clock import utcnow
from app.database.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class PiaItem(Base):
    __tablename__ = "pia_items"
    __table_args__ = (UniqueConstraint("item_code", "version", name="uq_pia_item_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    item_code: Mapped[str] = mapped_column(String(40), index=True, nullable=False)  # e.g. PIA-GF-MR-001
    version: Mapped[int] = mapped_column(Integer, default=1)
    domain: Mapped[str] = mapped_column(String(8), index=True, nullable=False)
    subdomain: Mapped[str] = mapped_column(String(60), nullable=False)
    item_format: Mapped[str] = mapped_column(String(60), nullable=False)
    stimulus_type: Mapped[str] = mapped_column(String(40), default="text")
    asset_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False)  # authoring hypothesis only
    min_age: Mapped[int] = mapped_column(Integer, default=13)
    scoring_rule: Mapped[str] = mapped_column(String(40), default="binary")
    time_allowance_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Set => the stimulus is withheld from the item list and released once, for this many seconds (e.g. memory tasks).
    stimulus_display_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    answer_key: Mapped[str] = mapped_column(String(20), nullable=False)  # never serialised to clients
    status: Mapped[str] = mapped_column(String(20), default="draft")
    author: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    reviewer: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    accessibility_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    translations: Mapped[list["PiaItemTranslation"]] = relationship(
        "PiaItemTranslation", back_populates="item", cascade="all, delete-orphan"
    )

    def translation(self, language: str) -> "PiaItemTranslation | None":
        by_language = {t.language: t for t in self.translations}
        return by_language.get(language) or by_language.get("en")


class PiaItemTranslation(Base):
    __tablename__ = "pia_item_translations"
    __table_args__ = (UniqueConstraint("item_id", "language", name="uq_pia_item_language"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("pia_items.id", ondelete="CASCADE"), nullable=False)
    language: Mapped[str] = mapped_column(String(5), nullable=False)
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    stimulus: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # material to study/read above the stem
    options: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)  # [{"key": "a", "text": "..."}]
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    distractor_rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)

    item: Mapped[PiaItem] = relationship("PiaItem", back_populates="translations")


class PiaForm(Base):
    __tablename__ = "pia_forms"
    __table_args__ = (UniqueConstraint("code", "version", name="uq_pia_form_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    items: Mapped[list["PiaFormItem"]] = relationship(
        "PiaFormItem", back_populates="form", cascade="all, delete-orphan", order_by="PiaFormItem.position"
    )


class PiaFormItem(Base):
    __tablename__ = "pia_form_items"
    __table_args__ = (
        UniqueConstraint("form_id", "item_id", name="uq_pia_form_item"),
        UniqueConstraint("form_id", "domain", "position", name="uq_pia_form_position"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    form_id: Mapped[str] = mapped_column(String(36), ForeignKey("pia_forms.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("pia_items.id", ondelete="RESTRICT"))
    domain: Mapped[str] = mapped_column(String(8), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)  # order within the subtest

    form: Mapped[PiaForm] = relationship("PiaForm", back_populates="items")
    item: Mapped[PiaItem] = relationship("PiaItem")


class PiaConsent(Base):
    __tablename__ = "pia_consents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    consent_version: Mapped[str] = mapped_column(String(30), nullable=False)
    age_at_consent: Mapped[int] = mapped_column(Integer, nullable=False)
    guardian_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class PiaSession(Base):
    __tablename__ = "pia_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    form_id: Mapped[str] = mapped_column(String(36), ForeignKey("pia_forms.id", ondelete="RESTRICT"))
    consent_id: Mapped[str] = mapped_column(String(36), ForeignKey("pia_consents.id", ondelete="RESTRICT"))
    language: Mapped[str] = mapped_column(String(5), default="en")
    status: Mapped[str] = mapped_column(String(20), default="in_progress")  # in_progress | completed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    form: Mapped[PiaForm] = relationship("PiaForm")
    runs: Mapped[list["PiaSubtestRun"]] = relationship(
        "PiaSubtestRun", back_populates="session", cascade="all, delete-orphan", order_by="PiaSubtestRun.sequence"
    )


class PiaSubtestRun(Base):
    __tablename__ = "pia_subtest_runs"
    __table_args__ = (UniqueConstraint("session_id", "domain", name="uq_pia_run_domain"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("pia_sessions.id", ondelete="CASCADE"), index=True)
    domain: Mapped[str] = mapped_column(String(8), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | in_progress | completed | timed_out
    time_limit_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deadline_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # server-computed, never client-set
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    interrupted: Mapped[bool] = mapped_column(Boolean, default=False)

    session: Mapped[PiaSession] = relationship("PiaSession", back_populates="runs")


class PiaResponse(Base):
    """One row per answer event; the latest row per item is the final answer."""

    __tablename__ = "pia_responses"
    __table_args__ = (Index("ix_pia_response_session_item", "session_id", "item_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("pia_sessions.id", ondelete="CASCADE"), index=True)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("pia_subtest_runs.id", ondelete="CASCADE"))
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("pia_items.id", ondelete="RESTRICT"))
    selected_key: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # None = explicit skip
    server_elapsed_ms: Mapped[int] = mapped_column(Integer, nullable=False)  # since subtest start
    client_response_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # self-reported, advisory
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class PiaEvent(Base):
    __tablename__ = "pia_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("pia_sessions.id", ondelete="CASCADE"), index=True)
    run_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class PiaStimulusView(Base):
    """Records the single release of a timed stimulus; the unique key is what enforces 'no replay'."""

    __tablename__ = "pia_stimulus_views"
    __table_args__ = (UniqueConstraint("session_id", "item_id", name="uq_pia_stimulus_once"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("pia_sessions.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("pia_items.id", ondelete="RESTRICT"))
    shown_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class PiaScoreReport(Base):
    __tablename__ = "pia_score_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("pia_sessions.id", ondelete="CASCADE"), unique=True)
    form_code: Mapped[str] = mapped_column(String(40), nullable=False)
    form_version: Mapped[int] = mapped_column(Integer, nullable=False)
    scoring_model_version: Mapped[str] = mapped_column(String(30), nullable=False)
    norm_version: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # None until norms exist
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


def _immutable(_mapper, _connection, target):
    raise ValueError(f"{type(target).__name__} rows are append-only")


for _model in (PiaResponse, PiaEvent, PiaStimulusView):
    event.listen(_model, "before_update", _immutable)
    event.listen(_model, "before_delete", _immutable)
