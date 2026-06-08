import { hasI18nKey, t } from ".";
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

const roleNameKeys: Record<string, string> = {
  admin: "role.admin.name",
  user: "role.user.name"
};

const roleDescriptionKeys: Record<string, string> = {
  admin: "role.admin.description",
  user: "role.user.description"
};

export function roleName(role: RoleLike) {
  return translateBuiltin(roleNameKeys[role.code] || role.name, role.name);
}

export function roleDescription(role: RoleLike) {
  return translateBuiltin(roleDescriptionKeys[role.code] || role.description || "", role.description || "");
}

export function permissionName(permission: PermissionLike) {
  if (!isActivePermissionCode(permission.code)) {
    return "";
  }
  return translateBuiltin(`permission.${permission.code}`, permission.name);
}

export function permissionGroupName(name: string) {
  return translateBuiltin(name, name);
}

function translateBuiltin(key: string, fallback: string) {
  return key && hasI18nKey(key) ? t(key) : fallback;
}
