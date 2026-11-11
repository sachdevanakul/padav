from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.models.user import User
from tests.conftest import PASSWORD, auth_headers, register

API = "/api/v1"


def test_register_login_me(client):
    register(client)
    r = client.post(f"{API}/auth/login", json={"email": "USER@example.com", "password": PASSWORD})
    assert r.status_code == 200
    me = client.get(f"{API}/auth/me", headers=auth_headers(r.json()))
    assert me.status_code == 200 and "hashed_password" not in me.json()


def test_email_is_case_insensitive_unique(client):
    register(client, email="Mixed@Example.com")
    r = client.post(f"{API}/auth/register", json={"email": "mixed@example.com", "password": PASSWORD, "full_name": "x"})
    assert r.status_code == 400


def test_password_policy(client):
    base = {"email": "a@example.com", "full_name": "A"}
    assert client.post(f"{API}/auth/register", json={**base, "password": "short"}).status_code == 422
    assert client.post(f"{API}/auth/register", json={**base, "password": "é" * 40}).status_code == 422  # >72 bytes
    assert client.post(f"{API}/auth/register", json={**base, "password": PASSWORD, "is_verified": True}).status_code == 422


def test_login_errors_are_generic(client):
    register(client)
    wrong = client.post(f"{API}/auth/login", json={"email": "user@example.com", "password": "nope-nope-nope"})
    unknown = client.post(f"{API}/auth/login", json={"email": "ghost@example.com", "password": "nope-nope-nope"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_login_lockout(client):
    register(client)
    for _ in range(5):
        assert client.post(f"{API}/auth/login", json={"email": "user@example.com", "password": "bad-password"}).status_code == 401
    locked = client.post(f"{API}/auth/login", json={"email": "user@example.com", "password": PASSWORD})
    assert locked.status_code == 429 and "Retry-After" in locked.headers


def test_refresh_rotation_and_reuse_detection(client):
    first = register(client)
    second = client.post(f"{API}/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert second.status_code == 200
    # Replaying the already-rotated token is treated as theft ...
    replay = client.post(f"{API}/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert replay.status_code == 401
    # ... and revokes the descendant too.
    child = client.post(f"{API}/auth/refresh", json={"refresh_token": second.json()["refresh_token"]})
    assert child.status_code == 401


def test_logout_revokes_refresh_token(client):
    tokens = register(client)
    assert client.post(f"{API}/auth/logout", json={"refresh_token": tokens["refresh_token"]}).status_code == 200
    assert client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


def test_token_types_are_not_interchangeable(client):
    tokens = register(client)
    assert client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}).status_code == 401
    assert client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["access_token"]}).status_code == 401


def _forge(**overrides):
    now = datetime.now(timezone.utc)
    claims = {"sub": "x", "type": "access", "jti": "j", "iat": now, "exp": now + timedelta(minutes=5),
              "iss": settings.jwt_issuer, "aud": settings.jwt_audience}
    key = overrides.pop("key", settings.secret_key)
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="HS256")


def test_forged_and_expired_tokens_rejected(client, db):
    register(client)
    uid = db.query(User).one().id
    bad = {
        "wrong key": _forge(sub=uid, key="k" * 40),
        "expired": _forge(sub=uid, exp=datetime.now(timezone.utc) - timedelta(minutes=1)),
        "wrong audience": _forge(sub=uid, aud="someone-else"),
        "wrong issuer": _forge(sub=uid, iss="evil"),
        "alg none": jwt.encode({"sub": uid, "type": "access"}, None, algorithm="none"),
        "garbage": "not.a.jwt",
    }
    for name, token in bad.items():
        r = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401, name
    assert client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {_forge(sub=uid)}"}).status_code == 200


def test_deactivated_user_loses_access_immediately(client, db):
    tokens = register(client)
    db.query(User).update({"is_active": False})
    db.commit()
    assert client.get(f"{API}/auth/me", headers=auth_headers(tokens)).status_code == 401
    assert client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


def test_otp_stub_removed(client):
    assert client.post(f"{API}/auth/verify-otp", json={"email": "a@example.com", "otp": "000000"}).status_code in (404, 405)


def test_profile_update_cannot_escalate(client, user):
    h = user["headers"]
    assert client.put(f"{API}/users/me", headers=h, json={"is_verified": True}).status_code == 422
    assert client.put(f"{API}/users/me", headers=h, json={"is_active": False, "hashed_password": "x"}).status_code == 422
    assert client.put(f"{API}/users/me", headers=h, json={"language": "<script>"}).status_code == 422
    assert client.put(f"{API}/users/me", headers=h, json={"language": None}).status_code == 422
    assert client.put(f"{API}/users/me", headers=h, json={"avatar_url": "javascript:alert(1)"}).status_code == 422
    ok = client.put(f"{API}/users/me", headers=h, json={"language": "hi", "avatar_url": "https://example.com/a.png"})
    assert ok.status_code == 200 and ok.json()["language"] == "hi"


def test_profile_validation(client, user):
    h = user["headers"]
    assert client.put(f"{API}/users/me/profile", headers=h, json={"phone": "abc"}).status_code == 422
    assert client.put(f"{API}/users/me/profile", headers=h, json={"study_goal_hours_per_week": 9999}).status_code == 422
    assert client.put(f"{API}/users/me/profile", headers=h, json={"date_of_birth": "3000-01-01"}).status_code == 422
    assert client.put(f"{API}/users/me/profile", headers=h, json={"phone": "+91 98765 43210", "date_of_birth": "2000-01-31"}).status_code == 200
