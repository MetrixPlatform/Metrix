from dataclasses import dataclass


ROUTE_DASHBOARD = "route:dashboard"
ROUTE_USERS = "route:users"
ROUTE_APPROVALS = "route:approvals"
ROUTE_PERMISSIONS = "route:permissions"

USER_CREATE = "action:user:create"
USER_READ = "action:user:read"
USER_UPDATE = "action:user:update"
USER_DELETE = "action:user:delete"
USER_OPERATE = "action:user:operate"

ROLE_CREATE = "action:role:create"
ROLE_READ = "action:role:read"
ROLE_UPDATE = "action:role:update"
ROLE_DELETE = "action:role:delete"
ROLE_OPERATE = "action:role:operate"

ADMIN_ROLE = "admin"
USER_ROLE = "user"

ROUTE_READ_PERMISSIONS = {
    ROUTE_USERS: USER_READ,
    ROUTE_APPROVALS: USER_READ,
    ROUTE_PERMISSIONS: ROLE_READ,
}


@dataclass(frozen=True)
class PermissionSeed:
    code: str
    name: str
    type: str
    resource: str
    group_name: str
    description: str
    sort_order: int


PERMISSION_SEEDS = [
    PermissionSeed(ROUTE_DASHBOARD, "首页", "route", "dashboard", "页面", "访问首页", 10),
    PermissionSeed(ROUTE_USERS, "用户管理", "route", "user", "页面", "访问用户管理", 20),
    PermissionSeed(ROUTE_APPROVALS, "注册审批", "route", "user", "页面", "访问注册审批", 30),
    PermissionSeed(ROUTE_PERMISSIONS, "权限管理", "route", "role", "页面", "访问权限管理", 40),
    PermissionSeed(USER_CREATE, "新增用户", "action", "user", "用户", "创建用户", 110),
    PermissionSeed(USER_READ, "查询用户", "action", "user", "用户", "查询用户", 120),
    PermissionSeed(USER_UPDATE, "修改用户", "action", "user", "用户", "修改用户", 130),
    PermissionSeed(USER_DELETE, "删除用户", "action", "user", "用户", "删除用户", 140),
    PermissionSeed(USER_OPERATE, "操作用户", "action", "user", "用户", "审核、启用、禁用、重置密码、分配角色", 150),
    PermissionSeed(ROLE_CREATE, "新增角色", "action", "role", "角色", "创建角色", 210),
    PermissionSeed(ROLE_READ, "查询角色", "action", "role", "角色", "查询角色和权限字典", 220),
    PermissionSeed(ROLE_UPDATE, "修改角色", "action", "role", "角色", "修改角色", 230),
    PermissionSeed(ROLE_DELETE, "删除角色", "action", "role", "角色", "删除角色", 240),
    PermissionSeed(ROLE_OPERATE, "操作角色", "action", "role", "角色", "分配权限", 250),
]


def expand_permissions(codes: set[str]) -> set[str]:
    expanded = set(codes)
    for route_code, read_code in ROUTE_READ_PERMISSIONS.items():
        if route_code in expanded:
            expanded.add(read_code)
    return expanded
