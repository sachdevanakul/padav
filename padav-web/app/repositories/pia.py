from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.pia import (
    PiaConsent, PiaEvent, PiaForm, PiaFormItem, PiaItem, PiaResponse, PiaScoreReport, PiaSession, PiaStimulusView,
)
from app.repositories.base import BaseRepository, OwnedRepository


class PiaItemRepository(BaseRepository[PiaItem]):
    model = PiaItem
    resource_name = "Item"

    def get_version(self, item_code: str, version: int) -> PiaItem | None:
        return self.db.scalars(select(PiaItem).where(PiaItem.item_code == item_code, PiaItem.version == version)).first()

    def latest(self, item_code: str) -> PiaItem | None:
        return self.db.scalars(
            select(PiaItem).where(PiaItem.item_code == item_code).order_by(PiaItem.version.desc())
        ).first()


class PiaFormRepository(BaseRepository[PiaForm]):
    model = PiaForm
    resource_name = "Assessment form"

    def get_version(self, code: str, version: int) -> PiaForm | None:
        return self.db.scalars(select(PiaForm).where(PiaForm.code == code, PiaForm.version == version)).first()

    def active(self) -> PiaForm | None:
        return self.db.scalars(
            select(PiaForm).where(PiaForm.is_active.is_(True)).options(selectinload(PiaForm.items))
        ).first()

    def deactivate_all(self) -> None:
        for form in self.db.scalars(select(PiaForm).where(PiaForm.is_active.is_(True))):
            form.is_active = False

    def form_items(self, form_id: str, domain: str | None = None) -> list[PiaFormItem]:
        query = (
            select(PiaFormItem).where(PiaFormItem.form_id == form_id)
            .options(selectinload(PiaFormItem.item).selectinload(PiaItem.translations))
            .order_by(PiaFormItem.domain, PiaFormItem.position)
        )
        if domain:
            query = query.where(PiaFormItem.domain == domain)
        return list(self.db.scalars(query))


class PiaConsentRepository(OwnedRepository[PiaConsent]):
    model = PiaConsent
    resource_name = "Consent"

    def latest_for(self, user_id: str, version: str) -> PiaConsent | None:
        return self.db.scalars(
            select(PiaConsent).where(PiaConsent.user_id == user_id, PiaConsent.consent_version == version)
            .order_by(PiaConsent.created_at.desc())
        ).first()


class PiaSessionRepository(OwnedRepository[PiaSession]):
    model = PiaSession
    resource_name = "Assessment session"

    def in_progress_for(self, user_id: str) -> PiaSession | None:
        return self.db.scalars(
            select(PiaSession).where(PiaSession.user_id == user_id, PiaSession.status == "in_progress")
            .order_by(PiaSession.created_at.desc())
        ).first()


class PiaResponseRepository(BaseRepository[PiaResponse]):
    model = PiaResponse

    def latest_per_item(self, session_id: str) -> dict[str, PiaResponse]:
        """Final answer per item = the newest row; ties broken by insertion order."""
        rows = self.db.scalars(
            select(PiaResponse).where(PiaResponse.session_id == session_id)
            .order_by(PiaResponse.server_elapsed_ms, PiaResponse.created_at)
        )
        return {row.item_id: row for row in rows}


class PiaEventRepository(BaseRepository[PiaEvent]):
    model = PiaEvent


class PiaStimulusRepository(BaseRepository[PiaStimulusView]):
    model = PiaStimulusView

    def seen_item_ids(self, session_id: str) -> set[str]:
        return set(self.db.scalars(select(PiaStimulusView.item_id).where(PiaStimulusView.session_id == session_id)))


class PiaReportRepository(BaseRepository[PiaScoreReport]):
    model = PiaScoreReport

    def for_session(self, session_id: str) -> PiaScoreReport | None:
        return self.db.scalars(select(PiaScoreReport).where(PiaScoreReport.session_id == session_id)).first()
