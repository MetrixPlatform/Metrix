from app.core.module import action_code, route_code
from app.modules.registry import get_page_permission_specs, get_resource_permission_specs


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


PAGE_PERMISSION_SPECS = get_page_permission_specs()

RESOURCE_PERMISSION_SPECS = get_resource_permission_specs()

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
    for route_permission, read_permission in ROUTE_READ_PERMISSIONS.items():
        if route_permission in expanded:
            expanded.add(read_permission)
    return expanded
