import { reactive } from "vue";

import { listMyAnnouncements, markAnnouncementRead } from "../api/announcements";
import type { AnnouncementFeedItem } from "../api/types";

export const announcementStore = reactive({
  items: [] as AnnouncementFeedItem[],
  loading: false,
  async load() {
    this.loading = true;
    try {
      this.items = await listMyAnnouncements();
    } finally {
      this.loading = false;
    }
  },
  async markRead(announcementId: number) {
    const updated = await markAnnouncementRead(announcementId);
    this.items = this.items.map((item) => (item.id === announcementId ? updated : item));
  },
  clear() {
    this.items = [];
    this.loading = false;
  }
});
