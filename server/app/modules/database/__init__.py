from app.core.module import (
    AppModule,
    action_code,
    define_module,
    resource_action,
    resource_permissions,
    table_column_sync,
)

DATABASE_CREATE = action_code("database", "create")
DATABASE_READ = action_code("database", "read")
DATABASE_UPDATE = action_code("database", "update")
DATABASE_DELETE = action_code("database", "delete")
DATABASE_OPERATE = action_code("database", "operate")
DATABASE_MANAGE_OTHERS = action_code("database", "manage_others")

SQL_SCRIPT_CREATE = action_code("sql_script", "create")
SQL_SCRIPT_READ = action_code("sql_script", "read")
SQL_SCRIPT_UPDATE = action_code("sql_script", "update")
SQL_SCRIPT_DELETE = action_code("sql_script", "delete")
SQL_SCRIPT_MANAGE_OTHERS = action_code("sql_script", "manage_others")

APP_MODULE = define_module(
    AppModule(
        key="database",
        version="0.1.0",
        order=40,
        dependencies=("core",),
        router_paths=(
            "app.modules.database.api:router",
            "app.modules.database.api:scripts_router",
            "app.modules.database.api:jobs_router",
        ),
        model_paths=("app.modules.database.models",),
        resource_permissions=(
            resource_permissions(
                "database",
                "database",
                880,
                (
                    resource_action("create", 10),
                    resource_action("read", 20),
                    resource_action("update", 30),
                    resource_action("delete", 40),
                    resource_action("operate", 50),
                    resource_action("manage_others", 60),
                ),
            ),
            resource_permissions(
                "sql_script",
                "database",
                950,
                (
                    resource_action("create", 10),
                    resource_action("read", 20),
                    resource_action("update", 30),
                    resource_action("delete", 40),
                    resource_action("manage_others", 50),
                ),
            ),
        ),
        table_syncs=(
            table_column_sync("sql_scripts", {"database": "ALTER TABLE sql_scripts ADD COLUMN `database` VARCHAR(128) NOT NULL DEFAULT ''"}),
        ),
        openapi_hidden_tags=("databases", "sql-scripts"),
    )
)
