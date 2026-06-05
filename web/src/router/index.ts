import { createRouter, createWebHistory } from "vue-router";

import { AUTH_EXPIRED_EVENT } from "../api/client";
import { getInstallStatus } from "../api/install";
import { getMe } from "../api/auth";
import { authStore } from "../stores/auth";
import { createAppPageRoutes, getFallbackPath } from "./page-registry";

const routes = [
  { path: "/install", component: () => import("../views/InstallView.vue"), meta: { public: true } },
  { path: "/login", component: () => import("../views/LoginView.vue"), meta: { public: true } },
  { path: "/register", component: () => import("../views/RegisterView.vue"), meta: { public: true } },
  {
    path: "/",
    component: () => import("../components/AppShell.vue"),
    children: createAppPageRoutes()
  },
  { path: "/:pathMatch(.*)*", component: () => import("../views/NotFoundView.vue"), meta: { public: true } }
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
  const status = await getInstallStatus();
  if (!status.installed && to.path !== "/install") {
    return "/install";
  }
  if (status.installed && to.path === "/install") {
    return authStore.token ? "/" : "/login";
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
  if (permission && !authStore.has(permission)) {
    const path = getFallbackPath((code) => authStore.has(code));
    return to.path === path ? true : path;
  }
  return true;
});
