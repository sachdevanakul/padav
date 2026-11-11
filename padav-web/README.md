# PADAV

PADAV is a bilingual exam preparation platform with a React + TypeScript frontend and a Python + FastAPI backend. The React app is the primary interface; the former browser app is available under `/legacy` while its content is migrated.

## Run locally

Run these commands from PowerShell. The backend commands assume Python 3.11 is installed.

One-time setup:

```powershell
cd D:\padav\padav-web
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm ci
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Start both the API and React development server together:

```powershell
cd D:\padav\padav-web
.\.venv\Scripts\python.exe main.py
```

If you activated the virtual environment, you can instead run `python main.py`. Open `http://localhost:5173` for the frontend; API docs are at `http://localhost:8000/docs`. Press `Ctrl+C` in that terminal to stop both servers. Make sure Node.js is installed and `npm ci` has completed before starting.

After initial setup, apply migrations whenever a new schema migration is added:

```powershell
cd D:\padav\padav-web
.\.venv\Scripts\python.exe -m alembic upgrade head
```

To serve the built React app through FastAPI instead, run `npm run build`, then start the API and open `http://localhost:8000`.

## Project layout

- `app/` — FastAPI backend, layered: `api/` (thin routers) → `services/` (business rules) → `repositories/` (data access) → `models/`. `core/` holds config, security, rate limiting, middleware and shared exceptions.
- `alembic/` and `alembic.ini` — schema migration environment and revision history.
- `src/` — React pages, reusable components, state, API services, locales, and styles.
- `tests/` — backend API, access-control and security tests (`pip install -r requirements-dev.txt && pytest`).
- `legacy/` plus root `js/`, `css/`, `data/`, and `icons/` — the previous browser app, retained during migration.
- `.env.example` — local environment variable template.

The default development database is SQLite (`padav.db`). PostgreSQL can be configured with `DATABASE_URL`. Development catalog data is seeded automatically when the API starts. Run migrations before starting the API.

## Database migrations

Alembic owns schema creation and changes; the application no longer creates tables with `Base.metadata.create_all()` on startup.

```powershell
# Apply migrations to the configured database
python -m alembic upgrade head

# Create a migration after changing SQLAlchemy models, then review its operations
python -m alembic revision --autogenerate -m "describe the schema change"

# Apply the new migration
python -m alembic upgrade head
```

The checked-in initial revision is the baseline for new databases. If upgrading a database that was already created by the old `create_all()` startup path, and its schema already matches the current models, mark it at the baseline once instead of trying to create the existing tables again:

```powershell
python -m alembic stamp head
```

Only use `stamp head` for an existing database whose schema already matches the baseline. Back up existing data before database changes.

## Current implementation scope

Foundation and initial experience include the responsive app shell, onboarding, login and registration, exam selection, the dashboard, persistent theme/language preferences, JWT authentication with rotating refresh tokens, course/catalog APIs, study planning, test attempt scoring endpoints, and Alembic database migrations. Course player, full test-taking UI, detailed analytics, profile/settings, and deployment hardening remain follow-up work.

## Security notes

- **Secrets:** never commit `.env`. In production `SECRET_KEY` (>= 32 random chars), `ALLOWED_HOSTS` and explicit `CORS_ORIGINS` are mandatory and `DEBUG` must be off; the app refuses to start otherwise. In development an empty `SECRET_KEY` gives a random per-process key.
- **Auth:** bcrypt passwords (max 72 bytes), JWTs pinned to HS256 with issuer/audience/`jti`, single-use rotating refresh tokens with reuse detection (a replayed token revokes all of that user's sessions), per-account login lockout and per-IP rate limits. Rate-limit state is in memory (per worker); use a shared store such as Redis when running several instances, and run uvicorn with `--proxy-headers --forwarded-allow-ips=<proxy>` behind a reverse proxy.
- **Authorization:** all per-user data goes through `OwnedRepository`, which scopes every lookup by `user_id`; other users' rows return 404.
- **Responses:** correct answers and per-answer correctness are never sent while an attempt is open; locked lessons need a signed-in user.
- **HTTP:** CSP, `X-Frame-Options`, `nosniff`, HSTS (production) and `Cache-Control: no-store` on API responses. Swagger docs and starter seed data are off in production.
- **Service worker:** `/api/*` responses are never cached.
- **Known follow-ups:** there is no test<->question link table yet (answers are checked against the test's section subjects); tokens are kept in `sessionStorage` on the client (an HttpOnly-cookie refresh token would reduce XSS impact); e-mail verification / password reset are not implemented.

## Test arena (v1 slice)

- Pages: `/tests` (list + your attempts), `/tests/attempts/:id` (timed runner), `/tests/attempts/:id/result` (score + review).
- The runner counts down from the server-computed `seconds_remaining`, auto-saves each answer, auto-submits at zero, and never receives the answer key. The key and explanations are only served by `/tests/attempts/:id/review` after submission.
- Add content with `python -m app.cli import-content content/<file>.json` (format: `content/ssc-cgl-sample.json`). Keep answer-key files in `content/`, never in a served folder such as `data/`.
- After pulling: `python -m alembic upgrade head`.
