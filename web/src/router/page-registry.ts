import {
  Board20Regular,
  KeyMultiple20Regular,
  MegaphoneLoud20Regular,
  People20Regular,
  Settings20Regular
} from "@vicons/fluent";
import type { Component } from "vue";
import type { RouteRecordRaw } from "vue-router";

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
  label: string;
  icon: Component;
  order: number;
}

interface AppPage {
  key: string;
  path: string;
  title: string;
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
  { key: "system", label: "系统管理", icon: Settings20Regular, order: 20 }
];

// 新增主框架页面时优先维护这里，路由、标题、菜单和 fallback 会自动派生。
const appPages: AppPage[] = [
  {
    key: "dashboard",
    path: "/",
    title: "首页",
    component: () => import("../views/DashboardView.vue"),
    permission: "route:dashboard",
    fallbackOrder: 10,
    menu: { icon: Board20Regular, order: 10 }
  },
  {
    key: "users",
    path: "/users",
    title: "用户管理",
    component: () => import("../views/UserManageView.vue"),
    permission: "route:users",
    fallbackOrder: 20,
    menu: { group: "system", icon: People20Regular, order: 10 }
  },
  {
    key: "permissions",
    path: "/permissions",
    title: "权限管理",
    component: () => import("../views/PermissionView.vue"),
    permission: "route:permissions",
    fallbackOrder: 30,
    menu: { group: "system", icon: KeyMultiple20Regular, order: 20 }
  },
  {
    key: "announcements",
    path: "/announcements",
    title: "公告管理",
    component: () => import("../views/AnnouncementManageView.vue"),
    permission: "route:announcements",
    fallbackOrder: 40,
    menu: { group: "system", icon: MegaphoneLoud20Regular, order: 30 }
  },
  {
    key: "profile",
    path: "/profile",
    title: "个人信息",
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
      title: page.title
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
  return appPages.find((page) => page.path === path)?.title;
}

export function getVisibleMenuItems(hasPermission: HasPermission) {
  const groupMap = new Map<string, AppMenuItem & { order: number; children: AppMenuItem[] }>();
  const topLevel: Array<AppMenuItem & { order: number }> = [];

  for (const group of menuGroups) {
    groupMap.set(group.key, {
      key: group.key,
      label: group.label,
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
    label: page.title,
    permission: page.permission,
    icon: menu.icon,
    order: menu.order
  };
}

function sortMenuItems(left: AppMenuItem & { order?: number }, right: AppMenuItem & { order?: number }) {
  return (left.order || 0) - (right.order || 0);
}
