<template>
  <n-layout has-sider class="app-layout">
    <n-layout-sider
      class="app-sider"
      collapse-mode="width"
      :collapsed="collapsed"
      :collapsed-width="64"
      :width="220"
      show-trigger="arrow-circle"
      @update:collapsed="handleCollapsed"
    >
      <div class="brand">
        <BrandMark />
        <span class="brand-text">{{ APP_NAME }}</span>
      </div>
      <n-menu
        class="app-menu"
        :value="activeMenu"
        :options="menuOptions"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :expanded-keys="expandedKeys"
        @update:expanded-keys="handleExpandedKeys"
        @update:value="handleMenuChange"
      />
    </n-layout-sider>

    <n-layout class="app-main">
      <n-layout-header bordered class="app-header">
        <div class="page-title">
          <strong>{{ currentTitle }}</strong>
        </div>
        <div class="header-actions">
          <n-button quaternary circle :title="themeTitle" @click="toggleTheme">
            <template #icon><n-icon :component="themeIcon" /></template>
          </n-button>
          <n-dropdown trigger="click" :options="userOptions" @select="handleUserAction">
            <n-button quaternary>
              <template #icon><n-icon :component="PersonCircle" /></template>
              {{ authStore.user?.full_name || authStore.user?.username }}
            </n-button>
          </n-dropdown>
        </div>
      </n-layout-header>
      <n-layout-content class="app-content">
        <router-view />
      </n-layout-content>
      <n-layout-footer class="app-footer">
        <CopyrightNotice />
      </n-layout-footer>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import {
  PersonCircle20Regular as PersonCircle,
  PersonSettings20Regular,
  WeatherMoon20Regular as WeatherMoon,
  WeatherSunny20Regular as WeatherSunny
} from "@vicons/fluent";
import { computed, h, ref, watch, type Component } from "vue";
import { useRoute, useRouter } from "vue-router";
import { NButton, NDropdown, NIcon, NLayout, NLayoutContent, NLayoutFooter, NLayoutHeader, NLayoutSider, NMenu } from "naive-ui";
import type { MenuOption } from "naive-ui";

import { logout } from "../api/auth";
import { APP_NAME, appKey } from "../config/app";
import {
  getPageTitle,
  getVisibleMenuItems,
  hasMenuKey,
  hasMenuPath,
  menuKey,
  parentKeysForPath,
  type AppMenuItem
} from "../router/page-registry";
import { appStore } from "../stores/app";
import { authStore } from "../stores/auth";
import BrandMark from "./BrandMark.vue";
import CopyrightNotice from "./CopyrightNotice.vue";

const SIDEBAR_KEY = appKey("sidebar.collapsed");

const collapsed = ref(localStorage.getItem(SIDEBAR_KEY) === "1");
const route = useRoute();
const router = useRouter();

const menuItems = computed(() => getVisibleMenuItems((code) => authStore.has(code)));
const menuOptions = computed<MenuOption[]>(() => toMenuOptions(menuItems.value));
const activeMenu = computed(() => (hasMenuPath(menuItems.value, route.path) ? route.path : null));
const expandedKeys = ref<string[]>([]);
const currentTitle = computed(() => getPageTitle(route.path) || APP_NAME);
const themeIcon = computed(() => (appStore.dark ? WeatherSunny : WeatherMoon));
const themeTitle = computed(() => (appStore.dark ? "切换浅色主题" : "切换深色主题"));

const userOptions = [
  { label: "个人信息", key: "profile", icon: renderIcon(PersonSettings20Regular) },
  { label: "退出登录", key: "logout", icon: renderIcon(PersonCircle) }
];

function handleCollapsed(value: boolean) {
  collapsed.value = value;
  localStorage.setItem(SIDEBAR_KEY, value ? "1" : "0");
}

function handleExpandedKeys(keys: Array<string | number>) {
  expandedKeys.value = keys.map(String);
}

async function handleMenuChange(key: string | number) {
  const path = String(key);
  if (!path.startsWith("/")) return;
  if (path === route.path) return;
  await router.push(path);
}

async function handleUserAction(key: string) {
  if (key === "profile") {
    await router.push("/profile");
    return;
  }
  try {
    await logout();
  } finally {
    authStore.clear();
    await router.push("/login");
  }
}

function toggleTheme() {
  appStore.toggleTheme();
}

function renderIcon(icon: Component) {
  return () => h(NIcon, null, { default: () => h(icon) });
}

function toMenuOptions(items: AppMenuItem[]) {
  return items.map((item) => {
    const option: MenuOption = {
      key: menuKey(item),
      label: item.label,
      icon: renderIcon(item.icon)
    };
    if (item.children?.length) {
      option.children = toMenuOptions(item.children);
    }
    return option;
  });
}

watch(
  [menuItems, () => route.path],
  () => {
    const activeParents = parentKeysForPath(menuItems.value, route.path);
    const validKeys = expandedKeys.value.filter((key) => hasMenuKey(menuItems.value, key));
    expandedKeys.value = Array.from(new Set([...validKeys, ...activeParents]));
  },
  { immediate: true }
);
</script>
