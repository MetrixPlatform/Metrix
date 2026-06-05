import { t, type I18nKey } from ".";

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
  "action:announcement:manage_others": "permission.action:announcement:manage_others"
};

const permissionGroupKeys: Record<string, I18nKey> = {
  页面: "permission.group.page",
  用户: "permission.group.user",
  角色: "permission.group.role",
  公告: "permission.group.announcement"
};

export function roleName(role: RoleLike) {
  return roleNameKeys[role.code] ? t(roleNameKeys[role.code]) : role.name;
}

export function roleDescription(role: RoleLike) {
  return roleDescriptionKeys[role.code] ? t(roleDescriptionKeys[role.code]) : role.description || "";
}

export function permissionName(permission: PermissionLike) {
  return permissionNameKeys[permission.code] ? t(permissionNameKeys[permission.code]) : permission.name;
}

export function permissionGroupName(name: string) {
  return permissionGroupKeys[name] ? t(permissionGroupKeys[name]) : name;
}
