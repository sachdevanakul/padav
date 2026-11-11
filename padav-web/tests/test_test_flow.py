from app.models.question import Question
from app.models.subject import Subject
from app.models.test import Test as Assessment


def test_attempt_scores_answers_on_the_backend(api_client):
    exam = api_client.get("/api/v1/exams").json()[0]
    tokens = api_client.post("/api/v1/auth/register", json={
        "email": "test-taker@example.com",
        "password": "A-secure-pass-123",
        "full_name": "Test Taker",
    }).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    from app.main import app

    with app.state.test_session_factory() as db:
        subject = db.query(Subject).filter(Subject.exam_id == exam["id"]).first()
        assessment = Assessment(exam_id=exam["id"], title="Scoring verification", total_questions=1, total_marks=1, marks_per_question=1, negative_marks_per_question=0.25)
        db.add(assessment)
        db.flush()
        question = Question(subject_id=subject.id, text="What is 2 + 2?", correct_option_key="B", marks=1, negative_marks=0.25)
        db.add(question)
        db.commit()
        test_id, question_id = assessment.id, question.id

    started = api_client.post(f"/api/v1/tests/{test_id}/start", headers=headers)
    assert started.status_code == 200
    attempt_id = started.json()["attempt_id"]
    saved = api_client.put(
        f"/api/v1/tests/attempts/{attempt_id}/answers",
        params={"question_id": question_id, "selected_option_key": "B"},
        headers=headers,
    )
    result = api_client.post(f"/api/v1/tests/attempts/{attempt_id}/submit", headers=headers)

    assert saved.status_code == 200
    assert result.status_code == 200
    assert result.json()["score_obtained"] == 1
    assert result.json()["correct"] == 1
    assert result.json()["accuracy"] == 100
