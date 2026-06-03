<template>
  <div class="app-layout">
    <aside class="app-sidebar" :class="{ collapsed }">
      <div class="brand">
        <BrandMark />
        <span v-if="!collapsed">Metrix</span>
      </div>
      <nav class="nav-list">
        <router-link v-for="item in menuItems" :key="item.path" :to="item.path" class="nav-item">
          <n-icon :component="item.icon" />
          <span v-if="!collapsed">{{ item.label }}</span>
        </router-link>
      </nav>
    </aside>
    <section class="app-main">
      <header class="app-header">
        <n-button quaternary circle :title="collapsed ? '展开菜单' : '收起菜单'" @click="collapsed = !collapsed">
          <template #icon><n-icon :component="PanelLeftContract" /></template>
        </n-button>
        <div class="page-title">
          <strong>{{ currentTitle }}</strong>
          <span>{{ currentSubtitle }}</span>
        </div>
        <div class="header-actions">
          <n-button quaternary circle title="切换主题" @click="appStore.toggleTheme">
            <template #icon><n-icon :component="WeatherMoon" /></template>
          </n-button>
          <n-dropdown :options="userOptions" @select="handleUserAction">
            <n-button quaternary>
              <template #icon><n-icon :component="PersonCircle" /></template>
              {{ authStore.user?.full_name || authStore.user?.username }}
            </n-button>
          </n-dropdown>
        </div>
      </header>
      <main class="app-content">
        <router-view />
      </main>
    </section>
  </div>
</template>

<script setup lang="ts">
import {
  Board20Regular,
  CheckmarkCircle20Regular,
  KeyMultiple20Regular,
  PanelLeftContract20Regular as PanelLeftContract,
  People20Regular,
  PersonCircle20Regular as PersonCircle,
  PersonSettings20Regular,
  WeatherMoon20Regular as WeatherMoon
} from "@vicons/fluent";
import { computed, h, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { NButton, NDropdown, NIcon } from "naive-ui";

import { logout } from "../api/auth";
import BrandMark from "./BrandMark.vue";
import { appStore } from "../stores/app";
import { authStore } from "../stores/auth";

const collapsed = ref(false);
const route = useRoute();
const router = useRouter();

const allMenus = [
  { path: "/", label: "首页", permission: "route:dashboard", icon: Board20Regular },
  { path: "/users", label: "用户管理", permission: "route:users", icon: People20Regular },
  { path: "/approvals", label: "注册审批", permission: "route:approvals", icon: CheckmarkCircle20Regular },
  { path: "/permissions", label: "权限管理", permission: "route:permissions", icon: KeyMultiple20Regular },
  { path: "/profile", label: "个人信息", permission: "", icon: PersonSettings20Regular }
];

const menuItems = computed(() => allMenus.filter((item) => !item.permission || authStore.has(item.permission)));
const currentMenu = computed(() => allMenus.find((item) => item.path === route.path) || allMenus[0]);
const currentTitle = computed(() => currentMenu.value.label);
const currentSubtitle = computed(() => (route.path === "/" ? "基础框架工作台" : "内网平台基础管理"));

const userOptions = [
  { label: "个人信息", key: "profile", icon: () => h(NIcon, null, { default: () => h(PersonSettings20Regular) }) },
  { label: "退出登录", key: "logout", icon: () => h(NIcon, null, { default: () => h(PersonCircle) }) }
];

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
</script>
