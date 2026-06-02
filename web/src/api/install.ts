import { post, request } from "./client";
import type { InstallStatus } from "./types";

export interface InstallPayload {
  database_type: "sqlite" | "mysql";
  sqlite_path?: string;
  mysql?: {
    host: string;
    port: number;
    database: string;
    username: string;
    password: string;
  };
  admin_username: string;
  admin_password: string;
  admin_full_name: string;
  admin_company: string;
  admin_department: string;
}

export function getInstallStatus() {
  return request<InstallStatus>("/install/status");
}

export function installSystem(payload: InstallPayload) {
  return post<{ message: string }>("/install", payload);
}
