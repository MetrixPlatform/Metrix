import { t, type I18nKey } from ".";
import { isActivePermissionCode } from "../config/permissions";

interface RoleLike {
  code: string;
  name: string;
  description?: string;
}

interface PermissionLike {
  code: string;
  name: string;
  group_name: string;
}

const roleNameKeys: Record<string, I18nKey> = {
  admin: "role.admin.name",
  user: "role.user.name"
};

const roleDescriptionKeys: Record<string, I18nKey> = {
  admin: "role.admin.description",
  user: "role.user.description"
};

const permissionNameKeys: Record<string, I18nKey> = {
  "route:dashboard": "permission.route:dashboard",
  "route:users": "permission.route:users",
  "route:permissions": "permission.route:permissions",
  "route:announcements": "permission.route:announcements",
  "route:audit_logs": "permission.route:audit_logs",
  "route:settings": "permission.route:settings",
  "route:tokens": "permission.route:tokens",
  "route:api_docs": "permission.route:api_docs",
  "action:user:create": "permission.action:user:create",
  "action:user:read": "permission.action:user:read",
  "action:user:update": "permission.action:user:update",
  "action:user:delete": "permission.action:user:delete",
  "action:user:operate": "permission.action:user:operate",
  "action:role:create": "permission.action:role:create",
  "action:role:read": "permission.action:role:read",
  "action:role:update": "permission.action:role:update",
  "action:role:delete": "permission.action:role:delete",
  "action:role:operate": "permission.action:role:operate",
  "action:announcement:create": "permission.action:announcement:create",
  "action:announcement:read": "permission.action:announcement:read",
  "action:announcement:update": "permission.action:announcement:update",
  "action:announcement:delete": "permission.action:announcement:delete",
  "action:announcement:manage_others": "permission.action:announcement:manage_others",
  "action:audit_log:read": "permission.action:audit_log:read",
  "action:audit_log:manage_others": "permission.action:audit_log:manage_others",
  "action:setting:read": "permission.action:setting:read",
  "action:setting:update": "permission.action:setting:update",
  "action:setting:operate": "permission.action:setting:operate",
  "action:api_token:read": "permission.action:api_token:read",
  "action:api_token:create": "permission.action:api_token:create",
  "action:api_token:delete": "permission.action:api_token:delete",
  "action:api_docs:read": "permission.action:api_docs:read"
};

const permissionGroupKeys: Record<string, I18nKey> = {
  页面: "permission.group.page",
  用户: "permission.group.user",
  角色: "permission.group.role",
  公告: "permission.group.announcement",
  操作日志: "permission.group.auditLog",
  系统设置: "permission.group.setting",
  API: "permission.group.api"
};

export function roleName(role: RoleLike) {
  return roleNameKeys[role.code] ? t(roleNameKeys[role.code]) : role.name;
}

export function roleDescription(role: RoleLike) {
  return roleDescriptionKeys[role.code] ? t(roleDescriptionKeys[role.code]) : role.description || "";
}

export function permissionName(permission: PermissionLike) {
  if (!isActivePermissionCode(permission.code)) {
    return "";
  }
  return permissionNameKeys[permission.code] ? t(permissionNameKeys[permission.code]) : permission.name;
}

export function permissionGroupName(name: string) {
  return permissionGroupKeys[name] ? t(permissionGroupKeys[name]) : name;
}
