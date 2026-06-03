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
        <span class="brand-text">Metrix</span>
      </div>
      <n-menu
        class="app-menu"
        :value="activeMenu"
        :options="menuOptions"
        :collapsed-width="64"
        :collapsed-icon-size="22"
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
          <n-dropdown :options="userOptions" @select="handleUserAction">
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
        Copyright © 2025 - 2026 NIXEVOL.All Rights Reserved.
      </n-layout-footer>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import {
  Board20Regular,
  KeyMultiple20Regular,
  People20Regular,
  PersonCircle20Regular as PersonCircle,
  PersonSettings20Regular,
  WeatherMoon20Regular as WeatherMoon,
  WeatherSunny20Regular as WeatherSunny
} from "@vicons/fluent";
import { computed, h, ref, type Component } from "vue";
import { useRoute, useRouter } from "vue-router";
import { NButton, NDropdown, NIcon, NLayout, NLayoutContent, NLayoutFooter, NLayoutHeader, NLayoutSider, NMenu } from "naive-ui";
import type { MenuOption } from "naive-ui";

import { logout } from "../api/auth";
import { appStore } from "../stores/app";
import { authStore } from "../stores/auth";
import BrandMark from "./BrandMark.vue";

const SIDEBAR_KEY = "metrix.sidebar.collapsed";

const collapsed = ref(localStorage.getItem(SIDEBAR_KEY) === "1");
const route = useRoute();
const router = useRouter();

const allMenus = [
  { path: "/", label: "首页", permission: "route:dashboard", icon: Board20Regular },
  { path: "/users", label: "用户管理", permission: "route:users", icon: People20Regular },
  { path: "/permissions", label: "权限管理", permission: "route:permissions", icon: KeyMultiple20Regular },
  { path: "/profile", label: "个人信息", permission: "", icon: PersonSettings20Regular }
];

const menuItems = computed(() => allMenus.filter((item) => !item.permission || authStore.has(item.permission)));
const menuOptions = computed<MenuOption[]>(() =>
  menuItems.value.map((item) => ({
    key: item.path,
    label: item.label,
    icon: renderIcon(item.icon)
  }))
);
const activeMenu = computed(() => menuItems.value.find((item) => item.path === route.path)?.path || "/");
const currentMenu = computed(() => allMenus.find((item) => item.path === route.path) || allMenus[0]);
const currentTitle = computed(() => currentMenu.value.label);
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

async function handleMenuChange(key: string | number) {
  const path = String(key);
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
</script>
