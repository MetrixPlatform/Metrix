import { del, post, request } from "./client";
import type { ApiTokenCreateResponse, ApiTokenItem, ServerMessage } from "./types";

export interface ApiTokenCreatePayload {
  name: string;
  expires_at: string | null;
}

export function listApiTokens() {
  return request<ApiTokenItem[]>("/tokens");
}

export function createApiToken(payload: ApiTokenCreatePayload) {
  return post<ApiTokenCreateResponse>("/tokens", payload);
}

export function getApiTokenSecret(id: number) {
  return request<{ token: string }>(`/tokens/${id}/secret`);
}

export function deleteApiToken(id: number) {
  return del<ServerMessage>(`/tokens/${id}`);
}
