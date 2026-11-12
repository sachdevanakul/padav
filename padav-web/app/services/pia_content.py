"""Imports PIA items (and optionally a form) from a validated JSON file in one transaction.

Items are versioned: re-importing an existing (item_code, version) is skipped, never overwritten, because
responses may already reference it. Changing an item means publishing a new version.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError
from app.models.pia import PiaForm, PiaFormItem, PiaItem, PiaItemTranslation
from app.repositories import PiaFormRepository, PiaItemRepository
from app.schemas.pia import ContentForm, ContentItem, PiaContentFile
from app.services.base import BaseService
from app.services.pia_blueprint import validate_form_shape


@dataclass
class PiaImportReport:
    items_created: int = 0
    items_skipped: int = 0
    form: str | None = None
    problems: list[str] = field(default_factory=list)


class PiaContentImporter(BaseService):
    def __init__(self, db: Session) -> None:
        super().__init__(db)
        self.items = PiaItemRepository(db)
        self.forms = PiaFormRepository(db)

    def import_file(self, path: Path, *, activate: bool = False) -> PiaImportReport:
        return self.import_content(PiaContentFile.model_validate(json.loads(path.read_text(encoding="utf-8"))), activate=activate)

    def import_content(self, content: PiaContentFile, *, activate: bool = False) -> PiaImportReport:
        report = PiaImportReport()
        for spec in content.items:
            if self.items.get_version(spec.item_code, spec.version):
                report.items_skipped += 1
                continue
            self.items.add(self._build_item(spec))
            report.items_created += 1
        self.db.flush()
        if content.form:
            report.form = self._build_form(content.form, activate)
        self.commit()  # all-or-nothing
        return report

    @staticmethod
    def _build_item(spec: ContentItem) -> PiaItem:
        item = PiaItem(**spec.model_dump(exclude={"translations"}))
        for language, text in spec.translations.items():
            item.translations.append(PiaItemTranslation(
                language=language, stem=text.stem, options=[o.model_dump() for o in text.options],
                explanation=text.explanation, distractor_rationale=text.distractor_rationale, reviewed=text.reviewed,
            ))
        return item

    def _build_form(self, spec: ContentForm, activate: bool) -> str:
        if self.forms.get_version(spec.code, spec.version):
            raise BadRequestError(f"Form {spec.code} v{spec.version} already exists; publish a new version instead")
        chosen = []
        for code in spec.items:
            item = self.items.latest(code)
            if item is None:
                raise BadRequestError(f"Form references unknown item {code}")
            chosen.append(item)
        if len({i.id for i in chosen}) != len(chosen):
            raise BadRequestError("Form lists the same item twice")
        problems = validate_form_shape((i.domain, i.difficulty) for i in chosen)
        if activate and problems:
            raise BadRequestError("Cannot activate: " + "; ".join(problems))
        if activate and any(i.status == "draft" for i in chosen):
            raise BadRequestError("Cannot activate a form that contains draft items")
        form = PiaForm(code=spec.code, version=spec.version, name=spec.name, status=spec.status, is_active=False)
        positions: dict[str, int] = {}
        for item in chosen:
            positions[item.domain] = positions.get(item.domain, 0) + 1
            form.items.append(PiaFormItem(item_id=item.id, domain=item.domain, position=positions[item.domain]))
        self.forms.add(form)
        if activate:
            self.forms.deactivate_all()
            form.is_active = True
        return f"{spec.code}@{spec.version}"
