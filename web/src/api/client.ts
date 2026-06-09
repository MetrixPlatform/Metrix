import { authStore } from "../stores/auth";
import { appKey } from "../config/app";
import { hasI18nKey, t, translateMessage, type I18nKey, type TranslateParams } from "../i18n";

const API_PREFIX = "/api";
export const AUTH_EXPIRED_EVENT = appKey("auth-expired");
const FIELD_LABEL_KEYS: Record<string, I18nKey> = {
  username: "field.username",
  password: "field.password",
  old_password: "field.oldPassword",
  new_password: "field.newPassword",
  full_name: "field.fullName",
  phone: "field.phone",
  email: "field.email",
  company: "field.company",
  department: "field.department",
  admin_username: "field.adminUsername",
  admin_password: "field.adminPassword",
  admin_full_name: "field.adminFullName",
  admin_phone: "field.adminPhone",
  admin_email: "field.adminEmail",
  admin_company: "field.adminCompany",
  admin_department: "field.adminDepartment",
  database_type: "field.databaseType",
  sqlite_path: "field.sqlitePath",
  "mysql.host": "field.mysqlHost",
  "mysql.port": "field.mysqlPort",
  "mysql.database": "field.mysqlDatabase",
  "mysql.username": "field.mysqlUsername",
  "mysql.password": "field.mysqlPassword",
  code: "field.roleCode",
  name: "field.roleName",
  description: "field.description",
  reason: "field.reason",
  role_ids: "field.roles",
  permission_ids: "field.roles",
  title: "field.title",
  content: "field.content",
  target_type: "field.targetType",
  target_value: "field.targetValue",
  expires_at: "field.expiresAt"
};

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await rawRequest(path, options);
  const data = await parseJson(response);
  if (!response.ok) {
    handleUnauthorized(response);
    throw new Error(errorMessage(data));
  }
  return data as T;
}

export async function download(path: string, options: RequestInit = {}): Promise<Blob> {
  const response = await rawRequest(path, options);
  if (!response.ok) {
    handleUnauthorized(response);
    throw new Error(errorMessage(await parseJson(response)));
  }
  return response.blob();
}

async function rawRequest(path: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (authStore.token) {
    headers.set("Authorization", `Bearer ${authStore.token}`);
  }

  return fetch(`${API_PREFIX}${path}`, {
    ...options,
    headers
  });
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

export function queryString(filters: object = {}, ignoredKeys: string[] = []) {
  const ignored = new Set(ignoredKeys);
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (ignored.has(key) || value === undefined || value === null || value === "") {
      return;
    }
    if (Array.isArray(value)) {
      value
        .filter((item) => item !== undefined && item !== null && item !== "")
        .forEach((item) => params.append(key, String(item)));
      return;
    }
    params.set(key, String(value));
  });
  return params.size ? `?${params}` : "";
}

async function parseJson(response: Response): Promise<Record<string, unknown> | null> {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function handleUnauthorized(response: Response) {
  if (response.status === 401) {
    authStore.clear();
    window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT));
  }
}

function errorMessage(data: Record<string, unknown> | null): string {
  const detail = data?.detail;
  const message = data?.message;
  if (isServerMessage(detail)) {
    return translateServerMessage(detail);
  }
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    const messages = detail.map(formatValidationError).filter(Boolean);
    return messages.length > 0 ? messages.join(t("common.messageSeparator")) : t("api.invalidParams");
  }
  if (isServerMessage(data)) {
    return translateServerMessage(data);
  }
  if (typeof message === "string") {
    return message;
  }
  return t("api.requestFailed");
}

function formatValidationError(error: unknown): string {
  if (!isRecord(error)) {
    return t("api.invalidParams");
  }
  const label = fieldLabel(error.loc);
  const type = typeof error.type === "string" ? error.type : "";
  const ctx = isRecord(error.ctx) ? error.ctx : {};
  if (hasI18nKey(type)) {
    return t(type, { ...toTranslateParams(ctx), label });
  }
  if (type === "missing" || type === "string_too_short") {
    const min = typeof ctx.min_length === "number" ? ctx.min_length : null;
    return min && min > 1 ? t("validation.minLength", { label, min }) : t("validation.required", { label });
  }
  if (type === "string_too_long") {
    const max = typeof ctx.max_length === "number" ? ctx.max_length : null;
    return max ? t("validation.maxLength", { label, max }) : t("validation.tooLong", { label });
  }
  if (type === "greater_than_equal") {
    return typeof ctx.ge === "number" ? t("validation.minValue", { label, min: ctx.ge }) : t("validation.tooSmall", { label });
  }
  if (type === "less_than_equal") {
    return typeof ctx.le === "number" ? t("validation.maxValue", { label, max: ctx.le }) : t("validation.tooLarge", { label });
  }
  if (type === "int_parsing" || type === "int_type") {
    return t("validation.integer", { label });
  }
  return t("validation.invalidFormat", { label });
}

function translateServerMessage(payload: { code: string; message?: string; params?: Record<string, unknown> }) {
  return translateMessage(payload.code, toTranslateParams(payload.params), payload.message || "");
}

function fieldLabel(loc: unknown): string {
  if (!Array.isArray(loc)) {
    return t("api.requestParam");
  }
  const parts = loc.filter((item) => typeof item === "string" || typeof item === "number").map(String);
  const keyParts = parts.filter((item) => !["body", "query", "path"].includes(item));
  const key = keyParts.join(".");
  const last = keyParts[keyParts.length - 1];
  const labelKey = FIELD_LABEL_KEYS[key] || FIELD_LABEL_KEYS[last];
  return labelKey ? t(labelKey) : key || t("api.requestParam");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isServerMessage(value: unknown): value is { code: string; message?: string; params?: Record<string, unknown> } {
  return isRecord(value) && typeof value.code === "string";
}

function toTranslateParams(value: unknown): TranslateParams {
  if (!isRecord(value)) {
    return {};
  }
  return Object.fromEntries(
    Object.entries(value).filter((entry): entry is [string, string | number | boolean | null] => {
      const item = entry[1];
      return item === null || ["string", "number", "boolean"].includes(typeof item);
    })
  );
}
