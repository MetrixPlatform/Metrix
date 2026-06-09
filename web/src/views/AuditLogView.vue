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
      <div class="toolbar-group audit-log-actions">
        <n-button :loading="downloading" @click="downloadLogs">
          <template #icon><n-icon :component="ArrowDownload20Regular" /></template>
          {{ t("common.download") }}
        </n-button>
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
      @unstable-column-resize="handleColumnResize"
      @update:filters="handleTableFilters"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
      @update:sorter="handleSorter"
    />

    <n-modal v-model:show="showDetailModal" preset="card" class="audit-log-detail-modal" :title="t('auditLog.detailTitle')">
      <div v-if="selectedLog" class="audit-log-detail">
        <n-descriptions bordered size="small" :column="2">
          <n-descriptions-item :label="t('field.auditSource')">{{ sourceLabel(selectedLog.source) }}</n-descriptions-item>
          <n-descriptions-item :label="t('field.operator')">
            {{ selectedLog.actor_username || t("auditLog.systemOperator") }}
          </n-descriptions-item>
          <n-descriptions-item :label="t('field.action')">{{ actionLabel(selectedLog.action) }}</n-descriptions-item>
          <n-descriptions-item :label="t('field.auditTargetType')">{{ targetTypeLabel(selectedLog.target_type) }}</n-descriptions-item>
          <n-descriptions-item :label="t('field.targetId')">{{ selectedLog.target_id || t("common.none") }}</n-descriptions-item>
          <n-descriptions-item :label="t('field.createdAt')">{{ formatTime(selectedLog.created_at) }}</n-descriptions-item>
          <n-descriptions-item :label="t('auditLog.targetName')" :span="2">{{ selectedTargetName }}</n-descriptions-item>
        </n-descriptions>

        <section class="audit-log-detail-section">
          <h3>{{ t("auditLog.changedFields") }}</h3>
          <div v-if="selectedChanges.length" class="audit-log-change-wrapper">
            <table class="audit-log-change-table">
              <thead>
                <tr>
                  <th>{{ t("apiDocs.fieldName") }}</th>
                  <th>{{ t("auditLog.before") }}</th>
                  <th>{{ t("auditLog.after") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="change in selectedChanges" :key="change.field">
                  <td>{{ fieldLabel(change.field) }}</td>
                  <td>{{ formatDetailValue(change.before) }}</td>
                  <td>{{ formatDetailValue(change.after) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="audit-log-empty-detail">{{ selectedFallbackDetail }}</p>
        </section>

        <section v-if="selectedMetaEntries.length" class="audit-log-detail-section">
          <h3>{{ t("auditLog.meta") }}</h3>
          <dl class="audit-log-meta-list">
            <template v-for="item in selectedMetaEntries" :key="item.key">
              <dt>{{ fieldLabel(item.key) }}</dt>
              <dd>{{ formatDetailValue(item.value) }}</dd>
            </template>
          </dl>
        </section>
      </div>
    </n-modal>
  </section>
</template>

<script setup lang="ts">
import { ArrowDownload20Regular } from "@vicons/fluent";
import { computed, h, onMounted, reactive, ref } from "vue";
import { NButton, NDataTable, NDatePicker, NDescriptions, NDescriptionsItem, NIcon, NInput, NModal, NTag, useMessage } from "naive-ui";
import type { DataTableColumns, DataTableFilterState, DataTableSortState } from "naive-ui";

import { listAuditLogs, type AuditLogFilters } from "../api/audit";
import type { AuditLogDetailChange, AuditLogItem } from "../api/types";
import { ensureLocaleNames, formatDateTime, hasI18nKey, localeOptions, t } from "../i18n";
import { defaultMessages } from "../i18n/messages";
import { authStore } from "../stores/auth";
import { saveBlob } from "../utils/download";
import { showError } from "../utils/message";
import { singleFilterValue, sumColumnWidths, updateColumnWidth, withResizableColumns } from "../utils/table";

type AuditActorScope = "self" | "all";

const EXPORT_PAGE_SIZE = 500;
const message = useMessage();
const loading = ref(false);
const downloading = ref(false);
const logs = ref<AuditLogItem[]>([]);
const showDetailModal = ref(false);
const selectedLog = ref<AuditLogItem | null>(null);
const filters = reactive<{
  keyword: string;
  actor_scope: AuditActorScope;
  action: string | null;
  target_type: string | null;
  source: string | null;
  sort_order: "ascend" | "descend";
  time_range: [number, number] | null;
}>({
  keyword: "",
  actor_scope: "self",
  action: null,
  target_type: null,
  source: null,
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
const auditLogColumnWidths = reactive<Record<string, number>>({
  source: 110,
  actor: 130,
  action: 180,
  targetType: 130,
  targetId: 130,
  detail: 340,
  createdAt: 170
});
const auditLogColumnWidthKeys: Record<string, string> = {
  source: "source",
  actor_scope: "actor",
  action: "action",
  target_type: "targetType",
  target_id: "targetId",
  detail: "detail",
  created_at: "createdAt"
};
const tableScrollX = computed(() => sumColumnWidths(auditLogColumnWidths));
const auditActionCodes = messagePathKeys(defaultMessages.auditLog.action);
const auditTargetTypes = Object.keys(defaultMessages.auditLog.target);
const auditSources = ["web", "api"];
const canViewAllLogs = computed(() => authStore.has("action:audit_log:manage_others"));
const actorScopeOptions = computed(() => [
  { label: t("auditLog.scopeSelf"), value: "self" },
  ...(canViewAllLogs.value ? [{ label: t("auditLog.scopeAll"), value: "all" }] : [])
]);
const actionOptions = computed(() => distinctActionOptions([...auditActionCodes, ...logs.value.map((item) => item.action)]));
const targetTypeOptions = computed(() => distinctTargetOptions([...auditTargetTypes, ...logs.value.map((item) => item.target_type)]));
const sourceOptions = computed(() => distinctSourceOptions([...auditSources, ...logs.value.map((item) => item.source)]));
const localeLabelMap = computed(() => Object.fromEntries(localeOptions.value.map((option) => [option.value, option.label])));
const selectedChanges = computed(() => (selectedLog.value ? detailChanges(selectedLog.value) : []));
const selectedMetaEntries = computed(() => (selectedLog.value ? detailMetaEntries(selectedLog.value) : []));
const selectedTargetName = computed(() => (selectedLog.value ? detailTargetName(selectedLog.value) : t("common.none")));
const selectedFallbackDetail = computed(() => {
  if (!selectedLog.value) return t("auditLog.noStructuredDetail");
  return selectedLog.value.detail || t("auditLog.noStructuredDetail");
});
const columns = computed<DataTableColumns<AuditLogItem>>(() =>
  withResizableColumns([
    {
      title: t("field.auditSource"),
      key: "source",
      width: auditLogColumnWidths.source,
      filter: (value, row) => row.source === value,
      filterMultiple: false,
      filterOptionValue: filters.source,
      filterOptions: sourceOptions.value,
      render: (row) => h(NTag, { size: "small", round: true, type: row.source === "api" ? "info" : "default" }, { default: () => sourceLabel(row.source) })
    },
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
    {
      title: t("field.detail"),
      key: "detail",
      width: auditLogColumnWidths.detail,
      render: (row) =>
        h(
          NButton,
          {
            class: "audit-detail-button",
            text: true,
            type: "primary",
            title: t("auditLog.viewDetail"),
            onClick: () => openLogDetail(row)
          },
          { default: () => detailSummary(row) }
        )
    },
    {
      title: t("field.createdAt"),
      key: "created_at",
      width: auditLogColumnWidths.createdAt,
      sorter: true,
      sortOrder: filters.sort_order,
      render: (row) => formatTime(row.created_at)
    }
  ])
);

onMounted(async () => {
  void ensureLocaleNames();
  await loadLogs();
});

async function loadLogs() {
  loading.value = true;
  try {
    const result = await listAuditLogs(buildFilters(true));
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

async function downloadLogs() {
  downloading.value = true;
  try {
    const blob = new Blob([auditLogsCsv(await loadExportLogs())], { type: "text/csv;charset=utf-8" });
    saveBlob(blob, `audit-logs-${new Date().toISOString().slice(0, 10)}.csv`);
  } catch (error) {
    showError(message, error);
  } finally {
    downloading.value = false;
  }
}

async function loadExportLogs() {
  const items: AuditLogItem[] = [];
  let page = 1;
  let total = 0;
  do {
    const result = await listAuditLogs({ ...buildFilters(false), page, page_size: EXPORT_PAGE_SIZE });
    items.push(...result.items);
    total = result.total;
    page += 1;
    if (result.items.length === 0) break;
  } while (items.length < total);
  return items;
}

function auditLogsCsv(items: AuditLogItem[]) {
  const rows = [
    [t("field.auditSource"), t("field.operator"), t("field.action"), t("field.auditTargetType"), t("field.targetId"), t("field.detail"), t("field.createdAt")],
    ...items.map((item) => [
      sourceLabel(item.source),
      item.actor_username || t("auditLog.systemOperator"),
      actionLabel(item.action),
      targetTypeLabel(item.target_type),
      item.target_id || t("common.none"),
      detailSummary(item),
      excelText(formatTime(item.created_at))
    ])
  ];
  return `\ufeff${rows.map((row) => row.map(csvCell).join(",")).join("\n")}\n`;
}

function csvCell(value: unknown) {
  return `"${String(value ?? "").replaceAll('"', '""')}"`;
}

function excelText(value: string) {
  return `\t${value}`;
}

function buildFilters(withPagination: boolean): AuditLogFilters {
  return {
    keyword: filters.keyword,
    actor_scope: filters.actor_scope,
    action: filters.action || "",
    target_type: filters.target_type || "",
    source: filters.source || "",
    sort_order: filters.sort_order,
    start_time: filters.time_range ? new Date(filters.time_range[0]).toISOString() : "",
    end_time: filters.time_range ? new Date(filters.time_range[1]).toISOString() : "",
    page: withPagination ? pagination.page : undefined,
    page_size: withPagination ? pagination.pageSize : undefined
  };
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
  const source = singleFilterValue(filterState, "source");
  filters.actor_scope = isActorScope(actorScope) && (actorScope === "self" || canViewAllLogs.value) ? actorScope : "self";
  filters.action = typeof action === "string" ? action : null;
  filters.target_type = typeof targetType === "string" ? targetType : null;
  filters.source = typeof source === "string" ? source : null;
  pagination.page = 1;
  void loadLogs();
}

function handleSorter(sortState: DataTableSortState | DataTableSortState[] | null) {
  const state = Array.isArray(sortState) ? sortState[0] : sortState;
  filters.sort_order = state?.order === "ascend" ? "ascend" : "descend";
  pagination.page = 1;
  void loadLogs();
}

function handleColumnResize(_: number, limitedWidth: number, column: { key?: string | number }) {
  updateColumnWidth(auditLogColumnWidths, column.key, auditLogColumnWidthKeys, limitedWidth);
}

function openLogDetail(row: AuditLogItem) {
  selectedLog.value = row;
  showDetailModal.value = true;
}

function isActorScope(value: unknown): value is AuditActorScope {
  return value === "self" || value === "all";
}

function messagePathKeys(value: unknown, prefix = ""): string[] {
  if (!isRecord(value)) return prefix ? [prefix] : [];
  return Object.entries(value).flatMap(([key, item]) => messagePathKeys(item, prefix ? `${prefix}.${key}` : key));
}

function distinctActionOptions(values: string[]) {
  return Array.from(new Set(values.filter(Boolean))).map((value) => ({ label: actionLabel(value), value }));
}

function distinctTargetOptions(values: string[]) {
  return Array.from(new Set(values.filter(Boolean))).map((value) => ({ label: targetTypeLabel(value), value }));
}

function distinctSourceOptions(values: string[]) {
  return Array.from(new Set(values.filter(Boolean))).map((value) => ({ label: sourceLabel(value), value }));
}

function actionLabel(action: string) {
  const key = `auditLog.action.${action}`;
  return hasI18nKey(key) ? t(key) : action;
}

function targetTypeLabel(targetType: string) {
  if (!targetType) return t("common.none");
  const key = `auditLog.target.${targetType}`;
  return hasI18nKey(key) ? t(key) : targetType;
}

function sourceLabel(source: string) {
  const key = `auditLog.source.${source}`;
  return hasI18nKey(key) ? t(key) : source || t("common.none");
}

function detailSummary(row: AuditLogItem) {
  const changes = detailChanges(row);
  if (changes.length === 1) {
    const change = changes[0];
    return `${fieldLabel(change.field)}${t("common.labelSeparator")}${compactDetailValue(change.before)} -> ${compactDetailValue(change.after)}`;
  }
  if (changes.length > 1) {
    const fields = changes.slice(0, 2).map((change) => fieldLabel(change.field)).join(t("common.listSeparator"));
    return t("auditLog.changeSummary", { fields, count: changes.length });
  }
  const targetName = detailTargetName(row);
  return targetName ? `${actionLabel(row.action)}${t("common.labelSeparator")}${targetName}` : row.detail || t("common.none");
}

function detailChanges(row: AuditLogItem): AuditLogDetailChange[] {
  return Array.isArray(row.detail_data?.changes) ? row.detail_data.changes.filter((change) => typeof change.field === "string") : [];
}

function detailMetaEntries(row: AuditLogItem) {
  const meta = row.detail_data?.meta;
  if (!meta) return [];
  return Object.entries(meta).map(([key, value]) => ({ key, value }));
}

function detailTargetName(row: AuditLogItem) {
  return row.detail_data?.target_name || row.detail || t("common.none");
}

function fieldLabel(field: string) {
  const key = `auditLog.field.${field}`;
  return hasI18nKey(key) ? t(key) : field.replaceAll("_", " ");
}

function compactDetailValue(value: unknown) {
  const text = formatDetailValue(value);
  return text.length > 64 ? `${text.slice(0, 64)}...` : text;
}

function formatDetailValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return t("common.none");
  if (typeof value === "boolean") return value ? t("common.yes") : t("common.no");
  if (Array.isArray(value)) {
    return value.length ? value.map((item) => formatDetailValue(item)).join(t("common.listSeparator")) : t("common.none");
  }
  if (isRecord(value)) {
    const entries = Object.entries(value);
    if (!entries.length) return t("common.none");
    return entries.map(([key, item]) => `${fieldLabel(key)}${t("common.labelSeparator")}${formatDetailValue(item)}`).join(t("common.messageSeparator"));
  }
  if (typeof value === "string") return valueLabel(value);
  return String(value);
}

function valueLabel(value: string) {
  const statusKey = `status.${value}`;
  if (hasI18nKey(statusKey)) return t(statusKey);
  return localeLabelMap.value[value] || value;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function formatTime(value: string) {
  return formatDateTime(value);
}
</script>
