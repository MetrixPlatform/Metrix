from app.core.module import (
    AppModule,
    action_code,
    define_module,
    resource_action,
    resource_permissions,
    table_column_sync,
)

SCRIPT_CREATE = action_code("script", "create")
SCRIPT_READ = action_code("script", "read")
SCRIPT_UPDATE = action_code("script", "update")
SCRIPT_DELETE = action_code("script", "delete")
SCRIPT_OPERATE = action_code("script", "operate")
SCRIPT_MANAGE_OTHERS = action_code("script", "manage_others")

APP_MODULE = define_module(
    AppModule(
        key="scripts",
        version="0.1.0",
        order=50,
        dependencies=("core", "containers"),
        router_paths=("app.modules.scripts.api:router",),
        model_paths=("app.modules.scripts.models",),
        table_syncs=(
            table_column_sync(
                "script_projects",
                {"is_shared": "ALTER TABLE script_projects ADD COLUMN is_shared BOOLEAN NOT NULL DEFAULT 0"},
            ),
        ),
        resource_permissions=(
            resource_permissions(
                "script",
                "script",
                887,
                (
                    resource_action("create", 10),
                    resource_action("read", 20),
                    resource_action("update", 30),
                    resource_action("delete", 40),
                    resource_action("operate", 50),
                    resource_action("manage_others", 60),
                ),
            ),
        ),
        openapi_hidden_tags=("scripts",),
        openapi_hidden_path_prefixes=("/api/scripts",),
    )
)
