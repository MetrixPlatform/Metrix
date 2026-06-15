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

import { defineMenuGroup, defineModule, definePage, routePermission } from "../types";

export default defineModule({
  key: "core",
  version: "0.1.0",
  order: 10,
  menuGroups: [
    defineMenuGroup({ key: "system", labelKey: "route.group.system", icon: Settings20Regular, order: 40 })
  ],
  pages: [
    definePage({
      key: "dashboard",
      path: "/",
      titleKey: "route.dashboard",
      component: () => import("../../views/DashboardView.vue"),
      permission: routePermission("dashboard"),
      fallbackOrder: 10,
      menu: { icon: Board20Regular, order: 10 }
    }),
    definePage({
      key: "users",
      path: "/users",
      titleKey: "route.users",
      component: () => import("../../views/UserManageView.vue"),
      permission: routePermission("users"),
      fallbackOrder: 20,
      menu: { group: "system", icon: People20Regular, order: 10 }
    }),
    definePage({
      key: "permissions",
      path: "/permissions",
      titleKey: "route.permissions",
      component: () => import("../../views/PermissionView.vue"),
      permission: routePermission("permissions"),
      fallbackOrder: 30,
      menu: { group: "system", icon: KeyMultiple20Regular, order: 20 }
    }),
    definePage({
      key: "announcements",
      path: "/announcements",
      titleKey: "route.announcements",
      component: () => import("../../views/AnnouncementManageView.vue"),
      permission: routePermission("announcements"),
      fallbackOrder: 40,
      menu: { group: "system", icon: MegaphoneLoud20Regular, order: 30 }
    }),
    definePage({
      key: "auditLogs",
      path: "/audit-logs",
      titleKey: "route.auditLogs",
      component: () => import("../../views/AuditLogView.vue"),
      permission: routePermission("audit_logs"),
      fallbackOrder: 50,
      menu: { group: "system", icon: ClipboardClock20Regular, order: 40 }
    }),
    definePage({
      key: "settings",
      path: "/settings",
      titleKey: "route.settings",
      component: () => import("../../views/SystemSettingsView.vue"),
      permission: routePermission("settings"),
      fallbackOrder: 60,
      menu: { group: "system", icon: PeopleSettings20Regular, order: 90 }
    }),
    definePage({
      key: "tokens",
      path: "/tokens",
      titleKey: "route.tokens",
      component: () => import("../../views/TokenManageView.vue"),
      permission: routePermission("tokens"),
      feature: "api",
      fallbackOrder: 70,
      menu: { group: "system", icon: Key20Regular, order: 50 }
    }),
    definePage({
      key: "apiDocs",
      path: "/api-docs",
      titleKey: "route.apiDocs",
      component: () => import("../../views/ApiDocsView.vue"),
      permission: routePermission("api_docs"),
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
