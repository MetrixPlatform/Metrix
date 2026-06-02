import { authStore } from "../stores/auth";

const API_PREFIX = "/api";

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (authStore.token) {
    headers.set("Authorization", `Bearer ${authStore.token}`);
  }

  const response = await fetch(`${API_PREFIX}${path}`, {
    ...options,
    headers
  });
  const data = await parseJson(response);
  if (!response.ok) {
    if (response.status === 401) {
      authStore.clear();
    }
    throw new Error(errorMessage(data));
  }
  return data as T;
}

export function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body: JSON.stringify(body ?? {}) });
}

export function put<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: "PUT", body: JSON.stringify(body ?? {}) });
}

export function del<T>(path: string): Promise<T> {
  return request<T>(path, { method: "DELETE" });
}

async function parseJson(response: Response): Promise<Record<string, unknown> | null> {
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

function errorMessage(data: Record<string, unknown> | null): string {
  const detail = data?.detail;
  const message = data?.message;
  if (typeof detail === "string") {
    return detail;
  }
  if (typeof message === "string") {
    return message;
  }
  return "请求失败";
}
