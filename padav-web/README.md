# PADAV

PADAV is a bilingual exam preparation platform with a React + TypeScript frontend and a Python + FastAPI backend. The React app is the primary interface; the former browser app is available under `/legacy` while its content is migrated.

## Run locally

In one PowerShell terminal, start the API:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m alembic upgrade head
python main.py
```

In a second terminal, start the React frontend:

```powershell
npm install
npm run dev
```

Open the Vite URL shown in the terminal (normally `http://localhost:5173`). The development server proxies `/api` requests to FastAPI at `http://localhost:8000`. API docs are at `http://localhost:8000/docs`.

To serve the built React app through FastAPI instead, run `npm run build`, then start the API and open `http://localhost:8000`.

## Project layout

- `app/` — FastAPI routers, services, schemas, models, and database setup.
- `alembic/` and `alembic.ini` — schema migration environment and revision history.
- `src/` — React pages, reusable components, state, API services, locales, and styles.
- `tests/` — backend API and scoring tests.
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
