import uuid
from datetime import datetime, timedelta

from app.models.chapter import Chapter
from app.models.course import Course
from app.models.exam import Exam
from app.models.lesson import Lesson
from app.models.question import Question
from app.models.question_option import QuestionOption
from app.models.subject import Subject
from app.models.test import Test
from app.models.test_attempt import TestAttempt

API = "/api/v1"


def seed_assessment(db, *, questions=2, duration=30):
    exam = Exam(name="E", code=f"e-{uuid.uuid4().hex[:6]}", category="SSC")
    db.add(exam)
    db.flush()
    test = Test(exam_id=exam.id, title="T", total_questions=questions, total_marks=questions, duration_minutes=duration)
    db.add(test)
    db.flush()
    qs = []
    for i in range(questions):
        q = Question(subject_id="sub-1", text=f"Q{i}", correct_option_key="a", marks=1.0, negative_marks=0.25)
        db.add(q)
        db.flush()
        for key in "abcd":
            db.add(QuestionOption(question_id=q.id, key=key, text=key, is_correct=key == "a"))
        qs.append(q)
    db.commit()
    return exam, test, qs


def start(client, headers, test):
    r = client.post(f"{API}/tests/{test.id}/start", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["attempt_id"]


def answer(client, headers, attempt_id, question, key):
    return client.put(f"{API}/tests/attempts/{attempt_id}/answers", headers=headers,
                      json={"question_id": question.id, "selected_option_key": key})


def test_full_attempt_scoring(client, db, user):
    _, test, (q1, q2) = seed_assessment(db)
    attempt = start(client, user["headers"], test)
    assert answer(client, user["headers"], attempt, q1, "a").status_code == 200   # correct
    assert answer(client, user["headers"], attempt, q2, "b").status_code == 200   # wrong
    assert answer(client, user["headers"], attempt, q2, None).status_code == 200  # cleared => no penalty

    # Correctness must not leak while the attempt is open.
    mid = client.get(f"{API}/tests/attempts/{attempt}", headers=user["headers"]).json()
    assert all(a["is_correct"] is None and a["marks_obtained"] is None for a in mid["answers"])

    result = client.post(f"{API}/tests/attempts/{attempt}/submit", headers=user["headers"]).json()
    assert result["score_obtained"] == 1.0 and result["correct"] == 1
    assert result["incorrect"] == 0 and result["unanswered"] == 1 and result["accuracy"] == 100.0

    done = client.get(f"{API}/tests/attempts/{attempt}", headers=user["headers"]).json()
    assert any(a["is_correct"] is True for a in done["answers"])
    assert client.post(f"{API}/tests/attempts/{attempt}/submit", headers=user["headers"]).status_code == 400
    assert answer(client, user["headers"], attempt, q1, "a").status_code == 400  # closed


def test_attempts_listing_route_not_shadowed(client, user):
    r = client.get(f"{API}/tests/attempts", headers=user["headers"])
    assert r.status_code == 200 and r.json() == []


def test_answer_validation(client, db, user):
    _, test, (q1, _q2) = seed_assessment(db)
    attempt = start(client, user["headers"], test)
    assert answer(client, user["headers"], attempt, q1, "z").status_code == 400
    assert client.put(f"{API}/tests/attempts/{attempt}/answers", headers=user["headers"],
                      json={"question_id": "missing", "selected_option_key": "a"}).status_code == 404
    inactive = Question(subject_id="sub-1", text="x", correct_option_key="a", is_active=False)
    db.add(inactive)
    db.commit()
    assert answer(client, user["headers"], attempt, inactive, "a").status_code == 404


def test_answers_limited_to_question_count(client, db, user):
    _, test, qs = seed_assessment(db, questions=1)
    extra = Question(subject_id="sub-1", text="extra", correct_option_key="a")
    db.add(extra)
    db.flush()
    db.add(QuestionOption(question_id=extra.id, key="a", text="a"))
    db.commit()
    attempt = start(client, user["headers"], test)
    assert answer(client, user["headers"], attempt, qs[0], "a").status_code == 200
    assert answer(client, user["headers"], attempt, extra, "a").status_code == 400


def test_section_subjects_restrict_questions(client, db, user):
    from app.models.test_section import TestSection
    _, test, (q1, _q) = seed_assessment(db)
    db.add(TestSection(test_id=test.id, name="S", subject_id="another-subject"))
    db.commit()
    attempt = start(client, user["headers"], test)
    assert answer(client, user["headers"], attempt, q1, "a").status_code == 400


def test_time_limit_enforced(client, db, user):
    _, test, (q1, _q) = seed_assessment(db, duration=10)
    attempt = start(client, user["headers"], test)
    db.query(TestAttempt).update({"started_at": datetime.utcnow() - timedelta(minutes=12)})
    db.commit()
    assert answer(client, user["headers"], attempt, q1, "a").status_code == 409
    assert client.post(f"{API}/tests/attempts/{attempt}/submit", headers=user["headers"]).status_code == 200


def test_inactive_test_cannot_be_started(client, db, user):
    _, test, _ = seed_assessment(db)
    test.is_active = False
    db.commit()
    assert client.post(f"{API}/tests/{test.id}/start", headers=user["headers"]).status_code == 404


def test_attempts_are_private(client, db, user, other_user):
    _, test, (q1, _q) = seed_assessment(db)
    attempt = start(client, user["headers"], test)
    h = other_user["headers"]
    assert client.get(f"{API}/tests/attempts/{attempt}", headers=h).status_code == 404
    assert answer(client, h, attempt, q1, "a").status_code == 404
    assert client.post(f"{API}/tests/attempts/{attempt}/submit", headers=h).status_code == 404
    assert client.get(f"{API}/tests/attempts", headers=h).json() == []


def test_planner_isolation_and_rules(client, user, other_user):
    body = {"title": "Maths", "study_date": "2026-11-12", "start_time": "09:00:00", "end_time": "10:00:00"}
    created = client.post(f"{API}/planner", headers=user["headers"], json=body)
    assert created.status_code == 201
    block_id = created.json()["id"]
    assert client.post(f"{API}/planner", headers=user["headers"], json=body).status_code == 409
    assert client.post(f"{API}/planner", headers=other_user["headers"], json=body).status_code == 201  # other user's slot is free
    for method, kwargs in (("patch", {"json": {"completed": True}}), ("delete", {})):
        assert getattr(client, method)(f"{API}/planner/{block_id}", headers=other_user["headers"], **kwargs).status_code == 404
    assert client.patch(f"{API}/planner/{block_id}", headers=user["headers"], json={"completed": True, "title": "x"}).status_code == 422
    assert client.get(f"{API}/planner?start_date=2026-01-01&end_date=2026-12-31", headers=user["headers"]).status_code == 400


def test_bookmarks(client, db, user, other_user):
    _, _, (q1, _q) = seed_assessment(db)
    h = user["headers"]
    assert client.post(f"{API}/bookmarks/", headers=h, json={}).status_code == 422
    assert client.post(f"{API}/bookmarks/", headers=h, json={"question_id": q1.id, "lesson_id": "x"}).status_code == 422
    assert client.post(f"{API}/bookmarks/", headers=h, json={"question_id": "does-not-exist"}).status_code == 404
    created = client.post(f"{API}/bookmarks/", headers=h, json={"question_id": q1.id})
    assert created.status_code == 200
    assert client.post(f"{API}/bookmarks/", headers=h, json={"question_id": q1.id}).status_code == 409
    assert client.delete(f"{API}/bookmarks/{created.json()['id']}", headers=other_user["headers"]).status_code == 404
    assert client.get(f"{API}/bookmarks/", headers=other_user["headers"]).json() == []
    assert client.delete(f"{API}/bookmarks/{created.json()['id']}", headers=h).status_code == 200


def test_course_outline_and_locked_lessons(client, db, user):
    exam = Exam(name="E", code="e1", category="SSC")
    db.add(exam)
    db.flush()
    subject = Subject(exam_id=exam.id, name="S")
    db.add(subject)
    db.flush()
    course = Course(subject_id=subject.id, title="C")
    db.add(course)
    db.flush()
    chapter = Chapter(course_id=course.id, subject_id=subject.id, title="Ch")
    db.add(chapter)
    db.flush()
    free = Lesson(chapter_id=chapter.id, title="free", content="SECRET-FREE", is_free=True)
    locked = Lesson(chapter_id=chapter.id, title="locked", content="SECRET-LOCKED", video_url="https://v", is_free=False)
    hidden = Lesson(chapter_id=chapter.id, title="hidden", is_active=False)
    db.add_all([free, locked, hidden])
    db.commit()

    outline = client.get(f"{API}/courses/{course.id}/chapters")
    assert outline.status_code == 200
    titles = [lesson["title"] for lesson in outline.json()[0]["lessons"]]
    assert sorted(titles) == ["free", "locked"]            # inactive lesson hidden
    assert "SECRET" not in outline.text and "https://v" not in outline.text  # bodies not in outline

    assert client.get(f"{API}/lessons/{free.id}").status_code == 200
    assert client.get(f"{API}/lessons/{locked.id}").status_code == 401
    assert client.get(f"{API}/lessons/{locked.id}", headers=user["headers"]).status_code == 200
    assert client.get(f"{API}/lessons/{locked.id}", headers={"Authorization": "Bearer junk"}).status_code == 401
    assert client.get(f"{API}/lessons/{hidden.id}").status_code == 404
    assert client.get(f"{API}/courses/nope/chapters").status_code == 404
