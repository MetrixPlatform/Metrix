import { post, request } from "./client";
import type { InstallStatus, ServerMessage } from "./types";

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
  admin_phone: string;
  admin_email: string;
  admin_company: string;
  admin_department: string;
}

export interface InstallDatabasePayload {
  database_type: "sqlite" | "mysql";
  sqlite_path?: string;
  mysql?: {
    host: string;
    port: number;
    database: string;
    username: string;
    password: string;
  };
}

export function getInstallStatus() {
  return request<InstallStatus>("/install/status");
}

export function testInstallDatabase(payload: InstallDatabasePayload) {
  return post<ServerMessage>("/install/test-database", payload);
}

export function installSystem(payload: InstallPayload) {
  return post<ServerMessage>("/install", payload);
}
