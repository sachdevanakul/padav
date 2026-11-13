"""PIA administration: consent, sessions, independently timed subtests, append-only responses, raw scoring.

Everything that decides *validity* of an answer (timer, ownership, key membership) happens here, on the
server. The client only ever receives item content, never keys, and the final report is explicitly
``experimental``: no IQ-style score exists until norms do (blueprint section 8, stage 5).
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import median

from app.core.clock import utcnow
from app.core.config import settings
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError, PermissionDeniedError
from app.models.pia import PiaConsent, PiaEvent, PiaResponse, PiaScoreReport, PiaSession, PiaStimulusView, PiaSubtestRun
from app.models.user import User
from app.repositories import (
    PiaConsentRepository, PiaEventRepository, PiaFormRepository, PiaReportRepository,
    PiaResponseRepository, PiaSessionRepository, PiaStimulusRepository,
)
from app.schemas.pia import (
    AnswerIn, AnswerOut, BlueprintOut, ConsentIn, EventIn, ItemOption, PiaItemPublic, ReportOut, RunOut,
    SessionCreate, SessionOut, StimulusOut,
)
from app.services.base import BaseService
from app.services.pia_blueprint import (
    CONSENT_VERSION, SCORING_MODEL_VERSION, SUBTEST_BY_DOMAIN, SUBTESTS, TOTAL_MINUTES, TOTAL_QUESTIONS,
    blueprint_summary,
)

ANSWER_GRACE = timedelta(seconds=2)  # network latency allowance on the final answer of a subtest
FINISHED = ("completed", "timed_out")

NOTICES = (
    "Experimental research result. This is not a validated or standardized IQ score.",
    "Raw accuracy is the share of items answered correctly. It is not an IQ score and must not be converted into one.",
    "Domain results are descriptive only; individual domain scores are not interpreted until their reliability is established.",
    "Do not use this result for admissions, hiring, diagnosis or any other consequential decision.",
)


@dataclass(frozen=True)
class ScoredItem:
    item_id: str
    domain: str
    answer_key: str


class RawScorer:
    """Stage 1 of the scoring methodology: correct = 1, incorrect/omitted = 0. Pure and reproducible."""

    @staticmethod
    def score(items: list[ScoredItem], responses: dict[str, PiaResponse], runs: dict[str, PiaSubtestRun]) -> dict:
        domains = []
        for subtest in SUBTESTS:
            mine = [i for i in items if i.domain == subtest.domain]
            correct = omitted = 0
            times: list[int] = []
            for item in mine:
                response = responses.get(item.item_id)
                if response is None or response.selected_key is None:
                    omitted += 1
                    continue
                correct += int(response.selected_key == item.answer_key)
                if response.client_response_ms is not None:
                    times.append(response.client_response_ms)
            run = runs.get(subtest.domain)
            domains.append({
                "domain": subtest.domain, "label": subtest.label, "questions": len(mine),
                "correct": correct, "omitted": omitted,
                "accuracy": round(correct / len(mine), 4) if mine else 0.0,
                "median_response_ms": int(median(times)) if times else None,
                "timed_out": bool(run and run.status == "timed_out"),
                "interrupted": bool(run and run.interrupted),
            })
        total_correct = sum(d["correct"] for d in domains)
        total = sum(d["questions"] for d in domains)
        return {
            "total_questions": total, "total_correct": total_correct,
            "total_omitted": sum(d["omitted"] for d in domains),
            "raw_accuracy": round(total_correct / total, 4) if total else 0.0,
            "domains": domains,
        }


class PiaService(BaseService):
    def __init__(self, db, scorer: RawScorer | None = None) -> None:
        super().__init__(db)
        self.forms = PiaFormRepository(db)
        self.consents = PiaConsentRepository(db)
        self.sessions = PiaSessionRepository(db)
        self.responses = PiaResponseRepository(db)
        self.events = PiaEventRepository(db)
        self.stimuli = PiaStimulusRepository(db)
        self.reports = PiaReportRepository(db)
        self.scorer = scorer or RawScorer()

    # -- public information -----------------------------------------------------------------------
    def blueprint(self) -> BlueprintOut:
        return BlueprintOut(**blueprint_summary(), consent_version=CONSENT_VERSION)

    # -- consent + session --------------------------------------------------------------------------
    def record_consent(self, user: User, data: ConsentIn) -> PiaConsent:
        consent = self.consents.add(PiaConsent(
            user_id=user.id, consent_version=CONSENT_VERSION, age_at_consent=data.age,
            guardian_consent=data.guardian_consent,
        ))
        self.commit()
        return consent

    def start_session(self, user: User, data: SessionCreate) -> SessionOut:
        existing = self.sessions.in_progress_for(user.id)
        if existing is not None:  # resume rather than create a parallel attempt
            return self._session_out(self._settle_session(existing))
        consent = self.consents.latest_for(user.id, CONSENT_VERSION)
        if consent is None:
            raise PermissionDeniedError("Consent is required before starting the assessment")
        form = self.forms.active()
        if form is None:
            raise ConflictError("The assessment is not available yet")
        session = self.sessions.add(PiaSession(user_id=user.id, form_id=form.id, consent_id=consent.id, language=data.language))
        self.db.flush()  # assigns session.id for the audit event below
        for index, subtest in enumerate(SUBTESTS, start=1):
            session.runs.append(PiaSubtestRun(domain=subtest.domain, sequence=index, time_limit_seconds=subtest.seconds))
        self.events.add(PiaEvent(session_id=session.id, event_type="session_started", payload={"form": f"{form.code}@{form.version}"}))
        self.commit()
        return self._session_out(session)

    def get_session(self, user: User, session_id: str) -> SessionOut:
        return self._session_out(self._settle_session(self.sessions.require_owned(session_id, user.id)))

    # -- subtests -----------------------------------------------------------------------------------------
    def start_subtest(self, user: User, session_id: str, domain: str) -> list[PiaItemPublic]:
        session = self._settle_session(self.sessions.require_owned(session_id, user.id))
        self._require_open(session)
        run = self._run(session, domain)
        if run.status != "pending":
            raise ConflictError("This subtest has already been started")
        if any(r.status == "in_progress" for r in session.runs):
            raise ConflictError("Finish the current subtest first")
        if any(r.sequence < run.sequence and r.status not in FINISHED for r in session.runs):
            raise ConflictError("Subtests must be taken in order")
        now = utcnow()
        run.status, run.started_at = "in_progress", now
        run.deadline_at = now + timedelta(seconds=run.time_limit_seconds)
        self.events.add(PiaEvent(session_id=session.id, run_id=run.id, event_type="subtest_started"))
        self.commit()
        return self._items(session, run)

    def items(self, user: User, session_id: str, domain: str) -> list[PiaItemPublic]:
        session = self._settle_session(self.sessions.require_owned(session_id, user.id))
        run = self._run(session, domain)
        if run.status != "in_progress":
            raise ConflictError("This subtest is not in progress")
        return self._items(session, run)

    def answer(self, user: User, session_id: str, domain: str, data: AnswerIn) -> AnswerOut:
        session = self.sessions.require_owned(session_id, user.id)
        run = self._run(session, domain)
        now = utcnow()
        if run.status != "in_progress" or now > run.deadline_at + ANSWER_GRACE:
            self._settle_session(session)
            raise ConflictError("Time is up for this subtest" if run.status == "timed_out" else "This subtest is not in progress")
        entry = next((e for e in self.forms.form_items(session.form_id, domain) if e.item.item_code == data.item_code), None)
        if entry is None:
            raise NotFoundError.for_resource("Item")
        if entry.item.stimulus_display_seconds and entry.item_id not in self.stimuli.seen_item_ids(session.id):
            raise ConflictError("View the question material before answering")
        if data.selected_key is not None:
            translation = entry.item.translation("en")
            if data.selected_key not in {o["key"] for o in translation.options}:
                raise BadRequestError("Unknown answer option")
        self.responses.add(PiaResponse(
            session_id=session.id, run_id=run.id, item_id=entry.item_id, selected_key=data.selected_key,
            server_elapsed_ms=int((now - run.started_at).total_seconds() * 1000),
            client_response_ms=data.client_response_ms,
        ))
        self.commit()
        return AnswerOut(seconds_remaining=self._remaining(run, now))

    def release_stimulus(self, user: User, session_id: str, domain: str, item_code: str) -> StimulusOut:
        """Returns a timed stimulus exactly once; the unique row is the 'no replay' rule."""
        session = self._settle_session(self.sessions.require_owned(session_id, user.id))
        run = self._run(session, domain)
        if run.status != "in_progress":
            raise ConflictError("This subtest is not in progress")
        entry = next((e for e in self.forms.form_items(session.form_id, domain) if e.item.item_code == item_code), None)
        if entry is None or not entry.item.stimulus_display_seconds:
            raise NotFoundError.for_resource("Stimulus")
        if entry.item_id in self.stimuli.seen_item_ids(session.id):
            raise ConflictError("This material has already been shown")
        translation = entry.item.translation(session.language)
        self.stimuli.add(PiaStimulusView(session_id=session.id, item_id=entry.item_id))
        self.events.add(PiaEvent(session_id=session.id, run_id=run.id, event_type="encoding_start",
                                 payload={"item_code": item_code, "seconds": entry.item.stimulus_display_seconds}))
        self.commit()
        return StimulusOut(item_code=item_code, stimulus=translation.stimulus or "", display_seconds=entry.item.stimulus_display_seconds)

    def record_event(self, user: User, session_id: str, domain: str, data: EventIn) -> None:
        session = self._settle_session(self.sessions.require_owned(session_id, user.id))
        run = self._run(session, domain)
        if run.status != "in_progress":
            raise ConflictError("This subtest is not in progress")
        if data.event_type == "interruption":
            run.interrupted = True  # the timer keeps running; the flag lets analysts apply the exclusion policy
        self.events.add(PiaEvent(session_id=session.id, run_id=run.id, event_type=data.event_type, payload=data.payload))
        self.commit()

    def complete_subtest(self, user: User, session_id: str, domain: str) -> SessionOut:
        session = self._settle_session(self.sessions.require_owned(session_id, user.id))
        run = self._run(session, domain)
        if run.status == "in_progress":
            run.status, run.ended_at = "completed", utcnow()
            self.events.add(PiaEvent(session_id=session.id, run_id=run.id, event_type="subtest_completed"))
            self.commit()
        elif run.status == "pending":
            raise ConflictError("This subtest has not been started")
        return self._session_out(session)

    # -- finish + report --------------------------------------------------------------------------------------
    def finish(self, user: User, session_id: str) -> ReportOut:
        session = self._settle_session(self.sessions.require_owned(session_id, user.id))
        report = self.reports.for_session(session.id)
        if report is not None:
            return self._report_out(report)
        if any(r.status not in FINISHED for r in session.runs):
            raise ConflictError("Complete all subtests before finishing")
        entries = self.forms.form_items(session.form_id)
        scored = [ScoredItem(e.item_id, e.domain, e.item.answer_key) for e in entries]
        payload = self.scorer.score(scored, self.responses.latest_per_item(session.id), {r.domain: r for r in session.runs})
        payload["notices"] = list(NOTICES)
        report = self.reports.add(PiaScoreReport(
            session_id=session.id, form_code=session.form.code, form_version=session.form.version,
            scoring_model_version=SCORING_MODEL_VERSION, norm_version=None, payload=payload,
        ))
        session.status, session.completed_at = "completed", utcnow()
        self.events.add(PiaEvent(session_id=session.id, event_type="session_completed"))
        self.commit()
        return self._report_out(report)

    def get_report(self, user: User, session_id: str) -> ReportOut:
        session = self.sessions.require_owned(session_id, user.id)
        report = self.reports.for_session(session.id)
        if report is None:
            raise NotFoundError.for_resource("Report")
        return self._report_out(report)

    # -- internals ----------------------------------------------------------------------------------------------
    @staticmethod
    def _require_open(session: PiaSession) -> None:
        if session.status != "in_progress":
            raise ConflictError("This assessment session is already complete")

    @staticmethod
    def _run(session: PiaSession, domain: str) -> PiaSubtestRun:
        run = next((r for r in session.runs if r.domain == domain), None)
        if run is None:
            raise NotFoundError.for_resource("Subtest")
        return run

    @staticmethod
    def _remaining(run: PiaSubtestRun, now: datetime) -> int:
        return max(0, int((run.deadline_at - now).total_seconds()))

    def _settle_session(self, session: PiaSession) -> PiaSession:
        """Expire any subtest whose server deadline has passed (the client clock is never trusted)."""
        now, changed = utcnow(), False
        for run in session.runs:
            if run.status == "in_progress" and now > run.deadline_at:
                run.status, run.ended_at, changed = "timed_out", run.deadline_at, True
                self.events.add(PiaEvent(session_id=session.id, run_id=run.id, event_type="subtest_timed_out"))
        if changed:
            self.commit()
        return session

    def _items(self, session: PiaSession, run: PiaSubtestRun) -> list[PiaItemPublic]:
        latest = self.responses.latest_per_item(session.id)
        saved = {item_id: response.selected_key for item_id, response in latest.items()}
        seen = self.stimuli.seen_item_ids(session.id)
        out = []
        for entry in self.forms.form_items(session.form_id, run.domain):
            translation = entry.item.translation(session.language)
            out.append(PiaItemPublic(
                item_code=entry.item.item_code, position=entry.position, stem=translation.stem,
                options=[ItemOption(key=o["key"], text=o["text"]) for o in translation.options],
                stimulus_type=entry.item.stimulus_type, asset_id=entry.item.asset_id,
                asset_data_uri=self._asset_uri(entry.item.asset_id),
                stimulus=None if entry.item.stimulus_display_seconds else translation.stimulus,
                stimulus_display_seconds=entry.item.stimulus_display_seconds,
                stimulus_seen=entry.item_id in seen,
                selected_key=saved.get(entry.item_id),
            ))
        return out

    @staticmethod
    def _asset_uri(asset_id: str | None) -> str | None:
        if not asset_id:
            return None
        path = settings.pia_asset_dir / f"{asset_id}.svg"
        if not path.is_file():
            return None
        return "data:image/svg+xml;base64," + base64.b64encode(path.read_bytes()).decode("ascii")

    def _session_out(self, session: PiaSession) -> SessionOut:
        now = utcnow()
        runs = []
        for run in session.runs:
            subtest = SUBTEST_BY_DOMAIN[run.domain]
            runs.append(RunOut(
                domain=run.domain, label=subtest.label, description=subtest.construct, sequence=run.sequence,
                status=run.status, question_count=subtest.questions, time_limit_seconds=run.time_limit_seconds,
                seconds_remaining=self._remaining(run, now) if run.status == "in_progress" else None,
            ))
        return SessionOut(
            id=session.id, status=session.status, language=session.language, created_at=session.created_at,
            completed_at=session.completed_at, total_questions=TOTAL_QUESTIONS, total_minutes=TOTAL_MINUTES, runs=runs,
        )

    @staticmethod
    def _report_out(report: PiaScoreReport) -> ReportOut:
        return ReportOut(
            session_id=report.session_id, form_code=report.form_code, form_version=report.form_version,
            scoring_model_version=report.scoring_model_version, norm_version=report.norm_version,
            created_at=report.created_at, **report.payload,
        )
