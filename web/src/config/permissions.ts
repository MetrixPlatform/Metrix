const DEPRECATED_PERMISSION_CODES = new Set(["route:approvals", "action:announcement:operate"]);

export function isActivePermissionCode(code: string) {
  return !DEPRECATED_PERMISSION_CODES.has(code);
}
