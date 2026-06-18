import {
  Board20Regular,
  ClipboardClock20Regular,
  Code20Regular,
  Key20Regular,
  KeyMultiple20Regular,
  MegaphoneLoud20Regular,
  People20Regular,
  PeopleSettings20Regular,
  Settings20Regular
} from "@vicons/fluent";

import { actionPermission, defineMenuGroup, defineModule, definePage } from "../types";

export default defineModule({
  key: "core",
  version: "0.1.0",
  order: 10,
  menuGroups: [
    defineMenuGroup({ key: "system", labelKey: "route.group.system", icon: Settings20Regular, order: 90 })
  ],
  pages: [
    definePage({
      key: "dashboard",
      path: "/",
      titleKey: "route.dashboard",
      component: () => import("../../views/DashboardView.vue"),
      permission: actionPermission("dashboard", "read"),
      fallbackOrder: 10,
      menu: { icon: Board20Regular, order: 10 }
    }),
    definePage({
      key: "users",
      path: "/users",
      titleKey: "route.users",
      component: () => import("../../views/UserManageView.vue"),
      permission: actionPermission("user", "read"),
      fallbackOrder: 20,
      menu: { group: "system", icon: People20Regular, order: 10 }
    }),
    definePage({
      key: "permissions",
      path: "/permissions",
      titleKey: "route.permissions",
      component: () => import("../../views/PermissionView.vue"),
      permission: actionPermission("role", "read"),
      fallbackOrder: 30,
      menu: { group: "system", icon: KeyMultiple20Regular, order: 20 }
    }),
    definePage({
      key: "announcements",
      path: "/announcements",
      titleKey: "route.announcements",
      component: () => import("../../views/AnnouncementManageView.vue"),
      permission: actionPermission("announcement", "read"),
      fallbackOrder: 40,
      menu: { group: "system", icon: MegaphoneLoud20Regular, order: 30 }
    }),
    definePage({
      key: "auditLogs",
      path: "/audit-logs",
      titleKey: "route.auditLogs",
      component: () => import("../../views/AuditLogView.vue"),
      permission: actionPermission("audit_log", "read"),
      fallbackOrder: 50,
      menu: { group: "system", icon: ClipboardClock20Regular, order: 40 }
    }),
    definePage({
      key: "settings",
      path: "/settings",
      titleKey: "route.settings",
      component: () => import("../../views/SystemSettingsView.vue"),
      permission: actionPermission("setting", "read"),
      fallbackOrder: 60,
      menu: { group: "system", icon: PeopleSettings20Regular, order: 90 }
    }),
    definePage({
      key: "tokens",
      path: "/tokens",
      titleKey: "route.tokens",
      component: () => import("../../views/TokenManageView.vue"),
      permission: actionPermission("api_token", "read"),
      feature: "api",
      fallbackOrder: 70,
      menu: { group: "system", icon: Key20Regular, order: 50 }
    }),
    definePage({
      key: "apiDocs",
      path: "/api-docs",
      titleKey: "route.apiDocs",
      component: () => import("../../views/ApiDocsView.vue"),
      permission: actionPermission("api_docs", "read"),
      feature: "api",
      fallbackOrder: 80,
      menu: { group: "system", icon: Code20Regular, order: 60 }
    }),
    definePage({
      key: "profile",
      path: "/profile",
      titleKey: "route.profile",
      component: () => import("../../views/ProfileView.vue"),
      fallbackOrder: 900
    })
  ]
});
