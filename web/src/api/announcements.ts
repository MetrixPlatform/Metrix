import { del, post, put, request } from "./client";
import type { AnnouncementFeedItem, AnnouncementItem, AnnouncementTargetType, PublicAnnouncementItem } from "./types";

export interface AnnouncementPayload {
  title: string;
  content: string;
  target_type: AnnouncementTargetType;
  target_value: string;
  show_popup: boolean;
  show_ticker: boolean;
  show_sidebar: boolean;
  is_active: boolean;
}

export interface AnnouncementFilters {
  keyword?: string;
  target_type?: AnnouncementTargetType | "";
  display_mode?: "popup" | "ticker" | "sidebar" | "";
  is_active?: boolean | null;
  start_time?: string;
  end_time?: string;
}

export function listPublicAnnouncements() {
  return request<PublicAnnouncementItem[]>("/announcements/public");
}

export function listMyAnnouncements() {
  return request<AnnouncementFeedItem[]>("/announcements/mine");
}

export function markAnnouncementRead(announcementId: number) {
  return post<AnnouncementFeedItem>(`/announcements/${announcementId}/read`);
}

export function listAnnouncements(filters: AnnouncementFilters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  });
  return request<AnnouncementItem[]>(`/announcements${params.size ? `?${params}` : ""}`);
}

export function createAnnouncement(payload: AnnouncementPayload) {
  return post<AnnouncementItem>("/announcements", payload);
}

export function updateAnnouncement(announcementId: number, payload: AnnouncementPayload) {
  return put<AnnouncementItem>(`/announcements/${announcementId}`, payload);
}

export function deleteAnnouncement(announcementId: number) {
  return del<{ message: string }>(`/announcements/${announcementId}`);
}

export function batchDeleteAnnouncements(ids: number[]) {
  return post<{ message: string }>("/announcements/batch-delete", { ids });
}
