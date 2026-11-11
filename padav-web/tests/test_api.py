def register(client, email="learner@example.com"):
    response = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "A-secure-pass-123",
        "full_name": "Padav Learner",
    })
    assert response.status_code == 200
    return response.json()


def test_health_and_seeded_exam_catalog(api_client):
    health = api_client.get("/health")
    exams = api_client.get("/api/v1/exams")
    courses = api_client.get("/api/v1/courses")

    assert health.json() == {"status": "ok", "service": "Padav"}
    assert health.status_code == 200
    assert exams.status_code == 200
    assert {exam["code"] for exam in exams.json()} >= {"ssc-cgl", "upsc-cse", "bank-po"}
    assert courses.status_code == 200
    assert len(courses.json()) >= 6


def test_register_login_and_authenticated_profile(api_client):
    tokens = register(api_client)
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    login = api_client.post("/api/v1/auth/login", json={
        "email": "learner@example.com",
        "password": "A-secure-pass-123",
    })
    assert login.status_code == 200

    profile = api_client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    assert profile.status_code == 200
    assert profile.json()["email"] == "learner@example.com"
    assert "hashed_password" not in profile.json()


def test_exam_preferences_persist_and_reject_duplicates(api_client):
    tokens = register(api_client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    exam = next(item for item in api_client.get("/api/v1/exams").json() if item["code"] == "ssc-cgl")

    added = api_client.post("/api/v1/users/me/exams", headers=headers, json={"exam_id": exam["id"], "is_primary": True})
    duplicate = api_client.post("/api/v1/users/me/exams", headers=headers, json={"exam_id": exam["id"], "is_primary": True})
    saved = api_client.get("/api/v1/users/me/exams", headers=headers)

    assert added.status_code == 200
    assert duplicate.status_code == 400
    assert len(saved.json()) == 1


def test_refresh_requires_a_refresh_token(api_client):
    tokens = register(api_client)
    refreshed = api_client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    rejected = api_client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]})
    replayed = api_client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert refreshed.status_code == 200
    assert rejected.status_code == 401
    assert replayed.status_code == 401
