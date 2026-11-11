import pytest

from app.core.config import ConfigurationError, Settings
from app.core.security import PasswordHasher

API = "/api/v1"


def test_security_headers(client):
    r = client.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert r.json() == {"status": "ok", "service": "Padav"}
    assert client.get(f"{API}/exams").headers["cache-control"] == "no-store"


def test_cors_only_for_configured_origins(client):
    ok = client.options(f"{API}/exams", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    bad = client.options(f"{API}/exams", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in bad.headers


def test_unhandled_errors_do_not_leak(monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app
    from app.services import catalog

    def boom(self):
        raise RuntimeError("secret internals")

    monkeypatch.setattr(catalog.CatalogService, "list_exams", boom)
    with TestClient(app, raise_server_exceptions=False) as quiet:
        r = quiet.get(f"{API}/exams")
    assert r.status_code == 500 and r.json() == {"detail": "Internal server error"}


def test_built_frontend_routes_support_deep_links(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    import app.main as main

    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    for asset_dir in main.LEGACY_ASSET_DIRS:
        (tmp_path / asset_dir).mkdir()
    (dist / "index.html").write_text("<html><div id='root'></div></html>", encoding="utf-8")
    monkeypatch.setattr(main, "PROJECT_ROOT", tmp_path)

    with TestClient(main.create_app()) as frontend:
        page = frontend.get("/onboarding", headers={"accept": "text/html"})
        assert page.status_code == 200 and "<div id='root'></div>" in page.text
        assert frontend.get("/auth/register", headers={"accept": "text/html"}).status_code == 200
        assert frontend.get("/api/v1/unknown", headers={"accept": "text/html"}).status_code == 404
        assert frontend.get("/missing.js", headers={"accept": "application/javascript"}).status_code == 404


def test_auth_endpoint_ip_rate_limit(client, monkeypatch):
    from app.core import rate_limit
    monkeypatch.setattr(rate_limit.auth_rate_limit._limiter, "limit", 3)
    codes = [client.post(f"{API}/auth/login", json={"email": "a@example.com", "password": "x"}).status_code for _ in range(5)]
    assert codes[:3] == [401, 401, 401] and codes[3:] == [429, 429]


def _prod_env(monkeypatch, **extra):
    base = {"ENVIRONMENT": "production", "SECRET_KEY": "s" * 48, "DEBUG": "false", "ALLOWED_HOSTS": "padav.example",
            "CORS_ORIGINS": "https://padav.example"}
    for key, value in {**base, **extra}.items():
        monkeypatch.setenv(key, value)


def test_production_config_ok(monkeypatch):
    _prod_env(monkeypatch)
    cfg = Settings()
    assert cfg.docs_enabled is False and cfg.seed_on_startup is False and cfg.is_production


@pytest.mark.parametrize("override", [
    {"SECRET_KEY": "short"},
    {"SECRET_KEY": "dev-only-change-me-before-deploying"},
    {"DEBUG": "true"},
    {"CORS_ORIGINS": "*"},
    {"ALLOWED_HOSTS": ""},
])
def test_production_config_rejects_unsafe(monkeypatch, override):
    _prod_env(monkeypatch, **override)
    with pytest.raises(ConfigurationError):
        Settings()


def test_production_requires_secret(monkeypatch):
    _prod_env(monkeypatch)
    monkeypatch.delenv("SECRET_KEY")
    monkeypatch.setattr("app.core.config.load_dotenv", lambda *a, **k: None, raising=False)
    with pytest.raises(ConfigurationError):
        Settings()


def test_dev_secret_is_random_not_constant(monkeypatch):
    monkeypatch.delenv("SECRET_KEY")
    a, b = Settings().secret_key, Settings().secret_key
    assert a != b and a != "dev-only-change-me-before-deploying"


def test_hasher_roundtrip_and_legacy_hash():
    hasher = PasswordHasher(rounds=10)
    hashed = hasher.hash("pässword-1")
    assert hasher.verify("pässword-1", hashed) and not hasher.verify("other", hashed)
    assert hasher.verify("anything", None) is False
    assert hasher.verify("x", "not-a-hash") is False
    assert hashed.startswith("$2b$")  # same format passlib produced, existing users keep working


def test_spa_route_serves_real_files_and_blocks_traversal(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    import app.main as main

    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    for asset_dir in main.LEGACY_ASSET_DIRS:
        (tmp_path / asset_dir).mkdir()
    (dist / "index.html").write_text("<html>app</html>", encoding="utf-8")
    (dist / "favicon.svg").write_text("<svg/>", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("TOP-SECRET", encoding="utf-8")
    monkeypatch.setattr(main, "PROJECT_ROOT", tmp_path)

    with TestClient(main.create_app()) as c:
        # a real root-level file is served even when the request does not accept HTML
        ok = c.get("/favicon.svg", headers={"accept": "image/svg+xml"})
        assert ok.status_code == 200 and "<svg/>" in ok.text
        # path traversal (plain and encoded) must never reach files outside dist
        for attempt in ("/../secret.txt", "/%2e%2e/secret.txt", "/..%2fsecret.txt", "/assets/../../secret.txt"):
            r = c.get(attempt, headers={"accept": "text/html"})
            assert "TOP-SECRET" not in r.text, attempt
