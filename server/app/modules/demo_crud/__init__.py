from app.core.module import AppModule, action_code, define_module, page_permission, resource_action, resource_permissions

DEMO_ITEM_CREATE = action_code("demo_item", "create")
DEMO_ITEM_READ = action_code("demo_item", "read")
DEMO_ITEM_UPDATE = action_code("demo_item", "update")
DEMO_ITEM_DELETE = action_code("demo_item", "delete")
DEMO_ITEM_MANAGE_OTHERS = action_code("demo_item", "manage_others")

APP_MODULE = define_module(
    AppModule(
        key="demo_crud",
        version="0.1.0",
        order=90,
        dependencies=("core",),
        router_paths=("app.modules.demo_crud.api:router",),
        model_paths=("app.modules.demo_crud.models",),
        page_permissions=(
            page_permission("demo_crud", "demo_item", 900, DEMO_ITEM_READ),
        ),
        resource_permissions=(
            resource_permissions(
                "demo_item",
                "demoCrud",
                910,
                (
                    resource_action("create", 10),
                    resource_action("read", 20),
                    resource_action("update", 30),
                    resource_action("delete", 40),
                    resource_action("manage_others", 50),
                ),
            ),
        ),
    )
)
