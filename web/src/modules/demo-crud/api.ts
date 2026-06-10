import { del, post, put, queryString, request } from "../../api/client";
import type { PageResult, ServerMessage } from "../../api/types";

export interface DemoItem {
  id: number;
  name: string;
  category: string;
  description: string;
  is_active: boolean;
  created_by: number | null;
  created_by_username: string;
  created_at: string;
  updated_at: string;
}

export interface DemoItemPayload {
  name: string;
  category: string;
  description: string;
  is_active: boolean;
}

export interface DemoItemFilters {
  keyword?: string;
  category?: string;
  is_active?: boolean | null;
  created_by?: "all" | "me" | "";
  sort_order?: "ascend" | "descend";
  page?: number;
  page_size?: number;
}

export function listDemoItems(filters: DemoItemFilters = {}) {
  return request<PageResult<DemoItem>>(`/demo-items${queryString(filters)}`);
}

export function createDemoItem(payload: DemoItemPayload) {
  return post<DemoItem>("/demo-items", payload);
}

export function updateDemoItem(itemId: number, payload: DemoItemPayload) {
  return put<DemoItem>(`/demo-items/${itemId}`, payload);
}

export function deleteDemoItem(itemId: number) {
  return del<ServerMessage>(`/demo-items/${itemId}`);
}
