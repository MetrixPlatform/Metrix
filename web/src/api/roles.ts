import { del, post, put, request } from "./client";
import type { PermissionItem, RoleItem } from "./types";

export function listRoles() {
  return request<RoleItem[]>("/roles");
}

export function createRole(payload: { code: string; name: string; description: string }) {
  return post<RoleItem>("/roles", payload);
}

export function updateRole(roleId: number, payload: { name: string; description: string }) {
  return put<RoleItem>(`/roles/${roleId}`, payload);
}

export function deleteRole(roleId: number) {
  return del<{ message: string }>(`/roles/${roleId}`);
}

export function listPermissions() {
  return request<PermissionItem[]>("/permissions");
}

export function assignPermissions(roleId: number, permissionIds: number[]) {
  return put<RoleItem>(`/roles/${roleId}/permissions`, { permission_ids: permissionIds });
}
