import type { Component } from "vue";
import type { RouteRecordRaw } from "vue-router";

import { t } from "../i18n";
import { appModules } from "../modules/registry";
import type { AppPage } from "../modules/types";

type HasPermission = (permission: string) => boolean;
type IsFeatureEnabled = (feature?: string) => boolean;

export interface AppMenuItem {
  key?: string;
  path?: string;
  navigationKey: string;
  label: string;
  permission?: string;
  icon: Component;
  children?: AppMenuItem[];
}

const menuGroups = appModules.flatMap((module) => module.menuGroups || []);
const appPages = appModules.flatMap((module) => module.pages || []);

export function createAppPageRoutes() {
  return appPages.map((page) => ({
    path: childRoutePath(page.path),
    component: page.component,
    meta: {
      permission: page.permission,
      feature: page.feature,
      titleKey: page.titleKey
    }
  })) as RouteRecordRaw[];
}

export function getFallbackPath(hasPermission: HasPermission, isFeatureEnabled: IsFeatureEnabled = () => true) {
  return (
    [...appPages]
      .filter((page) => page.fallbackOrder !== undefined && canAccessPage(page, hasPermission, isFeatureEnabled))
      .sort((left, right) => (left.fallbackOrder || 0) - (right.fallbackOrder || 0))[0]?.path || "/profile"
  );
}

export function getPageTitle(path: string) {
  const page = appPages.find((item) => item.path === path);
  return page ? t(page.titleKey) : undefined;
}

export function getVisibleMenuItems(
  hasPermission: HasPermission,
  isFeatureEnabled: IsFeatureEnabled = () => true,
  navigationOrder: string[] = []
) {
  return buildMenuItems(hasPermission, isFeatureEnabled, navigationOrder);
}

export function getNavigationLayout(navigationOrder: string[] = []) {
  return buildMenuItems(() => true, () => true, navigationOrder);
}

export function flattenNavigationKeys(items: AppMenuItem[]): string[] {
  return items.flatMap((item) => [item.navigationKey, ...(item.children ? flattenNavigationKeys(item.children) : [])]);
}

function buildMenuItems(hasPermission: HasPermission, isFeatureEnabled: IsFeatureEnabled, navigationOrder: string[]) {
  const customOrder = createNavigationOrderMap(navigationOrder);
  const groupMap = new Map<string, AppMenuItem & { order: number; children: AppMenuItem[] }>();
  const topLevel: Array<AppMenuItem & { order: number }> = [];

  for (const group of menuGroups) {
    groupMap.set(group.key, {
      key: group.key,
      navigationKey: navigationGroupKey(group.key),
      label: t(group.labelKey),
      icon: group.icon,
      order: group.order,
      children: []
    });
  }

  for (const page of appPages) {
    if (!page.menu || !canAccessPage(page, hasPermission, isFeatureEnabled)) continue;
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
      children: group.children.sort((left, right) => sortMenuItems(left, right, customOrder))
    }));

  const ordered = [...topLevel, ...visibleGroups].sort((left, right) => sortMenuItems(left, right, customOrder));
  return pinSystemGroupLast(ordered);
}

// 约定：导航栏「系统管理」分组永久置底。无论各模块的 menu.order 如何、也无论系统设置里的
// 自定义导航顺序（navigation_order）如何排列，"系统管理" 始终排在导航栏最后，新增业务模块/菜单
// 默认显示在它上方。如需调整此约定，请同时确认产品需求并更新这里的注释。
const SYSTEM_MENU_GROUP_KEY = "system";

function pinSystemGroupLast(items: AppMenuItem[]): AppMenuItem[] {
  const systemKey = navigationGroupKey(SYSTEM_MENU_GROUP_KEY);
  const index = items.findIndex((item) => item.navigationKey === systemKey);
  if (index < 0) return items;
  const [systemItem] = items.splice(index, 1);
  items.push(systemItem);
  return items;
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

function canAccessPage(page: AppPage, hasPermission: HasPermission, isFeatureEnabled: IsFeatureEnabled) {
  return isFeatureEnabled(page.feature) && (!page.permission || hasPermission(page.permission));
}

function pageToMenuItem(page: AppPage, menu: NonNullable<AppPage["menu"]>): AppMenuItem & { order: number } {
  return {
    path: page.path,
    navigationKey: navigationPathKey(page.path),
    label: t(page.titleKey),
    permission: page.permission,
    icon: menu.icon,
    order: menu.order
  };
}

function sortMenuItems(
  left: AppMenuItem & { order?: number },
  right: AppMenuItem & { order?: number },
  customOrder: Map<string, number>
) {
  const leftCustom = customOrder.get(left.navigationKey);
  const rightCustom = customOrder.get(right.navigationKey);
  if (leftCustom !== undefined && rightCustom !== undefined) return leftCustom - rightCustom;
  if (leftCustom !== undefined) return -1;
  if (rightCustom !== undefined) return 1;
  return (left.order || 0) - (right.order || 0);
}

function createNavigationOrderMap(order: string[]) {
  return new Map(order.map((key, index) => [key, index]));
}

function navigationPathKey(path: string) {
  return `path:${path}`;
}

function navigationGroupKey(group: string) {
  return `group:${group}`;
}
