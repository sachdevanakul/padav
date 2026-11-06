# PADAV

PADAV is a bilingual exam preparation platform with a React + TypeScript frontend and a Python + FastAPI backend. The React app is the primary interface; the former browser app is available under `/legacy` while its content is migrated.

## Run locally

In one PowerShell terminal, start the API:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
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
- `src/` — React pages, reusable components, state, API services, locales, and styles.
- `tests/` — backend API and scoring tests.
- `legacy/` plus root `js/`, `css/`, `data/`, and `icons/` — the previous browser app, retained during migration.
- `.env.example` — local environment variable template.

The default development database is SQLite (`padav.db`). PostgreSQL can be configured with `DATABASE_URL`. Development catalog data is seeded automatically when the API starts.

## Current implementation scope

Foundation and initial experience include the responsive app shell, onboarding, login and registration, exam selection, the dashboard, persistent theme/language preferences, JWT authentication with rotating refresh tokens, course/catalog APIs, and test attempt scoring endpoints. Course player, full test-taking UI, detailed analytics, profile/settings, production PostgreSQL migrations, and deployment hardening remain follow-up work.
