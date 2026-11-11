import json
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import select

from app.cli import main as cli_main
from app.models.question import Question
from app.models.test import Test
from app.models.test_question import TestQuestion
from app.services.seed import SAMPLE_CONTENT, seed_development_data

API = "/api/v1"
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def seeded(db):
    seed_development_data(db)
    return db.scalars(select(Test)).one()


def run_attempt(client, headers, test_id):
    r = client.post(f"{API}/tests/{test_id}/start", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["attempt_id"]


def test_seed_is_idempotent_and_complete(db, seeded):
    assert seeded.total_questions == 10 and seeded.total_marks == 20
    assert db.query(TestQuestion).count() == 10
    seed_development_data(db)  # run again
    assert db.query(Test).count() == 1 and db.query(Question).count() == 10


def test_questions_hide_answers_and_follow_order(client, db, user, seeded):
    attempt = run_attempt(client, user["headers"], seeded.id)
    r = client.get(f"{API}/tests/attempts/{attempt}/questions", headers=user["headers"])
    assert r.status_code == 200
    questions = r.json()
    assert len(questions) == 10 and questions[0]["text"] == "What is 15% of 240?"
    flat = json.dumps(questions)
    for leaked in ("correct_option_key", "is_correct", "explanation"):
        assert leaked not in flat
    assert all(len(q["options"]) == 4 for q in questions)


def test_review_only_after_submit_and_matches_key(client, user, seeded):
    h = user["headers"]
    attempt = run_attempt(client, h, seeded.id)
    assert client.get(f"{API}/tests/attempts/{attempt}/review", headers=h).status_code == 400
    questions = client.get(f"{API}/tests/attempts/{attempt}/questions", headers=h).json()
    client.put(f"{API}/tests/attempts/{attempt}/answers", headers=h,
               json={"question_id": questions[0]["id"], "selected_option_key": "b"})  # 36: correct
    client.put(f"{API}/tests/attempts/{attempt}/answers", headers=h,
               json={"question_id": questions[1]["id"], "selected_option_key": "a"})  # wrong
    result = client.post(f"{API}/tests/attempts/{attempt}/submit", headers=h).json()
    assert result["score_obtained"] == 1.5 and result["unanswered"] == 8  # +2 -0.5
    assert client.get(f"{API}/tests/attempts/{attempt}/questions", headers=h).status_code == 400  # closed

    review = client.get(f"{API}/tests/attempts/{attempt}/review", headers=h).json()
    assert len(review) == 10
    assert review[0]["correct_option_key"] == "b" and review[0]["selected_option_key"] == "b"
    assert review[1]["selected_option_key"] == "a" and review[1]["correct_option_key"] == "c"
    assert review[2]["selected_option_key"] is None and review[0]["explanation"]


def test_attempt_questions_and_review_are_private(client, user, other_user, seeded):
    attempt = run_attempt(client, user["headers"], seeded.id)
    h = other_user["headers"]
    assert client.get(f"{API}/tests/attempts/{attempt}/questions", headers=h).status_code == 404
    assert client.get(f"{API}/tests/attempts/{attempt}/review", headers=h).status_code == 404


def test_membership_is_strict(client, db, user, seeded):
    attempt = run_attempt(client, user["headers"], seeded.id)
    stray = Question(subject_id=db.scalars(select(Question.subject_id)).first(), text="stray", correct_option_key="a")
    db.add(stray)
    db.commit()
    from app.models.question_option import QuestionOption
    db.add(QuestionOption(question_id=stray.id, key="a", text="a"))
    db.commit()
    r = client.put(f"{API}/tests/attempts/{attempt}/answers", headers=user["headers"],
                   json={"question_id": stray.id, "selected_option_key": "a"})
    assert r.status_code == 400 and "not part of this test" in r.json()["detail"]


def _write(tmp_path, data):
    path = tmp_path / "c.json"
    path.write_text(json.dumps(data))
    return path


def test_importer_rejects_bad_files_atomically(db, tmp_path, capsys):
    seed_development_data(db)
    good = json.loads(SAMPLE_CONTENT.read_text())
    bad = json.loads(json.dumps(good))
    bad["tests"][0]["title"] = "Another"
    bad["tests"][0]["questions"][0]["correct"] = "e"
    assert cli_main(["import-content", str(_write(tmp_path, bad))]) == 1
    assert db.query(Test).count() == 1  # nothing half-imported

    bad2 = json.loads(json.dumps(good))
    bad2["exam"] = "no-such-exam"
    assert cli_main(["import-content", str(_write(tmp_path, bad2))]) == 1

    ok = json.loads(json.dumps(good))
    ok["tests"][0]["title"] = "Second Test"
    assert cli_main(["import-content", str(_write(tmp_path, ok))]) == 0
    db.expire_all()
    assert db.query(Test).count() == 2


def test_content_not_publicly_served(client):
    # answer keys live in /content, which is never mounted as static files
    assert client.get("/content/ssc-cgl-sample.json").status_code in (404,)


def test_migrations_upgrade_fresh_database(tmp_path):
    env = {"DATABASE_URL": f"sqlite:///{tmp_path/'m.db'}", "ENVIRONMENT": "development", "PATH": "/usr/bin:/bin"}
    out = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT, env=env, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    # Models and migrations must agree for the new table. (Pre-existing FLOAT/Double
    # differences on older columns come from the SQLAlchemy version, not from this change.)
    chk = subprocess.run([sys.executable, "-m", "alembic", "check"], cwd=ROOT, env=env, capture_output=True, text=True)
    assert "test_questions" not in chk.stdout + chk.stderr


def test_attempt_detail_exposes_server_side_timer(client, db, user, seeded):
    h = user["headers"]
    attempt = run_attempt(client, h, seeded.id)
    detail = client.get(f"{API}/tests/attempts/{attempt}", headers=h).json()
    assert detail["test_title"] == "SSC CGL Practice Test 1" and detail["duration_minutes"] == 10
    assert 590 <= detail["seconds_remaining"] <= 600
    listing = client.get(f"{API}/tests/attempts", headers=h).json()
    assert listing[0]["test_title"] == "SSC CGL Practice Test 1"
    client.post(f"{API}/tests/attempts/{attempt}/submit", headers=h)
    assert client.get(f"{API}/tests/attempts/{attempt}", headers=h).json()["seconds_remaining"] is None
