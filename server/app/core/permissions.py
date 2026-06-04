from dataclasses import dataclass


def route_code(page: str) -> str:
    return f"route:{page}"


def action_code(resource: str, action: str) -> str:
    return f"action:{resource}:{action}"


ROUTE_DASHBOARD = route_code("dashboard")
ROUTE_USERS = route_code("users")
ROUTE_PERMISSIONS = route_code("permissions")

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

ADMIN_ROLE = "admin"
USER_ROLE = "user"

DEPRECATED_PERMISSION_CODES = {"route:approvals"}


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
    name: str
    resource: str
    description: str
    sort_order: int
    read_permission: str | None = None

    def to_seed(self) -> PermissionSeed:
        return PermissionSeed(self.code, self.name, "route", self.resource, "页面", self.description, self.sort_order)


@dataclass(frozen=True)
class ResourceActionSpec:
    action: str
    name: str
    description: str
    order: int


@dataclass(frozen=True)
class ResourcePermissionSpec:
    resource: str
    group_name: str
    sort_order_base: int
    actions: tuple[ResourceActionSpec, ...]

    def to_seeds(self) -> tuple[PermissionSeed, ...]:
        return tuple(
            PermissionSeed(
                action_code(self.resource, action.action),
                action.name,
                "action",
                self.resource,
                self.group_name,
                action.description,
                self.sort_order_base + action.order,
            )
            for action in self.actions
        )


PAGE_PERMISSION_SPECS = (
    PagePermissionSpec(ROUTE_DASHBOARD, "首页", "dashboard", "访问首页", 10),
    PagePermissionSpec(ROUTE_USERS, "用户管理", "user", "访问用户管理", 20, USER_READ),
    PagePermissionSpec(ROUTE_PERMISSIONS, "权限管理", "role", "访问权限管理", 40, ROLE_READ),
)

RESOURCE_PERMISSION_SPECS = (
    ResourcePermissionSpec(
        "user",
        "用户",
        100,
        (
            ResourceActionSpec("create", "新增用户", "创建用户", 10),
            ResourceActionSpec("read", "查询用户", "查询用户", 20),
            ResourceActionSpec("update", "修改用户", "修改用户", 30),
            ResourceActionSpec("delete", "删除用户", "删除用户", 40),
            ResourceActionSpec("operate", "操作用户", "审核、启用、禁用、重置密码、分配角色", 50),
        ),
    ),
    ResourcePermissionSpec(
        "role",
        "角色",
        200,
        (
            ResourceActionSpec("create", "新增角色", "创建角色", 10),
            ResourceActionSpec("read", "查询角色", "查询角色和权限字典", 20),
            ResourceActionSpec("update", "修改角色", "修改角色", 30),
            ResourceActionSpec("delete", "删除角色", "删除角色", 40),
            ResourceActionSpec("operate", "操作角色", "分配权限", 50),
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
