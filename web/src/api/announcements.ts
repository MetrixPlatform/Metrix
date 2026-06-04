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

export function listPublicAnnouncements() {
  return request<PublicAnnouncementItem[]>("/announcements/public");
}

export function listMyAnnouncements() {
  return request<AnnouncementFeedItem[]>("/announcements/mine");
}

export function markAnnouncementRead(announcementId: number) {
  return post<AnnouncementFeedItem>(`/announcements/${announcementId}/read`);
}

export function listAnnouncements() {
  return request<AnnouncementItem[]>("/announcements");
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
