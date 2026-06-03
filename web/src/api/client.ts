import { authStore } from "../stores/auth";

const API_PREFIX = "/api";
const FIELD_LABELS: Record<string, string> = {
  username: "账号",
  password: "密码",
  old_password: "旧密码",
  new_password: "新密码",
  full_name: "姓名",
  company: "公司",
  department: "部门",
  admin_username: "管理员账号",
  admin_password: "管理员密码",
  admin_full_name: "姓名",
  admin_company: "公司",
  admin_department: "部门",
  database_type: "数据库类型",
  sqlite_path: "SQLite 数据库文件",
  "mysql.host": "MySQL 地址",
  "mysql.port": "端口",
  "mysql.database": "数据库名",
  "mysql.username": "用户名",
  "mysql.password": "密码",
  code: "角色编码",
  name: "角色名称",
  description: "说明",
  reason: "驳回原因",
  role_ids: "角色",
  permission_ids: "权限"
};

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
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function errorMessage(data: Record<string, unknown> | null): string {
  const detail = data?.detail;
  const message = data?.message;
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    const messages = detail.map(formatValidationError).filter(Boolean);
    return messages.length > 0 ? messages.join("；") : "请求参数不正确";
  }
  if (typeof message === "string") {
    return message;
  }
  return "请求失败";
}

function formatValidationError(error: unknown): string {
  if (!isRecord(error)) {
    return "请求参数不正确";
  }
  const label = fieldLabel(error.loc);
  const type = typeof error.type === "string" ? error.type : "";
  const ctx = isRecord(error.ctx) ? error.ctx : {};
  if (type === "missing" || type === "string_too_short") {
    const min = typeof ctx.min_length === "number" ? ctx.min_length : null;
    return min && min > 1 ? `${label}至少 ${min} 个字符` : `请输入${label}`;
  }
  if (type === "string_too_long") {
    const max = typeof ctx.max_length === "number" ? ctx.max_length : null;
    return max ? `${label}不能超过 ${max} 个字符` : `${label}过长`;
  }
  if (type === "greater_than_equal") {
    return typeof ctx.ge === "number" ? `${label}不能小于 ${ctx.ge}` : `${label}过小`;
  }
  if (type === "less_than_equal") {
    return typeof ctx.le === "number" ? `${label}不能大于 ${ctx.le}` : `${label}过大`;
  }
  if (type === "int_parsing" || type === "int_type") {
    return `${label}必须是整数`;
  }
  return `${label}格式不正确`;
}

function fieldLabel(loc: unknown): string {
  if (!Array.isArray(loc)) {
    return "请求参数";
  }
  const parts = loc.filter((item) => typeof item === "string" || typeof item === "number").map(String);
  const keyParts = parts.filter((item) => !["body", "query", "path"].includes(item));
  const key = keyParts.join(".");
  const last = keyParts[keyParts.length - 1];
  return FIELD_LABELS[key] || FIELD_LABELS[last] || key || "请求参数";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
