const DEPRECATED_PERMISSION_CODES = new Set(["action:announcement:operate"]);

export function isActivePermissionCode(code: string) {
  return !DEPRECATED_PERMISSION_CODES.has(code);
}
