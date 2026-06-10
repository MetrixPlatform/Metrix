import { createRouter, createWebHistory } from "vue-router";

import { AUTH_EXPIRED_EVENT } from "../api/client";
import { getInstallStatus } from "../api/install";
import { getMe } from "../api/auth";
import { appKey } from "../config/app";
import { appStore } from "../stores/app";
import { authStore } from "../stores/auth";
import { settingsStore } from "../stores/settings";
import { createAppPageRoutes, getFallbackPath } from "./page-registry";

const LOCALE_KEY = appKey("locale");

const routes = [
  { path: "/install", component: () => import("../views/InstallView.vue"), meta: { public: true } },
  { path: "/login", component: () => import("../views/LoginView.vue"), meta: { public: true } },
  { path: "/register", component: () => import("../views/RegisterView.vue"), meta: { public: true } },
  {
    path: "/",
    component: () => import("../components/AppShell.vue"),
    children: [
      ...createAppPageRoutes(),
      {
        path: ":pathMatch(.*)*",
        component: () => import("../views/NotFoundView.vue")
      }
    ]
  }
];

export const router = createRouter({
  history: createWebHistory(),
  routes
});

window.addEventListener(AUTH_EXPIRED_EVENT, () => {
  const current = router.currentRoute.value;
  if (current.path !== "/login") {
    void router.replace("/login");
  }
});

router.beforeEach(async (to) => {
  const status = await loadInstallStatus();
  if (status && !status.installed && to.path !== "/install") {
    return "/install";
  }
  if (status?.installed && to.path === "/install") {
    return authStore.token ? "/" : "/login";
  }
  if (status?.installed && !settingsStore.loaded) {
    try {
      const publicSettings = await settingsStore.loadPublic();
      if (!localStorage.getItem(LOCALE_KEY)) {
        await appStore.setLocale(publicSettings.default_locale);
      }
    } catch {
      // Keep bundled defaults if public settings are temporarily unavailable.
    }
  }
  if (status?.installed && to.path === "/register" && !settingsStore.publicSettings.registration_enabled) {
    return "/login";
  }
  if (to.meta.public) {
    return true;
  }
  if (!authStore.token) {
    return "/login";
  }
  if (!authStore.user) {
    try {
      const session = await getMe();
      authStore.setSession("", session.user, session.permissions);
    } catch {
      return "/login";
    }
  }
  const permission = to.meta.permission as string | undefined;
  const feature = to.meta.feature as string | undefined;
  if (feature && !isFeatureEnabled(feature)) {
    const path = getFallbackPath((code) => authStore.has(code), isFeatureEnabled);
    return to.path === path ? true : path;
  }
  if (permission && !authStore.has(permission)) {
    const path = getFallbackPath((code) => authStore.has(code), isFeatureEnabled);
    return to.path === path ? true : path;
  }
  return true;
});

async function loadInstallStatus() {
  try {
    return await getInstallStatus();
  } catch {
    return null;
  }
}

function isFeatureEnabled(feature?: string) {
  return feature !== "api" || settingsStore.apiEnabled();
}
