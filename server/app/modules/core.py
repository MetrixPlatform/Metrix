from app.core.module import (
    AppModule,
    action_code,
    define_module,
    page_permission,
    resource_action,
    resource_permissions,
    table_column_sync,
)

USER_READ = action_code("user", "read")
ROLE_READ = action_code("role", "read")
ANNOUNCEMENT_READ = action_code("announcement", "read")
AUDIT_LOG_READ = action_code("audit_log", "read")
SETTING_READ = action_code("setting", "read")
API_TOKEN_READ = action_code("api_token", "read")
API_DOCS_READ = action_code("api_docs", "read")

APP_MODULE = define_module(
    AppModule(
        key="core",
        order=10,
        router_paths=(
            "app.api.health:router",
            "app.api.install:router",
            "app.api.auth:router",
            "app.api.dashboard:router",
            "app.api.announcements:router",
            "app.api.audit:router",
            "app.api.settings:router",
            "app.api.tokens:router",
            "app.api.users:router",
            "app.api.roles:router",
        ),
        page_permissions=(
            page_permission("dashboard", "dashboard", 10),
            page_permission("users", "user", 20, USER_READ),
            page_permission("permissions", "role", 30, ROLE_READ),
            page_permission("announcements", "announcement", 40, ANNOUNCEMENT_READ),
            page_permission("audit_logs", "audit_log", 50, AUDIT_LOG_READ),
            page_permission("settings", "setting", 60, SETTING_READ),
            page_permission("tokens", "api_token", 70, API_TOKEN_READ),
            page_permission("api_docs", "api_docs", 80, API_DOCS_READ),
        ),
        resource_permissions=(
            resource_permissions(
                "user",
                "user",
                100,
                (
                    resource_action("create", 10),
                    resource_action("read", 20),
                    resource_action("update", 30),
                    resource_action("delete", 40),
                    resource_action("operate", 50),
                ),
            ),
            resource_permissions(
                "role",
                "role",
                200,
                (
                    resource_action("create", 10),
                    resource_action("read", 20),
                    resource_action("update", 30),
                    resource_action("delete", 40),
                    resource_action("operate", 50),
                ),
            ),
            resource_permissions(
                "announcement",
                "announcement",
                300,
                (
                    resource_action("create", 10),
                    resource_action("read", 20),
                    resource_action("update", 30),
                    resource_action("delete", 40),
                    resource_action("manage_others", 50),
                ),
            ),
            resource_permissions(
                "audit_log",
                "auditLog",
                400,
                (
                    resource_action("read", 20),
                    resource_action("manage_others", 50),
                ),
            ),
            resource_permissions(
                "setting",
                "setting",
                500,
                (
                    resource_action("read", 20),
                    resource_action("update", 30),
                    resource_action("operate", 50),
                ),
            ),
            resource_permissions(
                "api_token",
                "api",
                600,
                (
                    resource_action("read", 20),
                    resource_action("create", 30),
                    resource_action("delete", 40),
                ),
            ),
            resource_permissions(
                "api_docs",
                "api",
                700,
                (
                    resource_action("read", 20),
                ),
            ),
        ),
        table_syncs=(
            table_column_sync(
                "users",
                {
                    "phone": "ALTER TABLE users ADD COLUMN phone VARCHAR(20) NOT NULL DEFAULT ''",
                    "email": "ALTER TABLE users ADD COLUMN email VARCHAR(254) NOT NULL DEFAULT ''",
                },
            ),
            table_column_sync(
                "audit_logs",
                {
                    "source": "ALTER TABLE audit_logs ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'web'",
                    "api_token_prefix": "ALTER TABLE audit_logs ADD COLUMN api_token_prefix VARCHAR(16) NOT NULL DEFAULT ''",
                    "detail_data": "ALTER TABLE audit_logs ADD COLUMN detail_data TEXT",
                },
            ),
            table_column_sync(
                "api_tokens",
                {
                    "token_value": "ALTER TABLE api_tokens ADD COLUMN token_value VARCHAR(128)",
                },
            ),
        ),
        openapi_hidden_tags=("api-tokens", "auth", "health", "install", "roles", "settings", "users"),
        openapi_hidden_path_prefixes=(
            "/api/auth",
            "/api/health",
            "/api/install",
            "/api/permissions",
            "/api/roles",
            "/api/settings",
            "/api/tokens",
            "/api/users",
        ),
    )
)
