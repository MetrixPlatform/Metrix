from app.core.module import AppModule, action_code, define_module, resource_action, resource_permissions

STORAGE_CREATE = action_code("storage", "create")
STORAGE_READ = action_code("storage", "read")
STORAGE_UPDATE = action_code("storage", "update")
STORAGE_DELETE = action_code("storage", "delete")
STORAGE_OPERATE = action_code("storage", "operate")
STORAGE_MANAGE_OTHERS = action_code("storage", "manage_others")

APP_MODULE = define_module(
    AppModule(
        key="storage",
        version="0.1.0",
        order=30,
        dependencies=("core",),
        router_paths=("app.modules.storage.api:router",),
        model_paths=("app.modules.storage.models",),
        resource_permissions=(
            resource_permissions(
                "storage",
                "storage",
                860,
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
        openapi_hidden_tags=("storages",),
    )
)
