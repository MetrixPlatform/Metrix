from dataclasses import dataclass

MODULE_LIFECYCLE_EVENTS = {"install", "upgrade", "disable"}


def route_code(page: str) -> str:
    return f"route:{page}"


def action_code(resource: str, action: str) -> str:
    return f"action:{resource}:{action}"


def permission_name_key(code: str) -> str:
    return f"permission.{code}"


def permission_description_key(code: str) -> str:
    return f"permission.description.{code}"


def permission_group_key(group: str) -> str:
    return f"permission.group.{group}"


@dataclass(frozen=True)
class PermissionSeed:
    code: str
    name: str
    type: str
    resource: str
    group_name: str
    description: str
    sort_order: int


@dataclass(frozen=True)
class PagePermissionSpec:
    code: str
    resource: str
    sort_order: int
    read_permission: str | None = None

    def to_seed(self) -> PermissionSeed:
        return PermissionSeed(
            self.code,
            permission_name_key(self.code),
            "route",
            self.resource,
            permission_group_key("page"),
            permission_description_key(self.code),
            self.sort_order,
        )


@dataclass(frozen=True)
class ResourceActionSpec:
    action: str
    order: int


@dataclass(frozen=True)
class ResourcePermissionSpec:
    resource: str
    group: str
    sort_order_base: int
    actions: tuple[ResourceActionSpec, ...]

    def to_seeds(self) -> tuple[PermissionSeed, ...]:
        return tuple(self.to_seed(action) for action in self.actions)

    def to_seed(self, action: ResourceActionSpec) -> PermissionSeed:
        code = action_code(self.resource, action.action)
        return PermissionSeed(
            code,
            permission_name_key(code),
            "action",
            self.resource,
            permission_group_key(self.group),
            permission_description_key(code),
            self.sort_order_base + action.order,
        )


@dataclass(frozen=True)
class AppModule:
    key: str
    version: str = "0.1.0"
    order: int = 0
    dependencies: tuple[str, ...] = ()
    router_paths: tuple[str, ...] = ()
    model_paths: tuple[str, ...] = ()
    page_permissions: tuple[PagePermissionSpec, ...] = ()
    resource_permissions: tuple[ResourcePermissionSpec, ...] = ()
    table_syncs: tuple["TableColumnSync", ...] = ()
    migrations: tuple["MigrationStep", ...] = ()
    lifecycle_hooks: tuple["ModuleLifecycleHook", ...] = ()
    openapi_hidden_tags: tuple[str, ...] = ()
    openapi_hidden_path_prefixes: tuple[str, ...] = ()


@dataclass(frozen=True)
class TableColumnSync:
    table: str
    columns: dict[str, str]


@dataclass(frozen=True)
class MigrationStep:
    key: str
    statements: tuple[str, ...]
    description: str = ""


@dataclass(frozen=True)
class ModuleLifecycleHook:
    event: str
    key: str
    statements: tuple[str, ...]
    description: str = ""


def define_module(module: AppModule) -> AppModule:
    return module


def page_permission(
    page: str,
    resource: str,
    sort_order: int,
    read_permission: str | None = None,
) -> PagePermissionSpec:
    return PagePermissionSpec(route_code(page), resource, sort_order, read_permission)


def resource_permissions(
    resource: str,
    group: str,
    sort_order_base: int,
    actions: tuple[ResourceActionSpec, ...],
) -> ResourcePermissionSpec:
    return ResourcePermissionSpec(resource, group, sort_order_base, actions)


def resource_action(action: str, order: int) -> ResourceActionSpec:
    return ResourceActionSpec(action, order)


def table_column_sync(table: str, columns: dict[str, str]) -> TableColumnSync:
    return TableColumnSync(table, columns)


def migration_step(key: str, statements: tuple[str, ...], description: str = "") -> MigrationStep:
    return MigrationStep(key, statements, description)


def module_lifecycle_hook(
    event: str,
    key: str,
    statements: tuple[str, ...],
    description: str = "",
) -> ModuleLifecycleHook:
    return ModuleLifecycleHook(event, key, statements, description)
