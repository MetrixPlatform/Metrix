import { post, put, request } from "./client";
import type { LoginResponse, ServerMessage, UserProfile } from "./types";

export function login(payload: { username: string; password: string }) {
  return post<LoginResponse>("/auth/login", payload);
}

export function register(payload: {
  username: string;
  password: string;
  phone: string;
  email: string;
  company: string;
  department: string;
  full_name: string;
}) {
  return post<ServerMessage>("/auth/register", payload);
}

export function getMe() {
  return request<LoginResponse>("/auth/me");
}

export function logout() {
  return post<ServerMessage>("/auth/logout");
}

export function updateProfile(payload: { full_name: string; phone: string; email: string; company: string; department: string }) {
  return put<UserProfile>("/auth/profile", payload);
}

export function changePassword(payload: { old_password: string; new_password: string }) {
  return post<ServerMessage>("/auth/change-password", payload);
}
