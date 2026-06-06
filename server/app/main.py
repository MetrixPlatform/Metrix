import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from swagger_ui_bundle import swagger_ui_path

from app.api import announcements, audit, auth, dashboard, health, install, roles, settings as settings_api, users
from app.core.config import get_settings
from app.services.maintenance import audit_log_prune_loop


@asynccontextmanager
async def lifespan(_: FastAPI):
    audit_log_prune_task = asyncio.create_task(audit_log_prune_loop())
    try:
        yield
    finally:
        audit_log_prune_task.cancel()
        try:
            await audit_log_prune_task
        except asyncio.CancelledError:
            pass


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version, docs_url=None, redoc_url=None, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(install.router)
    app.include_router(auth.router)
    app.include_router(dashboard.router)
    app.include_router(announcements.router)
    app.include_router(audit.router)
    app.include_router(settings_api.router)
    app.include_router(users.router)
    app.include_router(roles.router)
    app.mount("/static/swagger-ui", StaticFiles(directory=swagger_ui_path), name="swagger-ui")

    @app.get("/docs", include_in_schema=False)
    def swagger_docs():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{settings.app_name} API",
            swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui/swagger-ui.css",
            swagger_favicon_url="/static/swagger-ui/favicon-32x32.png",
        )

    return app


app = create_app()
