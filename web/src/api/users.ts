import { del, post, put, request } from "./client";
import type { UserListItem } from "./types";

export interface UserPayload {
  username?: string;
  password?: string;
  full_name: string;
  company: string;
  department: string;
  role_ids?: number[];
}

export interface UserFilters {
  keyword?: string;
  approval_status?: string;
  is_active?: boolean | null;
}

export function listUsers(filters: UserFilters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  });
  return request<UserListItem[]>(`/users${params.size ? `?${params}` : ""}`);
}

export function createUser(payload: UserPayload) {
  return post<UserListItem>("/users", payload);
}

export function updateUser(userId: number, payload: UserPayload) {
  return put<UserListItem>(`/users/${userId}`, payload);
}

export function deleteUser(userId: number) {
  return del<{ message: string }>(`/users/${userId}`);
}

export function enableUser(userId: number) {
  return post<UserListItem>(`/users/${userId}/enable`);
}

export function disableUser(userId: number) {
  return post<UserListItem>(`/users/${userId}/disable`);
}

export function resetPassword(userId: number, password: string) {
  return post<{ message: string }>(`/users/${userId}/reset-password`, { password });
}

export function assignRoles(userId: number, roleIds: number[]) {
  return put<UserListItem>(`/users/${userId}/roles`, { role_ids: roleIds });
}
