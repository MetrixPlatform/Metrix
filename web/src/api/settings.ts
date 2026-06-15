import { download, put, request } from "./client";
import type { PublicSettings, SystemSettings } from "./types";

type SystemSettingsUpdate = Omit<SystemSettings, "data_job_retention_days"> & {
  data_job_retention_days?: number;
};

export function getPublicSettings() {
  return request<PublicSettings>("/settings/public");
}

export function getSystemSettings() {
  return request<SystemSettings>("/settings");
}

export function updateSystemSettings(payload: SystemSettingsUpdate) {
  return put<SystemSettings>("/settings", payload);
}

export function backupData() {
  return download("/settings/backup", { method: "POST" });
}
