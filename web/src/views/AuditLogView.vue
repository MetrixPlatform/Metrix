<template>
  <section class="work-card table-page-card">
    <div class="toolbar audit-log-toolbar">
      <div class="audit-log-filter-row">
        <n-input v-model:value="filters.keyword" class="filter-keyword" :placeholder="t('auditLog.searchPlaceholder')" clearable />
        <n-date-picker
          v-model:value="filters.time_range"
          class="filter-date-range"
          type="datetimerange"
          clearable
          :start-placeholder="t('common.startTime')"
          :end-placeholder="t('common.endTime')"
        />
        <n-button @click="searchLogs">{{ t("common.search") }}</n-button>
      </div>
    </div>
    <n-data-table
      class="page-data-table"
      flex-height
      :columns="columns"
      :data="logs"
      :loading="loading"
      :pagination="pagination"
      :row-key="(row) => row.id"
      :scroll-x="tableScrollX"
      remote
      @update:filters="handleTableFilters"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
      @update:sorter="handleSorter"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from "vue";
import { NButton, NDataTable, NDatePicker, NInput, NTag, useMessage } from "naive-ui";
import type { DataTableColumns, DataTableFilterState, DataTableSortState } from "naive-ui";

import { listAuditLogs } from "../api/audit";
import type { AuditLogItem } from "../api/types";
import { formatDateTime, hasI18nKey, t } from "../i18n";
import { authStore } from "../stores/auth";
import { showError } from "../utils/message";

type AuditActorScope = "self" | "all";

const message = useMessage();
const loading = ref(false);
const logs = ref<AuditLogItem[]>([]);
const filters = reactive<{
  keyword: string;
  actor_scope: AuditActorScope;
  action: string | null;
  target_type: string | null;
  sort_order: "ascend" | "descend";
  time_range: [number, number] | null;
}>({
  keyword: "",
  actor_scope: "self",
  action: null,
  target_type: null,
  sort_order: "descend",
  time_range: null
});
const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  pageSizes: [20, 50, 100, 500],
  showSizePicker: true,
  prefix: ({ itemCount }: { itemCount: number | undefined }) => t("common.total", { count: itemCount ?? 0 })
});
const auditLogColumnWidths = {
  actor: 130,
  action: 180,
  targetType: 130,
  targetId: 130,
  detail: 260,
  createdAt: 170
};
const tableScrollX = Object.values(auditLogColumnWidths).reduce((total, width) => total + width, 0);
const auditActionCodes = [
  "auth.login",
  "auth.login_failed",
  "auth.profile_update",
  "auth.change_password",
  "user.register",
  "user.create",
  "user.update",
  "user.delete",
  "user.approve",
  "user.reject",
  "user.enable",
  "user.disable",
  "user.reset_password",
  "user.assign_roles",
  "role.create",
  "role.update",
  "role.delete",
  "role.assign_permissions",
  "announcement.create",
  "announcement.update",
  "announcement.delete"
];
const auditTargetTypes = ["user", "role", "announcement"];
const canViewAllLogs = computed(() => authStore.has("action:audit_log:manage_others"));
const actorScopeOptions = computed(() => [
  { label: t("auditLog.scopeSelf"), value: "self" },
  ...(canViewAllLogs.value ? [{ label: t("auditLog.scopeAll"), value: "all" }] : [])
]);
const actionOptions = computed(() => distinctOptions([...auditActionCodes, ...logs.value.map((item) => item.action)]));
const targetTypeOptions = computed(() => distinctOptions([...auditTargetTypes, ...logs.value.map((item) => item.target_type)]));
const columns = computed<DataTableColumns<AuditLogItem>>(() => [
  {
    title: t("field.operator"),
    key: "actor_scope",
    width: auditLogColumnWidths.actor,
    filter: () => true,
    filterMultiple: false,
    filterOptionValue: filters.actor_scope,
    filterOptions: actorScopeOptions.value,
    render: (row) => row.actor_username || t("auditLog.systemOperator")
  },
  {
    title: t("field.action"),
    key: "action",
    width: auditLogColumnWidths.action,
    filter: (value, row) => row.action === value,
    filterMultiple: false,
    filterOptionValue: filters.action,
    filterOptions: actionOptions.value,
    render: (row) => h(NTag, { size: "small", round: true }, { default: () => actionLabel(row.action) })
  },
  {
    title: t("field.auditTargetType"),
    key: "target_type",
    width: auditLogColumnWidths.targetType,
    filter: (value, row) => row.target_type === value,
    filterMultiple: false,
    filterOptionValue: filters.target_type,
    filterOptions: targetTypeOptions.value,
    render: (row) => targetTypeLabel(row.target_type)
  },
  { title: t("field.targetId"), key: "target_id", width: auditLogColumnWidths.targetId, render: (row) => row.target_id || t("common.none") },
  { title: t("field.detail"), key: "detail", width: auditLogColumnWidths.detail, ellipsis: { tooltip: true }, render: (row) => row.detail || t("common.none") },
  {
    title: t("field.createdAt"),
    key: "created_at",
    width: auditLogColumnWidths.createdAt,
    sorter: true,
    sortOrder: filters.sort_order,
    render: (row) => formatTime(row.created_at)
  }
]);

onMounted(async () => {
  await loadLogs();
});

async function loadLogs() {
  loading.value = true;
  try {
    const result = await listAuditLogs({
      keyword: filters.keyword,
      actor_scope: filters.actor_scope,
      action: filters.action || "",
      target_type: filters.target_type || "",
      sort_order: filters.sort_order,
      start_time: filters.time_range ? new Date(filters.time_range[0]).toISOString() : "",
      end_time: filters.time_range ? new Date(filters.time_range[1]).toISOString() : "",
      page: pagination.page,
      page_size: pagination.pageSize
    });
    logs.value = result.items;
    pagination.itemCount = result.total;
    pagination.page = result.page;
    pagination.pageSize = result.page_size;
  } catch (error) {
    showError(message, error);
  } finally {
    loading.value = false;
  }
}

function searchLogs() {
  pagination.page = 1;
  void loadLogs();
}

function handlePageChange(page: number) {
  pagination.page = page;
  void loadLogs();
}

function handlePageSizeChange(pageSize: number) {
  pagination.pageSize = pageSize;
  pagination.page = 1;
  void loadLogs();
}

function handleTableFilters(filterState: DataTableFilterState) {
  const actorScope = singleFilterValue(filterState, "actor_scope");
  const action = singleFilterValue(filterState, "action");
  const targetType = singleFilterValue(filterState, "target_type");
  filters.actor_scope = isActorScope(actorScope) && (actorScope === "self" || canViewAllLogs.value) ? actorScope : "self";
  filters.action = typeof action === "string" ? action : null;
  filters.target_type = typeof targetType === "string" ? targetType : null;
  pagination.page = 1;
  void loadLogs();
}

function handleSorter(sortState: DataTableSortState | DataTableSortState[] | null) {
  const state = Array.isArray(sortState) ? sortState[0] : sortState;
  filters.sort_order = state?.order === "ascend" ? "ascend" : "descend";
  pagination.page = 1;
  void loadLogs();
}

function singleFilterValue(filterState: DataTableFilterState, key: string) {
  const value = filterState[key];
  return Array.isArray(value) ? value[0] ?? null : value ?? null;
}

function isActorScope(value: unknown): value is AuditActorScope {
  return value === "self" || value === "all";
}

function distinctOptions(values: string[]) {
  return Array.from(new Set(values.filter(Boolean))).map((value) => ({ label: actionOrTargetLabel(value), value }));
}

function actionLabel(action: string) {
  return actionOrTargetLabel(action);
}

function targetTypeLabel(targetType: string) {
  return targetType ? actionOrTargetLabel(targetType) : t("common.none");
}

function actionOrTargetLabel(value: string) {
  const key = `auditLog.${value}`;
  return hasI18nKey(key) ? t(key) : value;
}

function formatTime(value: string) {
  return formatDateTime(value);
}
</script>
