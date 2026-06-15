from app.core.module import AppModule, action_code, define_module, page_permission, resource_action, resource_permissions

CONTAINER_CREATE = action_code("container", "create")
CONTAINER_READ = action_code("container", "read")
CONTAINER_UPDATE = action_code("container", "update")
CONTAINER_DELETE = action_code("container", "delete")
CONTAINER_OPERATE = action_code("container", "operate")
CONTAINER_MANAGE_OTHERS = action_code("container", "manage_others")

APP_MODULE = define_module(
    AppModule(
        key="containers",
        version="0.1.0",
        order=45,
        dependencies=("core",),
        router_paths=(
            "app.modules.containers.api:engine_router",
            "app.modules.containers.api:images_router",
            "app.modules.containers.api:instances_router",
            "app.modules.containers.api:jobs_router",
        ),
        model_paths=("app.modules.containers.models",),
        page_permissions=(
            page_permission("containers", "container", 875, CONTAINER_READ),
        ),
        resource_permissions=(
            resource_permissions(
                "container",
                "container",
                885,
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
        openapi_hidden_tags=("container-engine",),
    )
)
