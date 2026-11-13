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

## Profile, settings and dashboard

- `/profile` edits name, phone, date of birth, education level and weekly study goal (validated on client and server) and lists/removes your exams.
- `/settings` switches language and theme (applied instantly, synced to the account best-effort) and changes the password via `POST /api/v1/auth/change-password`. A successful change signs out every other session and returns fresh tokens.
- The dashboard trend chart, streak week and next-test card use real data (`/analytics/trends`, `/analytics/overview?tz_offset=`, `/tests`). Streak days are calculated in the browser's time zone.

## Padav Intelligence Assessment (PIA)

Research build of the PIA described in the master specification (v1.0). It produces **experimental raw results only**; no IQ-style score exists until norms do.

- Blueprint constants (50 items, seven timed subtests, 46 min, difficulty mix, 240-item pool) live in `app/services/pia_blueprint.py`. Changing them is a formal specification revision.
- Flow: `POST /pia/consent` → `POST /pia/sessions` → per subtest `POST .../subtests/{domain}/start`, `PUT .../answers`, `POST .../complete` → `POST .../finish` → `GET .../report`. Subtests run strictly in order, one at a time.
- The server owns the clock: each subtest has a server-computed deadline (2 s answer grace). Late answers get 409 and the run is marked `timed_out`. An `interruption` event flags the run but does not pause the timer; exclusion/retest policy is for the analysis plan.
- Answer keys, explanations and difficulty never leave the server. `pia_responses` and `pia_events` are append-only (the ORM refuses updates/deletes); the newest response per item is the final answer.
- Consent is required before a session (13+; under 18 needs guardian consent). Reports carry `status: "experimental"`, `norm_version: null` and limitation notices.
- Content: `python -m app.cli import-pia content/pia-sample.json [--activate]`. Imports are atomic and versioned (existing item versions are skipped). A form can only be activated with exactly 50 non-draft items matching the blueprint's domain and difficulty counts. `content/pia-sample.json` shows the format (six draft items, English + Hindi).

### PIA screens

`/pia` (intro + consent, resumes an open session) → `/pia/sessions/:id` (section list, one timed section at a time) → `/pia/sessions/:id/report`. The runner mirrors the server's countdown, saves every answer immediately (with response time), treats a 409 as "time is up", and reports offline/tab-hidden periods as interruption events. The report shows raw counts only; it never shows an IQ, percentile or label.

### PIA master form v1 (draft prototype)

`content/pia-master-v1.json` holds the 50-item master form (English + Hindi) with 12 generated figures in `content/pia-assets/`. Regenerate with `python content/pia/build_master.py`; the builder computes or asserts every answer key (and a test checks the committed files match a fresh build).

- Blueprint: Gf 10, Gc 7, Gv 8, Gwm 7, Gs 7, Gq 7, Glr 4; difficulty 12 / 18 / 13 / 7.
- All items are **draft** (AI-drafted, original). They need expert review, bilingual review and cognitive interviews before use with real participants. A draft form can only be activated for development: `python -m app.cli import-pia content/pia-master-v1.json --activate --allow-draft`.
- Timed material (working memory, long-term retrieval) is withheld from the item list and released once via `POST .../items/{code}/stimulus`; the release is logged (`encoding_start`) and the answer choices stay hidden until the material has been shown and hidden. Answers are refused until the material has been released.
- Known limits: the Glr "delay" is only the time spent on the items in between (a true delayed retrieval after other subtests is not built); memory items use recognition choices, not free recall; visual items need a non-visual accommodation before release; speeded items are timed by the section clock, not per item.
