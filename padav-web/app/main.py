from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.database.session import create_db_and_tables
from app.api.v1 import auth, users, exams, courses, tests, analytics, bookmarks, lessons, planner
from app.database.session import SessionLocal
from app.services.seed import seed_development_data

PROJECT_ROOT = Path(__file__).resolve().parent.parent

@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.environment != "production":
        create_db_and_tables()
    with SessionLocal() as db:
        seed_development_data(db)
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the existing vanilla JavaScript PWA from the project root.
for asset_dir in ("css", "data", "icons", "js"):
    app.mount(
        f"/{asset_dir}",
        StaticFiles(directory=PROJECT_ROOT / asset_dir),
        name=asset_dir,
    )

# Include API routers
app.include_router(auth.router, prefix=settings.api_v1_str)
app.include_router(users.router, prefix=settings.api_v1_str)
app.include_router(exams.router, prefix=settings.api_v1_str)
app.include_router(courses.router, prefix=settings.api_v1_str)
app.include_router(tests.router, prefix=settings.api_v1_str)
app.include_router(analytics.router, prefix=settings.api_v1_str)
app.include_router(bookmarks.router, prefix=settings.api_v1_str)
app.include_router(lessons.router, prefix=settings.api_v1_str)
app.include_router(planner.router, prefix=settings.api_v1_str)

@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}


@app.get("/")
def home():
    built_entry = PROJECT_ROOT / "dist" / "index.html"
    return FileResponse(built_entry if built_entry.exists() else PROJECT_ROOT / "legacy" / "index.html")


@app.get("/legacy")
def legacy_home():
    return FileResponse(PROJECT_ROOT / "legacy" / "index.html")


@app.get("/manifest.webmanifest")
def manifest():
    return FileResponse(PROJECT_ROOT / "manifest.webmanifest")


@app.get("/sw.js")
def service_worker():
    return FileResponse(
        PROJECT_ROOT / "sw.js",
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/"},
    )


dist_assets = PROJECT_ROOT / "dist" / "assets"
if dist_assets.is_dir():
    app.mount("/assets", StaticFiles(directory=dist_assets), name="built-assets")

dist_directory = PROJECT_ROOT / "dist"
if dist_directory.is_dir():
    app.mount("/", StaticFiles(directory=dist_directory, html=True), name="frontend")
