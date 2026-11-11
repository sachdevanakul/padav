import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1 import analytics, auth, bookmarks, courses, exams, lessons, planner, tests, users
from app.core.config import settings
from app.core.exceptions import DomainError
from app.core.middleware import SecurityHeadersMiddleware
from app.database.session import SessionLocal
from app.services.seed import seed_development_data

logger = logging.getLogger("padav")
PROJECT_ROOT = Path(__file__).resolve().parent.parent

ROUTERS = (auth, users, exams, courses, tests, analytics, bookmarks, lessons, planner)
LEGACY_ASSET_DIRS = ("css", "data", "icons", "js")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.seed_on_startup:  # starter catalogue is for development only
        with SessionLocal() as db:
            seed_development_data(db)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        # Debug tracebacks and the interactive docs are never exposed in production.
        debug=settings.debug and not settings.is_production,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        lifespan=lifespan,
    )
    _add_middleware(app)
    _add_error_handlers(app)
    for module in ROUTERS:
        app.include_router(module.router, prefix=settings.api_v1_str)
    _add_frontend_routes(app)
    return app


def _add_middleware(app: FastAPI) -> None:
    # Added last = outermost, so security headers also cover CORS/host rejections.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
        max_age=600,
    )
    if settings.allowed_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    app.add_middleware(SecurityHeadersMiddleware, config=settings)


def _add_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse({"detail": "Internal server error"}, status_code=500)


def _add_frontend_routes(app: FastAPI) -> None:
    @app.get("/health", include_in_schema=False)
    def health():
        return {"status": "ok"}  # no service name/version: nothing to fingerprint

    # Legacy vanilla-JS PWA assets.
    for asset_dir in LEGACY_ASSET_DIRS:
        app.mount(f"/{asset_dir}", StaticFiles(directory=PROJECT_ROOT / asset_dir), name=asset_dir)

    @app.get("/", include_in_schema=False)
    def home():
        built = PROJECT_ROOT / "dist" / "index.html"
        return FileResponse(built if built.exists() else PROJECT_ROOT / "legacy" / "index.html")

    @app.get("/legacy", include_in_schema=False)
    def legacy_home():
        return FileResponse(PROJECT_ROOT / "legacy" / "index.html")

    @app.get("/manifest.webmanifest", include_in_schema=False)
    def manifest():
        return FileResponse(PROJECT_ROOT / "manifest.webmanifest")

    @app.get("/sw.js", include_in_schema=False)
    def service_worker():
        return FileResponse(
            PROJECT_ROOT / "sw.js",
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
        )

    dist = PROJECT_ROOT / "dist"
    if (dist / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="built-assets")
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")


app = create_app()
