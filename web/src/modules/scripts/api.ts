import { del, post, put, queryString, request, upload, type UploadProgress } from "../../api/client";
import type { PageResult, ServerMessage } from "../../api/types";

export type ScriptNetworkMode = "none" | "bridge";
export type ScriptRunStatus = "pending" | "running" | "success" | "failed" | "timeout" | "canceled";
export type ScriptScheduleTrigger = "interval" | "cron";

export interface ScriptProject {
  id: number;
  slug: string;
  name: string;
  description: string;
  language: string;
  base_image: string;
  network_mode: ScriptNetworkMode;
  is_shared: boolean;
  run_command: string;
  env: Record<string, string>;
  cpu_limit: number | null;
  memory_limit_mb: number | null;
  timeout_seconds: number;
  workspace_path: string;
  created_by: number | null;
  created_by_username: string;
  created_at: string;
  updated_at: string;
}

export interface ScriptProjectPayload {
  name: string;
  description: string;
  language: string;
  base_image: string;
  network_mode: ScriptNetworkMode;
  is_shared: boolean;
  run_command: string;
  env: Record<string, string>;
  cpu_limit: number | null;
  memory_limit_mb: number | null;
  timeout_seconds: number;
}

export interface ScriptProjectFilters {
  keyword?: string;
  language?: string;
  network_mode?: string;
  created_by?: "all" | "me" | "";
  sort_order?: "ascend" | "descend";
  page?: number;
  page_size?: number;
}

export interface PresetImage {
  image: string;
  language: string;
  run_command: string;
  use_venv: boolean;
  available: boolean;
}

export interface LocalImage {
  image: string;
}

export interface AvailableImages {
  presets: PresetImage[];
  local_images: LocalImage[];
  docker_available: boolean;
  message: string;
}

export interface ScriptFileEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
  modified_at: string;
}

export interface ScriptFileList {
  path: string;
  entries: ScriptFileEntry[];
}

export interface ScriptFileContent {
  path: string;
  content: string;
  truncated: boolean;
}

export interface ScriptRun {
  id: number;
  run_id: string;
  project_id: number;
  trigger: string;
  schedule_id: number | null;
  status: ScriptRunStatus;
  exit_code: number | null;
  error_code: string;
  created_by: number | null;
  created_by_username: string;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface ScriptRunLog {
  run_id: string;
  status: ScriptRunStatus;
  logs: string;
}

export interface RunSubmitResponse {
  run_id: string;
  status: string;
}

export interface ScriptSchedule {
  id: number;
  project_id: number;
  name: string;
  trigger_type: ScriptScheduleTrigger;
  interval_seconds: number | null;
  cron_expr: string;
  enabled: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface ScriptSchedulePayload {
  name: string;
  trigger_type: ScriptScheduleTrigger;
  interval_seconds: number | null;
  cron_expr: string;
  enabled: boolean;
}

export interface ScriptEnvironmentInfo {
  available: boolean;
  image: string;
  os_type: string;
  architecture: string;
  language: string;
  language_version: string;
  packages: string;
  pip_index_configured: boolean;
  npm_registry_configured: boolean;
  go_proxy_configured: boolean;
  network_mode: string;
  message: string;
}

export function listScripts(filters: ScriptProjectFilters = {}) {
  return request<PageResult<ScriptProject>>(`/scripts${queryString(filters)}`);
}

export function createScript(payload: ScriptProjectPayload) {
  return post<ScriptProject>("/scripts", payload);
}

export function getScript(projectId: number) {
  return request<ScriptProject>(`/scripts/${projectId}`);
}

export function updateScript(projectId: number, payload: ScriptProjectPayload) {
  return put<ScriptProject>(`/scripts/${projectId}`, payload);
}

export function deleteScript(projectId: number) {
  return del<ServerMessage>(`/scripts/${projectId}`);
}

export function listScriptImages() {
  return request<AvailableImages>("/scripts/images");
}

export function getScriptEnvironment(projectId: number) {
  return request<ScriptEnvironmentInfo>(`/scripts/${projectId}/environment`);
}

export function listScriptFiles(projectId: number, path = "/") {
  return request<ScriptFileList>(`/scripts/${projectId}/files${queryString({ path })}`);
}

export function readScriptFile(projectId: number, path: string) {
  return request<ScriptFileContent>(`/scripts/${projectId}/file${queryString({ path })}`);
}

export function writeScriptFile(projectId: number, path: string, content: string) {
  return post<ScriptFileEntry>(`/scripts/${projectId}/file`, { path, content });
}

export function mkdirScript(projectId: number, path: string) {
  return post<ScriptFileEntry>(`/scripts/${projectId}/mkdir`, { path });
}

export function renameScriptEntry(projectId: number, path: string, newName: string) {
  return post<ScriptFileEntry>(`/scripts/${projectId}/rename`, { path, new_name: newName });
}

export function deleteScriptEntry(projectId: number, path: string) {
  return del<ServerMessage>(`/scripts/${projectId}/files${queryString({ path })}`);
}

export function uploadScriptFile(
  projectId: number,
  path: string,
  file: File,
  onProgress?: (progress: UploadProgress) => void,
  signal?: AbortSignal
) {
  const body = new FormData();
  body.append("file", file);
  return upload<ScriptFileEntry>(`/scripts/${projectId}/upload${queryString({ path })}`, body, { onProgress, signal });
}

export function submitScriptRun(projectId: number) {
  return post<RunSubmitResponse>(`/scripts/${projectId}/runs`, {});
}

export function listScriptRuns(
  projectId: number,
  filters: { status?: string; trigger?: string; sort_order?: string; page?: number; page_size?: number } = {}
) {
  return request<PageResult<ScriptRun>>(`/scripts/${projectId}/runs${queryString(filters)}`);
}

export function getScriptRun(runId: string) {
  return request<ScriptRun>(`/scripts/runs/${runId}`);
}

export function getScriptRunLog(runId: string) {
  return request<ScriptRunLog>(`/scripts/runs/${runId}/log`);
}

export function cancelScriptRun(runId: string) {
  return post<ScriptRun>(`/scripts/runs/${runId}/cancel`, {});
}

export function listScriptSchedules(projectId: number) {
  return request<ScriptSchedule[]>(`/scripts/${projectId}/schedules`);
}

export function createScriptSchedule(projectId: number, payload: ScriptSchedulePayload) {
  return post<ScriptSchedule>(`/scripts/${projectId}/schedules`, payload);
}

export function updateScriptSchedule(scheduleId: number, payload: ScriptSchedulePayload) {
  return put<ScriptSchedule>(`/scripts/schedules/${scheduleId}`, payload);
}

export function deleteScriptSchedule(scheduleId: number) {
  return del<ServerMessage>(`/scripts/schedules/${scheduleId}`);
}
