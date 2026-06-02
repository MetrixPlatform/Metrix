import { request } from "./client";
import type { DashboardSummary } from "./types";

export function getDashboardSummary() {
  return request<DashboardSummary>("/dashboard/summary");
}
