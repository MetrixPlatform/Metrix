import { post, put, request } from "./client";
import type { LoginResponse, UserProfile } from "./types";

export function login(payload: { username: string; password: string }) {
  return post<LoginResponse>("/auth/login", payload);
}

export function register(payload: {
  username: string;
  password: string;
  company: string;
  department: string;
  full_name: string;
}) {
  return post<{ message: string }>("/auth/register", payload);
}

export function getMe() {
  return request<LoginResponse>("/auth/me");
}

export function logout() {
  return post<{ message: string }>("/auth/logout");
}

export function updateProfile(payload: { company: string; department: string; full_name: string }) {
  return put<UserProfile>("/auth/profile", payload);
}

export function changePassword(payload: { old_password: string; new_password: string }) {
  return post<{ message: string }>("/auth/change-password", payload);
}
