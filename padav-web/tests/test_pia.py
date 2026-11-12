from datetime import timedelta

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.core.clock import utcnow
from app.core.exceptions import BadRequestError
from app.models.pia import PiaEvent, PiaResponse, PiaSubtestRun
from app.schemas.pia import ContentItem, PiaContentFile
from app.services.pia_blueprint import (
    DIFFICULTY_TARGET, DOMAINS, POOL_TARGET, SUBTESTS, TOTAL_QUESTIONS, validate_form_shape,
)
from app.services.pia_content import PiaContentImporter

ADULT = {"accepted": True, "age": 25}


def _difficulties():
    pool = [d for d, n in DIFFICULTY_TARGET.items() for _ in range(n)]
    return iter(pool)


def build_content(*, status="operational", hindi=True, form=True, drop_one=False):
    """A structurally valid 50-item form: right domain counts and difficulty mix. Content is dummy."""
    difficulties = _difficulties()
    items, codes = [], []
    for subtest in SUBTESTS:
        for n in range(1, subtest.questions + 1):
            code = f"PIA-{subtest.domain.upper()}-TT-{n:03d}"
            translations = {"en": {"stem": f"{subtest.domain} question {n}", "options": [{"key": k, "text": f"opt {k}"} for k in "abcd"]}}
            if hindi:
                translations["hi"] = {"stem": f"{subtest.domain} प्रश्न {n}", "options": [{"key": k, "text": f"विकल्प {k}"} for k in "abcd"]}
            items.append({
                "item_code": code, "domain": subtest.domain, "subdomain": "test", "item_format": "mcq",
                "difficulty": next(difficulties), "answer_key": "b", "status": status, "translations": translations,
            })
            codes.append(code)
    if drop_one:
        items.pop()
        codes.pop()
    content = {"items": items}
    if form:
        content["form"] = {"code": "PIA-MASTER", "name": "Master form", "status": "pilot", "items": codes}
    return PiaContentFile.model_validate(content)


@pytest.fixture
def pia_form(db):
    PiaContentImporter(db).import_content(build_content(), activate=True)


def consent(client, headers, **over):
    return client.post("/api/v1/pia/consent", json={**ADULT, **over}, headers=headers)


def begin(client, headers, language="en"):
    assert consent(client, headers).status_code == 201
    r = client.post("/api/v1/pia/sessions", json={"language": language}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def base(sid, domain=""):
    return f"/api/v1/pia/sessions/{sid}" + (f"/subtests/{domain}" if domain else "")


def answer(client, headers, sid, domain, code, key):
    return client.put(f"{base(sid, domain)}/answers", json={"item_code": code, "selected_key": key}, headers=headers)


def code(domain, n):
    return f"PIA-{domain.upper()}-TT-{n:03d}"


def expire(db, sid, domain):
    run = db.scalars(select(PiaSubtestRun).where(PiaSubtestRun.session_id == sid, PiaSubtestRun.domain == domain)).one()
    run.deadline_at = utcnow() - timedelta(minutes=5)
    db.commit()


# ---- blueprint --------------------------------------------------------------------------------------
def test_blueprint_constants_match_the_specification():
    assert sum(s.questions for s in SUBTESTS) == TOTAL_QUESTIONS == 50
    assert [s.domain for s in SUBTESTS] == list(DOMAINS) and len(DOMAINS) == 7
    assert sum(POOL_TARGET.values()) == 240
    assert validate_form_shape([("gf", "easy")]) != []


def test_blueprint_endpoint_is_public(client):
    r = client.get("/api/v1/pia/blueprint")
    body = r.json()
    assert r.status_code == 200 and body["total_questions"] == 50 and body["total_minutes"] == 46
    assert body["min_age"] == 13 and len(body["subtests"]) == 7


# ---- consent --------------------------------------------------------------------------------------------
def test_consent_rules(client, user):
    h = user["headers"]
    assert consent(client, h, age=12).status_code == 422
    assert consent(client, h, age=15).status_code == 422  # minor without guardian consent
    assert consent(client, h, age=15, guardian_consent=True).status_code == 201
    assert consent(client, h, accepted=False).status_code == 422
    assert client.post("/api/v1/pia/consent", json=ADULT).status_code == 401


def test_cannot_start_without_consent_or_form(client, user, pia_form, db):
    r = client.post("/api/v1/pia/sessions", json={}, headers=user["headers"])
    assert r.status_code == 403


def test_no_active_form_is_a_clean_conflict(client, user):
    consent(client, user["headers"])
    assert client.post("/api/v1/pia/sessions", json={}, headers=user["headers"]).status_code == 409


# ---- importer --------------------------------------------------------------------------------------------
def test_importer_creates_items_and_form(db):
    report = PiaContentImporter(db).import_content(build_content(), activate=True)
    assert report.items_created == 50 and report.form == "PIA-MASTER@1"
    again = PiaContentImporter(db).import_content(build_content(form=False))
    assert again.items_created == 0 and again.items_skipped == 50


def test_form_with_wrong_shape_cannot_be_activated(db):
    with pytest.raises(BadRequestError, match="exactly 50"):
        PiaContentImporter(db).import_content(build_content(drop_one=True), activate=True)
    db.rollback()
    from app.models.pia import PiaItem
    assert db.scalars(select(PiaItem)).first() is None  # atomic


def test_draft_items_cannot_go_live(db):
    with pytest.raises(BadRequestError, match="draft"):
        PiaContentImporter(db).import_content(build_content(status="draft"), activate=True)


def test_item_validation():
    ok = build_content(form=False).items[0].model_dump()
    with pytest.raises(ValidationError, match="answer_key"):
        ContentItem.model_validate({**ok, "answer_key": "z"})
    with pytest.raises(ValidationError, match="same option keys"):
        hi = {"stem": "x", "options": [{"key": "a", "text": "1"}, {"key": "b", "text": "2"}]}
        ContentItem.model_validate({**ok, "translations": {**ok["translations"], "hi": hi}})
    with pytest.raises(ValidationError):
        ContentItem.model_validate({**ok, "item_code": "bad code"})
    with pytest.raises(ValidationError):
        ContentItem.model_validate({**ok, "min_age": 10})


# ---- session flow -------------------------------------------------------------------------------------------
def test_starting_again_resumes_the_open_session(client, user, pia_form):
    first = begin(client, user["headers"])
    second = client.post("/api/v1/pia/sessions", json={}, headers=user["headers"]).json()
    assert first["id"] == second["id"]
    assert [r["domain"] for r in first["runs"]] == list(DOMAINS)
    assert all(r["status"] == "pending" for r in first["runs"])


def test_items_never_expose_the_answer_key(client, user, pia_form):
    h, sid = user["headers"], begin(client, user["headers"])["id"]
    r = client.post(f"{base(sid, 'gf')}/start", headers=h)
    assert r.status_code == 200 and len(r.json()) == 10
    text = r.text.lower()
    for leaked in ("answer_key", "explanation", "correct", "rationale", "difficulty"):
        assert leaked not in text
    assert [i["position"] for i in r.json()] == list(range(1, 11))


def test_subtests_run_in_order_one_at_a_time(client, user, pia_form):
    h, sid = user["headers"], begin(client, user["headers"])["id"]
    assert client.post(f"{base(sid, 'gc')}/start", headers=h).status_code == 409  # gf not done
    assert client.post(f"{base(sid, 'gf')}/start", headers=h).status_code == 200
    assert client.post(f"{base(sid, 'gf')}/start", headers=h).status_code == 409  # already started
    assert client.post(f"{base(sid, 'gc')}/start", headers=h).status_code == 409  # gf still running
    assert client.post(f"{base(sid, 'gf')}/complete", headers=h).status_code == 200
    assert client.post(f"{base(sid, 'gc')}/start", headers=h).status_code == 200
    assert client.get("/api/v1/pia/sessions/x/subtests/zz/items", headers=h).status_code == 404


def test_answering_and_changing_answers(client, user, pia_form, db):
    h, sid = user["headers"], begin(client, user["headers"])["id"]
    client.post(f"{base(sid, 'gf')}/start", headers=h)
    r = answer(client, h, sid, "gf", code("gf", 1), "a")
    assert r.status_code == 200 and 0 < r.json()["seconds_remaining"] <= 480
    assert answer(client, h, sid, "gf", code("gf", 1), "b").status_code == 200  # change
    assert answer(client, h, sid, "gf", code("gf", 2), None).status_code == 200  # skip
    assert answer(client, h, sid, "gf", code("gf", 1), "zz").status_code == 400
    assert answer(client, h, sid, "gf", "PIA-GF-TT-999", "a").status_code == 404
    assert answer(client, h, sid, "gf", code("gc", 1), "a").status_code == 404  # other subtest's item
    assert client.put(f"{base(sid, 'gf')}/answers", json={"item_code": code("gf", 1), "selected_key": "a", "extra": 1}, headers=h).status_code == 422
    items = client.get(f"{base(sid, 'gf')}/items", headers=h).json()
    assert items[0]["selected_key"] == "b" and items[1]["selected_key"] is None  # resume shows own answers
    assert len(db.scalars(select(PiaResponse)).all()) == 3  # every event kept


def test_answers_require_a_running_subtest(client, user, pia_form):
    h, sid = user["headers"], begin(client, user["headers"])["id"]
    assert answer(client, h, sid, "gf", code("gf", 1), "a").status_code == 409  # not started
    client.post(f"{base(sid, 'gf')}/start", headers=h)
    client.post(f"{base(sid, 'gf')}/complete", headers=h)
    assert answer(client, h, sid, "gf", code("gf", 1), "a").status_code == 409  # already ended


def test_server_enforces_the_timer(client, user, pia_form, db):
    h, sid = user["headers"], begin(client, user["headers"])["id"]
    client.post(f"{base(sid, 'gf')}/start", headers=h)
    expire(db, sid, "gf")
    late = answer(client, h, sid, "gf", code("gf", 1), "b")
    assert late.status_code == 409 and "Time is up" in late.json()["detail"]
    session = client.get(base(sid), headers=h).json()
    assert session["runs"][0]["status"] == "timed_out" and session["runs"][0]["seconds_remaining"] is None
    assert client.get(f"{base(sid, 'gf')}/items", headers=h).status_code == 409
    assert client.post(f"{base(sid, 'gc')}/start", headers=h).status_code == 200  # next subtest is open
    assert any(e.event_type == "subtest_timed_out" for e in db.scalars(select(PiaEvent)))


def test_events_and_interruptions(client, user, pia_form, db):
    h, sid = user["headers"], begin(client, user["headers"])["id"]
    path = f"{base(sid, 'gf')}/events"
    assert client.post(path, json={"event_type": "interruption"}, headers=h).status_code == 409  # not running
    client.post(f"{base(sid, 'gf')}/start", headers=h)
    assert client.post(path, json={"event_type": "interruption", "payload": {"reason": "offline"}}, headers=h).status_code == 204
    assert client.post(path, json={"event_type": "resume"}, headers=h).status_code == 204
    assert client.post(path, json={"event_type": "subtest_completed"}, headers=h).status_code == 422  # server-only event
    assert client.post(path, json={"event_type": "resume", "payload": {"x": "y" * 2000}}, headers=h).status_code == 422
    db.expire_all()
    run = db.scalars(select(PiaSubtestRun).where(PiaSubtestRun.domain == "gf")).one()
    assert run.interrupted is True  # timer is not paused; the flag is for the analysis policy


def test_log_is_append_only(client, user, pia_form, db):
    h, sid = user["headers"], begin(client, user["headers"])["id"]
    client.post(f"{base(sid, 'gf')}/start", headers=h)
    answer(client, h, sid, "gf", code("gf", 1), "b")
    row = db.scalars(select(PiaResponse)).one()
    row.selected_key = "a"
    with pytest.raises(ValueError, match="append-only"):
        db.commit()
    db.rollback()
    db.delete(db.scalars(select(PiaResponse)).one())
    with pytest.raises(ValueError, match="append-only"):
        db.commit()
    db.rollback()
    event = db.scalars(select(PiaEvent)).first()
    event.event_type = "x"
    with pytest.raises(ValueError, match="append-only"):
        db.commit()


# ---- language ----------------------------------------------------------------------------------------------
def test_hindi_session_serves_hindi_text(client, user, pia_form):
    h, sid = user["headers"], begin(client, user["headers"], "hi")["id"]
    items = client.post(f"{base(sid, 'gf')}/start", headers=h).json()
    assert "प्रश्न" in items[0]["stem"] and items[0]["options"][0]["text"].startswith("विकल्प")


def test_missing_hindi_falls_back_to_english(client, user, db):
    PiaContentImporter(db).import_content(build_content(hindi=False), activate=True)
    h, sid = user["headers"], begin(client, user["headers"], "hi")["id"]
    items = client.post(f"{base(sid, 'gf')}/start", headers=h).json()
    assert items[0]["stem"] == "gf question 1"


# ---- scoring + report ------------------------------------------------------------------------------------------
def run_everything(client, h, sid, *, wrong_in=(), skip_in=(), time_out=(), db=None):
    for subtest in SUBTESTS:
        d = subtest.domain
        client.post(f"{base(sid, d)}/start", headers=h)
        if d in time_out:
            expire(db, sid, d)
            continue
        for n in range(1, subtest.questions + 1):
            key = None if d in skip_in else ("a" if d in wrong_in else "b")
            answer(client, h, sid, d, code(d, n), key)
        client.post(f"{base(sid, d)}/complete", headers=h)


def test_cannot_finish_early(client, user, pia_form):
    h, sid = user["headers"], begin(client, user["headers"])["id"]
    assert client.post(f"{base(sid)}/finish", headers=h).status_code == 409
    assert client.get(f"{base(sid)}/report", headers=h).status_code == 404


def test_full_run_produces_an_experimental_report(client, user, pia_form, db):
    h, sid = user["headers"], begin(client, user["headers"])["id"]
    run_everything(client, h, sid, wrong_in=("gv",), skip_in=("gs",), time_out=("glr",), db=db)
    r = client.post(f"{base(sid)}/finish", headers=h)
    assert r.status_code == 200, r.text
    rep = r.json()
    by = {d["domain"]: d for d in rep["domains"]}
    assert rep["status"] == "experimental" and rep["norm_version"] is None
    assert rep["total_questions"] == 50
    assert by["gf"]["correct"] == 10 and by["gf"]["accuracy"] == 1.0
    assert by["gv"]["correct"] == 0 and by["gv"]["omitted"] == 0
    assert by["gs"]["correct"] == 0 and by["gs"]["omitted"] == 7
    assert by["glr"]["timed_out"] is True and by["glr"]["omitted"] == 4
    assert rep["total_correct"] == 10 + 7 + 7 + 7  # gf, gc, gwm, gq; gv wrong, gs skipped, glr timed out
    assert rep["total_correct"] == 31 and rep["raw_accuracy"] == 0.62
    # 76% accuracy must never be turned into an IQ-style number
    for forbidden in ("iq", "percentile", "standard_score", "gifted"):
        assert forbidden not in " ".join(rep.keys()).lower()
    assert any("not a validated" in n for n in rep["notices"])
    assert client.get(f"{base(sid)}/report", headers=h).json() == rep
    assert client.post(f"{base(sid)}/finish", headers=h).json() == rep  # idempotent
    assert client.get(base(sid), headers=h).json()["status"] == "completed"
    assert client.post(f"{base(sid)}/subtests/gf/start", headers=h).status_code == 409


def test_latest_answer_wins_in_scoring(client, user, pia_form, db):
    h, sid = user["headers"], begin(client, user["headers"])["id"]
    client.post(f"{base(sid, 'gf')}/start", headers=h)
    answer(client, h, sid, "gf", code("gf", 1), "b")
    answer(client, h, sid, "gf", code("gf", 1), "a")  # changed to wrong
    client.post(f"{base(sid, 'gf')}/complete", headers=h)
    for subtest in SUBTESTS[1:]:
        client.post(f"{base(sid, subtest.domain)}/start", headers=h)
        client.post(f"{base(sid, subtest.domain)}/complete", headers=h)
    rep = client.post(f"{base(sid)}/finish", headers=h).json()
    assert {d["domain"]: d for d in rep["domains"]}["gf"]["correct"] == 0


def test_new_session_after_completion(client, user, pia_form, db):
    h, sid = user["headers"], begin(client, user["headers"])["id"]
    run_everything(client, h, sid)
    client.post(f"{base(sid)}/finish", headers=h)
    again = client.post("/api/v1/pia/sessions", json={}, headers=h).json()
    assert again["id"] != sid and again["status"] == "in_progress"


# ---- isolation -----------------------------------------------------------------------------------------------------
def test_other_users_cannot_touch_a_session(client, user, other_user, pia_form):
    h, o, sid = user["headers"], other_user["headers"], begin(client, user["headers"])["id"]
    client.post(f"{base(sid, 'gf')}/start", headers=h)
    answer(client, h, sid, "gf", code("gf", 1), "b")
    checks = [
        client.get(base(sid), headers=o),
        client.post(f"{base(sid, 'gf')}/start", headers=o),
        client.get(f"{base(sid, 'gf')}/items", headers=o),
        answer(client, o, sid, "gf", code("gf", 1), "b"),
        client.post(f"{base(sid, 'gf')}/complete", headers=o),
        client.post(f"{base(sid, 'gf')}/events", json={"event_type": "resume"}, headers=o),
        client.post(f"{base(sid)}/finish", headers=o),
        client.get(f"{base(sid)}/report", headers=o),
    ]
    assert [c.status_code for c in checks] == [404] * len(checks)
    assert client.get(base(sid)).status_code == 401
