from app.core.module import action_code
from app.modules.registry import get_resource_permission_specs


DASHBOARD_READ = action_code("dashboard", "read")

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

# route:* 页面权限已退役（页面/导航改由资源的查询权限充当网关）；历史 route:* 行由
# db/init.py 的清理逻辑删除，这里只保留非 route 的废弃 code。
DEPRECATED_PERMISSION_CODES = {"action:announcement:operate"}

RESOURCE_PERMISSION_SPECS = get_resource_permission_specs()

PERMISSION_SEEDS = tuple(seed for spec in RESOURCE_PERMISSION_SPECS for seed in spec.to_seeds())


def expand_permissions(codes: set[str]) -> set[str]:
    # 页面/导航由资源的查询(read)权限充当网关：持有某资源的任意操作权限
    # （action:<resource>:<verb>）即视为可访问该资源对应页面，自动补齐其 read 权限，
    # 因此授予了能力后无需再单独勾选页面权限。
    expanded = set(codes)
    for code in codes:
        if not code.startswith("action:"):
            continue
        parts = code.split(":", 2)
        if len(parts) == 3:
            expanded.add(action_code(parts[1], "read"))
    return expanded
