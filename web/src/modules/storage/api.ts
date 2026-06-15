import { del, download, post, put, queryString, request, upload, type UploadProgress } from "../../api/client";
import type { PageResult, ServerMessage } from "../../api/types";

export type StorageProtocol = "ftp" | "sftp";

export interface StorageConnection {
  id: number;
  storage_id: string;
  name: string;
  protocol: StorageProtocol;
  host: string;
  port: number;
  username: string;
  base_path: string;
  is_shared: boolean;
  is_active: boolean;
  created_by: number | null;
  created_by_username: string;
  created_at: string;
  updated_at: string;
}

export interface StorageConnectionPayload {
  name: string;
  storage_id: string;
  protocol: StorageProtocol;
  host: string;
  port: number;
  username: string;
  password: string;
  base_path: string;
  is_shared: boolean;
  is_active: boolean;
}

export interface StorageTestPayload {
  id?: number | null;
  protocol: StorageProtocol;
  host: string;
  port: number;
  username: string;
  password: string;
  base_path: string;
}

export interface StorageConnectionFilters {
  keyword?: string;
  protocol?: StorageProtocol | "";
  shared?: "shared" | "private" | "";
  is_active?: boolean | null;
  created_by?: "all" | "me" | "";
  sort_order?: "ascend" | "descend";
  page?: number;
  page_size?: number;
}

export interface StorageEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
  modified_at: string;
}

export interface StorageFileList {
  path: string;
  entries: StorageEntry[];
  truncated: boolean;
}

export function listStorages(filters: StorageConnectionFilters = {}) {
  return request<PageResult<StorageConnection>>(`/storages${queryString(filters)}`);
}

export function createStorage(payload: StorageConnectionPayload) {
  return post<StorageConnection>("/storages", payload);
}

export function updateStorage(connectionId: number, payload: StorageConnectionPayload) {
  return put<StorageConnection>(`/storages/${connectionId}`, payload);
}

export function deleteStorage(connectionId: number) {
  return del<ServerMessage>(`/storages/${connectionId}`);
}

export function testStorage(payload: StorageTestPayload) {
  return post<ServerMessage>("/storages/test", payload);
}

export function listStorageFiles(storageId: string, path: string, keyword = "", recursive = false) {
  return request<StorageFileList>(
    `/storages/${encodeURIComponent(storageId)}/files${queryString({ path, keyword, recursive: recursive || "" })}`
  );
}

export function downloadStorageFile(storageId: string, path: string) {
  return download(`/storages/${encodeURIComponent(storageId)}/download${queryString({ path })}`);
}

export function downloadStorageArchive(storageId: string, path: string) {
  return download(`/storages/${encodeURIComponent(storageId)}/download-archive${queryString({ path })}`);
}

export function uploadStorageFile(storageId: string, path: string, file: File, onProgress?: (progress: UploadProgress) => void) {
  const body = new FormData();
  body.append("file", file);
  return upload<StorageEntry>(`/storages/${encodeURIComponent(storageId)}/upload${queryString({ path })}`, body, onProgress);
}

export function mkdirStorage(storageId: string, path: string) {
  return post<StorageEntry>(`/storages/${encodeURIComponent(storageId)}/mkdir`, { path });
}

export function renameStorageEntry(storageId: string, path: string, newName: string) {
  return post<StorageEntry>(`/storages/${encodeURIComponent(storageId)}/rename`, { path, new_name: newName });
}

export function deleteStorageEntry(storageId: string, path: string) {
  return del<ServerMessage>(`/storages/${encodeURIComponent(storageId)}/files${queryString({ path })}`);
}
