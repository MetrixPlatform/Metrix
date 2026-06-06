import {
  Board20Regular,
  ClipboardClock20Regular,
  KeyMultiple20Regular,
  MegaphoneLoud20Regular,
  People20Regular,
  PeopleSettings20Regular,
  Settings20Regular
} from "@vicons/fluent";
import type { Component } from "vue";
import type { RouteRecordRaw } from "vue-router";

import { t, type I18nKey } from "../i18n";

type HasPermission = (permission: string) => boolean;
type PageComponent = () => Promise<unknown>;

export interface AppMenuItem {
  key?: string;
  path?: string;
  label: string;
  permission?: string;
  icon: Component;
  children?: AppMenuItem[];
}

interface AppMenuGroup {
  key: string;
  labelKey: I18nKey;
  icon: Component;
  order: number;
}

interface AppPage {
  key: string;
  path: string;
  titleKey: I18nKey;
  component: PageComponent;
  permission?: string;
  fallbackOrder?: number;
  menu?: {
    group?: string;
    icon: Component;
    order: number;
  };
}

const menuGroups: AppMenuGroup[] = [
  { key: "system", labelKey: "route.group.system", icon: Settings20Regular, order: 20 }
];

const appPages: AppPage[] = [
  {
    key: "dashboard",
    path: "/",
    titleKey: "route.dashboard",
    component: () => import("../views/DashboardView.vue"),
    permission: "route:dashboard",
    fallbackOrder: 10,
    menu: { icon: Board20Regular, order: 10 }
  },
  {
    key: "users",
    path: "/users",
    titleKey: "route.users",
    component: () => import("../views/UserManageView.vue"),
    permission: "route:users",
    fallbackOrder: 20,
    menu: { group: "system", icon: People20Regular, order: 10 }
  },
  {
    key: "permissions",
    path: "/permissions",
    titleKey: "route.permissions",
    component: () => import("../views/PermissionView.vue"),
    permission: "route:permissions",
    fallbackOrder: 30,
    menu: { group: "system", icon: KeyMultiple20Regular, order: 20 }
  },
  {
    key: "announcements",
    path: "/announcements",
    titleKey: "route.announcements",
    component: () => import("../views/AnnouncementManageView.vue"),
    permission: "route:announcements",
    fallbackOrder: 40,
    menu: { group: "system", icon: MegaphoneLoud20Regular, order: 30 }
  },
  {
    key: "auditLogs",
    path: "/audit-logs",
    titleKey: "route.auditLogs",
    component: () => import("../views/AuditLogView.vue"),
    permission: "route:audit_logs",
    fallbackOrder: 50,
    menu: { group: "system", icon: ClipboardClock20Regular, order: 40 }
  },
  {
    key: "settings",
    path: "/settings",
    titleKey: "route.settings",
    component: () => import("../views/SystemSettingsView.vue"),
    permission: "route:settings",
    fallbackOrder: 60,
    menu: { group: "system", icon: PeopleSettings20Regular, order: 50 }
  },
  {
    key: "profile",
    path: "/profile",
    titleKey: "route.profile",
    component: () => import("../views/ProfileView.vue"),
    fallbackOrder: 900
  }
];

export function createAppPageRoutes() {
  return appPages.map((page) => ({
    path: childRoutePath(page.path),
    component: page.component,
    meta: {
      permission: page.permission,
      titleKey: page.titleKey
    }
  })) as RouteRecordRaw[];
}

export function getFallbackPath(hasPermission: HasPermission) {
  return (
    [...appPages]
      .filter((page) => page.fallbackOrder !== undefined && canAccessPage(page, hasPermission))
      .sort((left, right) => (left.fallbackOrder || 0) - (right.fallbackOrder || 0))[0]?.path || "/profile"
  );
}

export function getPageTitle(path: string) {
  const page = appPages.find((item) => item.path === path);
  return page ? t(page.titleKey) : undefined;
}

export function getVisibleMenuItems(hasPermission: HasPermission) {
  const groupMap = new Map<string, AppMenuItem & { order: number; children: AppMenuItem[] }>();
  const topLevel: Array<AppMenuItem & { order: number }> = [];

  for (const group of menuGroups) {
    groupMap.set(group.key, {
      key: group.key,
      label: t(group.labelKey),
      icon: group.icon,
      order: group.order,
      children: []
    });
  }

  for (const page of appPages) {
    if (!page.menu || !canAccessPage(page, hasPermission)) continue;
    const item = pageToMenuItem(page, page.menu);
    if (page.menu.group) {
      const group = groupMap.get(page.menu.group);
      if (group) {
        group.children.push(item);
      } else {
        topLevel.push({ ...item, order: page.menu.order });
      }
    } else {
      topLevel.push({ ...item, order: page.menu.order });
    }
  }

  const visibleGroups = [...groupMap.values()]
    .filter((group) => group.children.length > 0)
    .map((group) => ({
      ...group,
      children: group.children.sort(sortMenuItems)
    }));

  return [...topLevel, ...visibleGroups].sort(sortMenuItems);
}

export function hasMenuPath(items: AppMenuItem[], path: string): boolean {
  return items.some((item) => item.path === path || (item.children ? hasMenuPath(item.children, path) : false));
}

export function hasMenuKey(items: AppMenuItem[], key: string): boolean {
  return items.some((item) => menuKey(item) === key || (item.children ? hasMenuKey(item.children, key) : false));
}

export function parentKeysForPath(items: AppMenuItem[], path: string, parents: string[] = []): string[] {
  for (const item of items) {
    if (item.path === path) return parents;
    if (item.children) {
      const keys = parentKeysForPath(item.children, path, [...parents, menuKey(item)]);
      if (keys.length > 0) return keys;
    }
  }
  return [];
}

export function menuKey(item: AppMenuItem) {
  return item.path || item.key || item.label;
}

function childRoutePath(path: string) {
  return path === "/" ? "" : path.replace(/^\//, "");
}

function canAccessPage(page: AppPage, hasPermission: HasPermission) {
  return !page.permission || hasPermission(page.permission);
}

function pageToMenuItem(page: AppPage, menu: NonNullable<AppPage["menu"]>): AppMenuItem & { order: number } {
  return {
    path: page.path,
    label: t(page.titleKey),
    permission: page.permission,
    icon: menu.icon,
    order: menu.order
  };
}

function sortMenuItems(left: AppMenuItem & { order?: number }, right: AppMenuItem & { order?: number }) {
  return (left.order || 0) - (right.order || 0);
}
