import { reactive } from "vue";

import type { UserProfile } from "../api/types";

const TOKEN_KEY = "metrix.token";

export const authStore = reactive({
  token: localStorage.getItem(TOKEN_KEY) || "",
  user: null as UserProfile | null,
  permissions: [] as string[],
  setSession(token: string, user: UserProfile, permissions: string[]) {
    this.token = token || this.token;
    this.user = user;
    this.permissions = permissions;
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    }
  },
  clear() {
    this.token = "";
    this.user = null;
    this.permissions = [];
    localStorage.removeItem(TOKEN_KEY);
  },
  has(permission: string) {
    return this.permissions.includes(permission);
  }
});
