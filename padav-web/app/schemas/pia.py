from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.base import ORMModel, StrictInput
from app.services.pia_blueprint import CLIENT_EVENTS, DIFFICULTIES, DOMAINS, ITEM_STATUSES, LANGUAGES, MIN_AGE

Language = Literal["en", "hi"]
ClientEvent = Literal[CLIENT_EVENTS]  # type: ignore[valid-type]


# ---- requests -------------------------------------------------------------------------
class ConsentIn(StrictInput):
    accepted: bool
    age: int = Field(ge=1, le=120)
    guardian_consent: bool = False

    @model_validator(mode="after")
    def _check(self):
        if not self.accepted:
            raise ValueError("Consent must be given to take the assessment")
        if self.age < MIN_AGE:
            raise ValueError(f"The assessment is for people aged {MIN_AGE} and over")
        if self.age < 18 and not self.guardian_consent:
            raise ValueError("Parent or guardian consent is required for participants under 18")
        return self


class SessionCreate(StrictInput):
    language: Language = "en"


class AnswerIn(StrictInput):
    item_code: str = Field(min_length=1, max_length=40)
    selected_key: str | None = Field(default=None, max_length=20)  # null = explicit skip
    client_response_ms: int | None = Field(default=None, ge=0, le=3_600_000)


class EventIn(StrictInput):
    event_type: ClientEvent
    payload: dict | None = None

    @model_validator(mode="after")
    def _small_payload(self):
        if self.payload is not None and len(str(self.payload)) > 1000:
            raise ValueError("Event payload too large")
        return self


# ---- responses (note: nothing here can carry an answer key) ---------------------------------
class ItemOption(BaseModel):
    key: str
    text: str


class PiaItemPublic(BaseModel):
    item_code: str
    position: int
    stem: str
    options: list[ItemOption]
    stimulus_type: str
    asset_id: str | None = None
    selected_key: str | None = None  # the caller's own saved answer, for resume


class RunOut(BaseModel):
    domain: str
    label: str
    description: str
    sequence: int
    status: str
    question_count: int
    time_limit_seconds: int
    seconds_remaining: int | None = None


class SessionOut(BaseModel):
    id: str
    status: str
    language: str
    created_at: datetime
    completed_at: datetime | None = None
    total_questions: int
    total_minutes: int
    runs: list[RunOut]


class ConsentOut(ORMModel):
    id: str
    consent_version: str
    created_at: datetime


class AnswerOut(BaseModel):
    saved: bool = True
    seconds_remaining: int


class DomainScore(BaseModel):
    domain: str
    label: str
    questions: int
    correct: int
    omitted: int
    accuracy: float
    median_response_ms: int | None = None
    timed_out: bool = False
    interrupted: bool = False


class ReportOut(BaseModel):
    session_id: str
    status: Literal["experimental"] = "experimental"
    form_code: str
    form_version: int
    scoring_model_version: str
    norm_version: str | None = None
    total_questions: int
    total_correct: int
    total_omitted: int
    raw_accuracy: float
    domains: list[DomainScore]
    notices: list[str]
    created_at: datetime


class BlueprintOut(BaseModel):
    version: str
    total_questions: int
    total_minutes: int
    min_age: int
    languages: list[str]
    consent_version: str
    subtests: list[dict]


# ---- content import ---------------------------------------------------------------------------
class ContentOption(StrictInput):
    key: str = Field(min_length=1, max_length=20)
    text: str = Field(min_length=1)


class ContentTranslation(StrictInput):
    stem: str = Field(min_length=1)
    options: list[ContentOption] = Field(min_length=2, max_length=8)
    explanation: str | None = None
    distractor_rationale: str | None = None
    reviewed: bool = False

    @model_validator(mode="after")
    def _unique_keys(self):
        keys = [o.key for o in self.options]
        if len(set(keys)) != len(keys):
            raise ValueError("option keys must be unique")
        return self


class ContentItem(StrictInput):
    item_code: str = Field(pattern=r"^PIA-[A-Z]{2,4}-[A-Z]{2,4}-\d{3}$")
    version: int = Field(default=1, ge=1)
    domain: Literal[DOMAINS]  # type: ignore[valid-type]
    subdomain: str = Field(min_length=1, max_length=60)
    item_format: str = Field(min_length=1, max_length=60)
    stimulus_type: str = "text"
    asset_id: str | None = None
    difficulty: Literal[DIFFICULTIES]  # type: ignore[valid-type]
    min_age: int = Field(default=13, ge=13)
    time_allowance_seconds: int | None = Field(default=None, ge=1)
    answer_key: str = Field(min_length=1, max_length=20)
    status: Literal[ITEM_STATUSES] = "draft"  # type: ignore[valid-type]
    author: str | None = None
    reviewer: str | None = None
    accessibility_notes: str | None = None
    translations: dict[Literal[LANGUAGES], ContentTranslation]  # type: ignore[valid-type]

    @model_validator(mode="after")
    def _check(self):
        if "en" not in self.translations:
            raise ValueError("an English version is required")
        for language, text in self.translations.items():
            if self.answer_key not in {o.key for o in text.options}:
                raise ValueError(f"answer_key '{self.answer_key}' is not an option in '{language}'")
        keysets = {frozenset(o.key for o in t.options) for t in self.translations.values()}
        if len(keysets) > 1:
            raise ValueError("English and Hindi must use the same option keys")
        return self


class ContentForm(StrictInput):
    code: str = Field(min_length=1, max_length=40)
    version: int = Field(default=1, ge=1)
    name: str = Field(min_length=1, max_length=120)
    status: Literal["draft", "pilot", "operational"] = "draft"
    items: list[str]  # item codes, in presentation order within each domain


class PiaContentFile(StrictInput):
    items: list[ContentItem]
    form: ContentForm | None = None

    @model_validator(mode="after")
    def _unique(self):
        codes = [(i.item_code, i.version) for i in self.items]
        if len(set(codes)) != len(codes):
            raise ValueError("duplicate item_code/version in file")
        return self
