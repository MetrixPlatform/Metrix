from dataclasses import dataclass


def route_code(page: str) -> str:
    return f"route:{page}"


def action_code(resource: str, action: str) -> str:
    return f"action:{resource}:{action}"


ROUTE_DASHBOARD = route_code("dashboard")
ROUTE_USERS = route_code("users")
ROUTE_PERMISSIONS = route_code("permissions")
ROUTE_ANNOUNCEMENTS = route_code("announcements")
ROUTE_AUDIT_LOGS = route_code("audit_logs")
ROUTE_SETTINGS = route_code("settings")
ROUTE_TOKENS = route_code("tokens")
ROUTE_API_DOCS = route_code("api_docs")

USER_CREATE = action_code("user", "create")
USER_READ = action_code("user", "read")
USER_UPDATE = action_code("user", "update")
USER_DELETE = action_code("user", "delete")
USER_OPERATE = action_code("user", "operate")

ROLE_CREATE = action_code("role", "create")
ROLE_READ = action_code("role", "read")
ROLE_UPDATE = action_code("role", "update")
ROLE_DELETE = action_code("role", "delete")
ROLE_OPERATE = action_code("role", "operate")

ANNOUNCEMENT_CREATE = action_code("announcement", "create")
ANNOUNCEMENT_READ = action_code("announcement", "read")
ANNOUNCEMENT_UPDATE = action_code("announcement", "update")
ANNOUNCEMENT_DELETE = action_code("announcement", "delete")
ANNOUNCEMENT_MANAGE_OTHERS = action_code("announcement", "manage_others")

AUDIT_LOG_READ = action_code("audit_log", "read")
AUDIT_LOG_MANAGE_OTHERS = action_code("audit_log", "manage_others")

SETTING_READ = action_code("setting", "read")
SETTING_UPDATE = action_code("setting", "update")
SETTING_OPERATE = action_code("setting", "operate")

API_TOKEN_READ = action_code("api_token", "read")
API_TOKEN_CREATE = action_code("api_token", "create")
API_TOKEN_DELETE = action_code("api_token", "delete")
API_DOCS_READ = action_code("api_docs", "read")

ADMIN_ROLE = "admin"
USER_ROLE = "user"

DEPRECATED_PERMISSION_CODES = {"route:approvals", "action:announcement:operate"}


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


def permission_name_key(code: str) -> str:
    return f"permission.{code}"


def permission_description_key(code: str) -> str:
    return f"permission.description.{code}"


def permission_group_key(group: str) -> str:
    return f"permission.group.{group}"


PAGE_PERMISSION_SPECS = (
    PagePermissionSpec(ROUTE_DASHBOARD, "dashboard", 10),
    PagePermissionSpec(ROUTE_USERS, "user", 20, USER_READ),
    PagePermissionSpec(ROUTE_PERMISSIONS, "role", 30, ROLE_READ),
    PagePermissionSpec(ROUTE_ANNOUNCEMENTS, "announcement", 40, ANNOUNCEMENT_READ),
    PagePermissionSpec(ROUTE_AUDIT_LOGS, "audit_log", 50, AUDIT_LOG_READ),
    PagePermissionSpec(ROUTE_SETTINGS, "setting", 60, SETTING_READ),
    PagePermissionSpec(ROUTE_TOKENS, "api_token", 70, API_TOKEN_READ),
    PagePermissionSpec(ROUTE_API_DOCS, "api_docs", 80, API_DOCS_READ),
)

RESOURCE_PERMISSION_SPECS = (
    ResourcePermissionSpec(
        "user",
        "user",
        100,
        (
            ResourceActionSpec("create", 10),
            ResourceActionSpec("read", 20),
            ResourceActionSpec("update", 30),
            ResourceActionSpec("delete", 40),
            ResourceActionSpec("operate", 50),
        ),
    ),
    ResourcePermissionSpec(
        "role",
        "role",
        200,
        (
            ResourceActionSpec("create", 10),
            ResourceActionSpec("read", 20),
            ResourceActionSpec("update", 30),
            ResourceActionSpec("delete", 40),
            ResourceActionSpec("operate", 50),
        ),
    ),
    ResourcePermissionSpec(
        "announcement",
        "announcement",
        300,
        (
            ResourceActionSpec("create", 10),
            ResourceActionSpec("read", 20),
            ResourceActionSpec("update", 30),
            ResourceActionSpec("delete", 40),
            ResourceActionSpec("manage_others", 50),
        ),
    ),
    ResourcePermissionSpec(
        "audit_log",
        "auditLog",
        400,
        (
            ResourceActionSpec("read", 20),
            ResourceActionSpec("manage_others", 50),
        ),
    ),
    ResourcePermissionSpec(
        "setting",
        "setting",
        500,
        (
            ResourceActionSpec("read", 20),
            ResourceActionSpec("update", 30),
            ResourceActionSpec("operate", 50),
        ),
    ),
    ResourcePermissionSpec(
        "api_token",
        "api",
        600,
        (
            ResourceActionSpec("read", 20),
            ResourceActionSpec("create", 30),
            ResourceActionSpec("delete", 40),
        ),
    ),
    ResourcePermissionSpec(
        "api_docs",
        "api",
        700,
        (
            ResourceActionSpec("read", 20),
        ),
    ),
)

ROUTE_READ_PERMISSIONS = {
    spec.code: spec.read_permission
    for spec in PAGE_PERMISSION_SPECS
    if spec.read_permission
}

PERMISSION_SEEDS = (
    *(spec.to_seed() for spec in PAGE_PERMISSION_SPECS),
    *(seed for spec in RESOURCE_PERMISSION_SPECS for seed in spec.to_seeds()),
)


def expand_permissions(codes: set[str]) -> set[str]:
    expanded = set(codes)
    for route_code, read_code in ROUTE_READ_PERMISSIONS.items():
        if route_code in expanded:
            expanded.add(read_code)
    return expanded
