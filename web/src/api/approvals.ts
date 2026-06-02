import { post, request } from "./client";
import type { UserListItem } from "./types";

export function listPendingUsers() {
  return request<UserListItem[]>("/approvals/users");
}

export function approveUser(userId: number, roleIds: number[]) {
  return post<UserListItem>(`/approvals/users/${userId}/approve`, { role_ids: roleIds });
}

export function rejectUser(userId: number, reason: string) {
  return post<UserListItem>(`/approvals/users/${userId}/reject`, { reason });
}
