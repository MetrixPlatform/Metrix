import { download, request } from "./client";
import type { AuditLogItem, PageResult } from "./types";

export interface AuditLogFilters {
  keyword?: string;
  actor_scope?: "self" | "all" | "";
  action?: string;
  target_type?: string;
  sort_order?: "ascend" | "descend";
  start_time?: string;
  end_time?: string;
  page?: number;
  page_size?: number;
}

export function listAuditLogs(filters: AuditLogFilters = {}) {
  return request<PageResult<AuditLogItem>>(`/audit-logs${queryString(filters)}`);
}

export function downloadAuditLogs(filters: AuditLogFilters = {}) {
  const { page, page_size, ...exportFilters } = filters;
  void page;
  void page_size;
  return download(`/audit-logs/export${queryString(exportFilters)}`);
}

function queryString(filters: AuditLogFilters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  });
  return params.size ? `?${params}` : "";
}
