import { del, download, post, put, queryString, request, upload, type UploadProgress } from "../../api/client";
import type { PageResult, ServerMessage } from "../../api/types";

export interface ContainerEngineStatus {
  available: boolean;
  message: string;
  version: string;
  os_type: string;
  architecture: string;
  docker_host: string;
  containers: number;
  images: number;
}

export interface ContainerItem {
  id: string;
  short_id: string;
  name: string;
  image: string;
  status: string;
  state: string;
  ports: string[];
  labels: Record<string, string>;
  created_at: string;
  owner_user_id: number | null;
  owner_username: string;
  cpu_percent: number | null;
  memory_usage: number | null;
  memory_limit: number | null;
}

export interface ContainerLogClearResult {
  cleared: boolean;
  restarted: boolean;
  requires_restart: boolean;
}

export interface ImageItem {
  id: string;
  short_id: string;
  repo_tags: string[];
  size: number;
  created_at: string;
  labels: Record<string, string>;
  owner_user_id: number | null;
  owner_username: string;
  is_public: boolean;
  source: string;
}

export interface ContainerPortMapping {
  container_port: string;
  host_port: number | null;
  protocol: "tcp" | "udp";
}

export interface ContainerVolumeMapping {
  container_path: string;
  volume_name: string;
  read_only: boolean;
}

export interface ContainerCreatePayload {
  name: string;
  image: string;
  command: string;
  env: Record<string, string>;
  ports: ContainerPortMapping[];
  volumes: ContainerVolumeMapping[];
  restart_policy: "no" | "always" | "unless-stopped" | "on-failure";
  memory_limit_mb: number | null;
  cpu_limit: number | null;
  auto_start: boolean;
}

export interface ContainerLogsResponse {
  logs: string;
}

export interface JobSubmitResponse {
  job_id: string;
  status: string;
}

export interface ContainerJobItem {
  job_id: string;
  kind: "import" | "export" | string;
  image_ref: string;
  status: "pending" | "running" | "success" | "failed" | string;
  file_name: string;
  file_size: number;
  error_code: string;
  created_by: number | null;
  created_by_username: string;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface ContainerFilters {
  keyword?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export interface ImageFilters {
  keyword?: string;
  page?: number;
  page_size?: number;
}

export interface JobFilters {
  keyword?: string;
  kind?: string;
  status?: string;
  sort_order?: "ascend" | "descend";
  page?: number;
  page_size?: number;
}

export function getContainerEngineStatus() {
  return request<ContainerEngineStatus>("/container-engine/status");
}

export function listContainers(filters: ContainerFilters = {}) {
  return request<PageResult<ContainerItem>>(`/container-instances${queryString(filters)}`);
}

export function createContainer(payload: ContainerCreatePayload) {
  return post<ContainerItem>("/container-instances", payload);
}

export function startContainer(containerId: string) {
  return post<ServerMessage>(`/container-instances/${encodeURIComponent(containerId)}/start`);
}

export function stopContainer(containerId: string) {
  return post<ServerMessage>(`/container-instances/${encodeURIComponent(containerId)}/stop`);
}

export function restartContainer(containerId: string) {
  return post<ServerMessage>(`/container-instances/${encodeURIComponent(containerId)}/restart`);
}

export function deleteContainer(containerId: string, force = false) {
  return del<ServerMessage>(`/container-instances/${encodeURIComponent(containerId)}${queryString({ force: force || "" })}`);
}

export function getContainerLogs(containerId: string, tail = 200) {
  return request<ContainerLogsResponse>(`/container-instances/${encodeURIComponent(containerId)}/logs${queryString({ tail })}`);
}

export function clearContainerLogs(containerId: string, restart = false) {
  return post<ContainerLogClearResult>(`/container-instances/${encodeURIComponent(containerId)}/clear-logs${queryString({ restart: restart || "" })}`);
}

export function listImages(filters: ImageFilters = {}) {
  return request<PageResult<ImageItem>>(`/container-images${queryString(filters)}`);
}

export function importImage(file: File, onProgress?: (progress: UploadProgress) => void) {
  const body = new FormData();
  body.append("file", file);
  return upload<JobSubmitResponse>("/container-images/import", body, onProgress);
}

export function exportImage(imageRef: string) {
  return post<JobSubmitResponse>(`/container-images/${encodeURIComponent(imageRef)}/export`);
}

export function deleteImage(imageRef: string) {
  return del<ServerMessage>(`/container-images/${encodeURIComponent(imageRef)}`);
}

export function updateImageVisibility(imageRef: string, isPublic: boolean) {
  return put<ImageItem>(`/container-images/${encodeURIComponent(imageRef)}/visibility`, { is_public: isPublic });
}

export function listContainerJobs(filters: JobFilters = {}) {
  return request<PageResult<ContainerJobItem>>(`/container-jobs${queryString(filters)}`);
}

export function downloadContainerJob(jobId: string) {
  return download(`/container-jobs/${encodeURIComponent(jobId)}/download`);
}
