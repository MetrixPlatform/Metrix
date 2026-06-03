import { createRouter, createWebHistory } from "vue-router";

import { getInstallStatus } from "../api/install";
import { getMe } from "../api/auth";
import { authStore } from "../stores/auth";

const fallbackPath = () => {
  if (authStore.has("route:dashboard")) return "/";
  if (authStore.has("route:users")) return "/users";
  if (authStore.has("route:permissions")) return "/permissions";
  return "/profile";
};

const routes = [
  { path: "/install", component: () => import("../views/InstallView.vue"), meta: { public: true } },
  { path: "/login", component: () => import("../views/LoginView.vue"), meta: { public: true } },
  { path: "/register", component: () => import("../views/RegisterView.vue"), meta: { public: true } },
  {
    path: "/",
    component: () => import("../components/AppShell.vue"),
    children: [
      { path: "", component: () => import("../views/DashboardView.vue"), meta: { permission: "route:dashboard" } },
      { path: "users", component: () => import("../views/UserManageView.vue"), meta: { permission: "route:users" } },
      { path: "permissions", component: () => import("../views/PermissionView.vue"), meta: { permission: "route:permissions" } },
      { path: "profile", component: () => import("../views/ProfileView.vue") }
    ]
  }
];

export const router = createRouter({
  history: createWebHistory(),
  routes
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
    const path = fallbackPath();
    return to.path === path ? true : path;
  }
  return true;
});
