import asyncio
from copy import deepcopy
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from swagger_ui_bundle import swagger_ui_path

from app.api import announcements, audit, auth, dashboard, health, install, roles, settings as settings_api, tokens, users
from app.core.config import get_settings
from app.core.deps import require_api_feature_enabled, require_permission
from app.core.permissions import API_DOCS_READ
from app.models import User
from app.services.maintenance import audit_log_prune_loop

OPENAPI_HIDDEN_TAGS = {"api-tokens", "health", "install"}
OPENAPI_HIDDEN_PATH_PREFIXES = ("/api/health", "/api/install", "/api/tokens")
OPENAPI_HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}


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
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
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
    app.include_router(tokens.router)
    app.include_router(users.router)
    app.include_router(roles.router)
    app.mount("/static/swagger-ui", StaticFiles(directory=swagger_ui_path), name="swagger-ui")

    @app.get("/openapi.json", include_in_schema=False)
    def openapi_json(
        _: None = Depends(require_api_feature_enabled),
        __: User = Depends(require_permission(API_DOCS_READ)),
    ) -> JSONResponse:
        return JSONResponse(filtered_openapi_schema(app.openapi()))

    @app.get("/docs", include_in_schema=False)
    def swagger_docs(
        _: None = Depends(require_api_feature_enabled),
        __: User = Depends(require_permission(API_DOCS_READ)),
    ):
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=f"{settings.app_name} API",
            swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui/swagger-ui.css",
            swagger_favicon_url="/static/swagger-ui/favicon-32x32.png",
        )

    return app


def filtered_openapi_schema(schema: dict) -> dict:
    filtered = deepcopy(schema)
    filtered_paths = {}
    for path, path_item in filtered.get("paths", {}).items():
        visible_path_item = _filtered_path_item(path, path_item)
        if visible_path_item:
            filtered_paths[path] = visible_path_item
    filtered["paths"] = filtered_paths
    filtered["tags"] = [
        tag
        for tag in filtered.get("tags", [])
        if tag.get("name") not in OPENAPI_HIDDEN_TAGS
    ]
    return filtered


def _filtered_path_item(path: str, path_item: dict) -> dict:
    if path.startswith(OPENAPI_HIDDEN_PATH_PREFIXES):
        return {}
    kept = {}
    for method, operation in path_item.items():
        if method not in OPENAPI_HTTP_METHODS:
            kept[method] = operation
            continue
        if OPENAPI_HIDDEN_TAGS.intersection(operation.get("tags") or []):
            continue
        kept[method] = operation
    return kept if any(method in OPENAPI_HTTP_METHODS for method in kept) else {}


app = create_app()
