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

export function roleName(role: RoleLike) {
  return translateBuiltin(role.name, translateBuiltin(`role.${role.code}.name`, role.name));
}

export function roleDescription(role: RoleLike) {
  return translateBuiltin(role.description || "", translateBuiltin(`role.${role.code}.description`, role.description || ""));
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
