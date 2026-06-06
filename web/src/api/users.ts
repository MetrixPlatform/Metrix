import { del, post, put, queryString, request } from "./client";
import type { PageResult, RoleBrief, ServerMessage, UserListItem } from "./types";

export interface UserPayload {
  username?: string;
  password?: string;
  full_name: string;
  phone: string;
  email: string;
  company: string;
  department: string;
  role_ids?: number[];
}

export interface UserFilters {
  keyword?: string;
  approval_status?: string;
  is_active?: boolean | null;
  start_time?: string;
  end_time?: string;
  sort_order?: "ascend" | "descend";
  page?: number;
  page_size?: number;
}

export function listUsers(filters: UserFilters = {}) {
  return request<PageResult<UserListItem>>(`/users${queryString(filters)}`);
}

export function listUserRoleOptions() {
  return request<RoleBrief[]>("/users/role-options");
}

export function createUser(payload: UserPayload) {
  return post<UserListItem>("/users", payload);
}

export function updateUser(userId: number, payload: UserPayload) {
  return put<UserListItem>(`/users/${userId}`, payload);
}

export function deleteUser(userId: number) {
  return del<ServerMessage>(`/users/${userId}`);
}

export function enableUser(userId: number) {
  return post<UserListItem>(`/users/${userId}/enable`);
}

export function disableUser(userId: number) {
  return post<UserListItem>(`/users/${userId}/disable`);
}

export function resetPassword(userId: number, password: string) {
  return post<ServerMessage>(`/users/${userId}/reset-password`, { password });
}

export function assignRoles(userId: number, roleIds: number[]) {
  return put<UserListItem>(`/users/${userId}/roles`, { role_ids: roleIds });
}

export function approveUser(userId: number, roleIds: number[]) {
  return post<UserListItem>(`/users/${userId}/approve`, { role_ids: roleIds });
}

export function rejectUser(userId: number, reason: string) {
  return post<UserListItem>(`/users/${userId}/reject`, { reason });
}
