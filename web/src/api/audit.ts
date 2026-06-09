import { queryString, request } from "./client";
import type { AuditLogItem, PageResult } from "./types";

export interface AuditLogFilters {
  keyword?: string;
  actor_scope?: "self" | "all" | "";
  action?: string;
  target_type?: string;
  source?: string;
  sort_order?: "ascend" | "descend";
  start_time?: string;
  end_time?: string;
  page?: number;
  page_size?: number;
}

export function listAuditLogs(filters: AuditLogFilters = {}) {
  return request<PageResult<AuditLogItem>>(`/audit-logs${queryString(filters)}`);
}
