<template>
  <div class="page-stack">
    <section class="stat-grid">
      <div class="stat-item">
        <span>用户数</span>
        <div class="stat-value">{{ summary?.user_count ?? "-" }}</div>
      </div>
      <div class="stat-item">
        <span>待审批</span>
        <div class="stat-value">{{ summary?.pending_user_count ?? "-" }}</div>
      </div>
      <div class="stat-item">
        <span>角色数</span>
        <div class="stat-value">{{ summary?.role_count ?? "-" }}</div>
      </div>
      <div class="stat-item">
        <span>权限数</span>
        <div class="stat-value">{{ summary?.permission_count ?? "-" }}</div>
      </div>
    </section>
    <section class="work-card">
      <h3>当前用户</h3>
      <n-descriptions :column="2" bordered>
        <n-descriptions-item label="账号">{{ authStore.user?.username }}</n-descriptions-item>
        <n-descriptions-item label="姓名">{{ authStore.user?.full_name }}</n-descriptions-item>
        <n-descriptions-item label="公司">{{ authStore.user?.company || "-" }}</n-descriptions-item>
        <n-descriptions-item label="部门">{{ authStore.user?.department || "-" }}</n-descriptions-item>
      </n-descriptions>
    </section>
    <section class="work-card">
      <h3>可访问页面</h3>
      <div class="toolbar-group">
        <n-tag v-for="item in pages" :key="item">{{ item }}</n-tag>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { NDescriptions, NDescriptionsItem, NTag, useMessage } from "naive-ui";
import { computed, onMounted, ref } from "vue";

import { getDashboardSummary } from "../api/system";
import type { DashboardSummary } from "../api/types";
import { showError } from "../utils/message";
import { authStore } from "../stores/auth";

const message = useMessage();
const summary = ref<DashboardSummary | null>(null);
const pages = computed(() => {
  const result = ["个人信息"];
  if (authStore.has("route:dashboard")) result.unshift("首页");
  if (authStore.has("route:users")) result.push("用户管理");
  if (authStore.has("route:permissions")) result.push("权限管理");
  return result;
});

onMounted(async () => {
  try {
    summary.value = await getDashboardSummary();
  } catch (error) {
    showError(message, error);
  }
});
</script>
