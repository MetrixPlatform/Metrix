import { download, put, request } from "./client";
import type { PublicSettings, SystemSettings } from "./types";

export function getPublicSettings() {
  return request<PublicSettings>("/settings/public");
}

export function getSystemSettings() {
  return request<SystemSettings>("/settings");
}

export function updateSystemSettings(payload: SystemSettings) {
  return put<SystemSettings>("/settings", payload);
}

export function backupData() {
  return download("/settings/backup", { method: "POST" });
}
