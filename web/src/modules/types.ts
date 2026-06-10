import type { Component } from "vue";

export type AppFeature = "api" | string;
export type PageComponent = () => Promise<unknown>;

export interface AppMenuGroup {
  key: string;
  labelKey: string;
  icon: Component;
  order: number;
}

export interface AppPage {
  key: string;
  path: string;
  titleKey: string;
  component: PageComponent;
  permission?: string;
  feature?: AppFeature;
  fallbackOrder?: number;
  menu?: {
    group?: string;
    icon: Component;
    order: number;
  };
}

export interface AppModule {
  key: string;
  version: string;
  order?: number;
  dependencies?: string[];
  menuGroups?: AppMenuGroup[];
  pages?: AppPage[];
}

export function defineModule(module: AppModule) {
  return module;
}

export function definePage(page: AppPage) {
  return page;
}

export function defineMenuGroup(group: AppMenuGroup) {
  return group;
}

export function routePermission(page: string) {
  return `route:${page}`;
}

export function actionPermission(resource: string, action: string) {
  return `action:${resource}:${action}`;
}
