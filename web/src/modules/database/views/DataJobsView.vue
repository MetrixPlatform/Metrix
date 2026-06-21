<template>
  <section class="work-card table-page-card database-jobs-view">
    <div class="toolbar file-manager-toolbar">
      <n-button v-if="props.embedded" size="small" quaternary :title="t('common.back')" :aria-label="t('common.back')" @click="emit('close')">
        <template #icon><n-icon :component="ArrowLeft20Regular" /></template>
      </n-button>
      <span class="file-manager-title">{{ t("database.jobs.view") }}</span>
      <n-tag v-if="activeConnectionId" size="small" type="success" :bordered="false" closable @close="clearConnectionScope">
        {{ t("database.jobs.currentScope", { name: activeConnectionName }) }}
      </n-tag>
      <div class="file-manager-spacer" />
      <n-input
        v-model:value="filters.keyword"
        class="database-job-search"
        clearable
        :placeholder="t('database.jobs.searchPlaceholder')"
        @keyup.enter="searchJobs"
        @clear="resetSearch"
      />
      <n-button type="primary" @click="searchJobs">{{ t("common.search") }}</n-button>
      <n-button @click="loadJobs">{{ t("common.refresh") }}</n-button>
    </div>
    <n-data-table
      class="page-data-table"
      flex-height
      remote
      :columns="columns"
      :data="items"
      :loading="loading"
      :pagination="pagination"
      :row-key="(row) => row.job_id"
      :scroll-x="tableScrollX"
      @unstable-column-resize="handleColumnResize"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
      @update:sorter="handleSorter"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, h, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { ArrowDownload20Regular, ArrowLeft20Regular, Delete20Regular } from "@vicons/fluent";
import { NButton, NDataTable, NIcon, NInput, NTag, useDialog, useMessage } from "naive-ui";
import type { DataTableColumns, DataTableSortState } from "naive-ui";

import { formatDateTime, t } from "../../../i18n";
import { authStore } from "../../../stores/auth";
import { saveBlob } from "../../../utils/download";
import { formatFileSize } from "../../../utils/format";
import { showError } from "../../../utils/message";
import { sumColumnWidths, updateColumnWidth, withResizableColumns } from "../../../utils/table";
import { deleteDataJob, downloadDataJob, listDataJobs, type DataJob } from "../api";
import { DATABASE_MANAGE_OTHERS } from "../permissions";

const props = defineProps<{ embedded?: boolean; connectionId?: number | null; connectionName?: string }>();
const emit = defineEmits<{ (event: "close"): void }>();

const message = useMessage();
const dialog = useDialog();
const loading = ref(false);
const items = ref<DataJob[]>([]);
const activeConnectionId = ref<number | null>(props.connectionId ?? null);
const activeConnectionName = ref(props.connectionName || "");
const filters = reactive({
  keyword: "",
  sort_order: "descend" as "ascend" | "descend"
});
const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  pageSizes: [20, 50, 100, 500],
  showSizePicker: true,
  prefix: ({ itemCount }: { itemCount: number | undefined }) => t("common.total", { count: itemCount ?? 0 })
});
const dataJobColumnWidths = reactive<Record<string, number>>({
  jobId: 260,
  connection: 180,
  creator: 130,
  kind: 90,
  format: 90,
  status: 110,
  rows: 100,
  size: 120,
  createdAt: 180,
  expiresAt: 180,
  error: 180,
  actions: 130
});
const dataJobColumnWidthKeys: Record<string, string> = {
  job_id: "jobId",
  connection_name: "connection",
  created_by: "creator",
  kind: "kind",
  format: "format",
  status: "status",
  row_count: "rows",
  file_size: "size",
  created_at: "createdAt",
  expires_at: "expiresAt",
  error_code: "error"
};
const tableScrollX = computed(() => sumColumnWidths(dataJobColumnWidths));
const columns = computed<DataTableColumns<DataJob>>(() =>
  withResizableColumns([
  { title: t("database.jobs.id"), key: "job_id", width: dataJobColumnWidths.jobId, minWidth: 180, resizable: true, ellipsis: { tooltip: true } },
  {
    title: t("database.connection"),
    key: "connection_name",
    width: dataJobColumnWidths.connection,
    minWidth: 130,
    resizable: true,
    ellipsis: { tooltip: true },
    render: (row) => row.connection_name || row.conn_id
  },
  {
    title: t("field.creator"),
    key: "created_by",
    width: dataJobColumnWidths.creator,
    minWidth: 110,
    resizable: true,
    render: (row) => row.created_by_username || "-"
  },
  {
    title: t("database.jobs.kind"),
    key: "kind",
    width: dataJobColumnWidths.kind,
    minWidth: 80,
    resizable: true,
    render: (row) => t(`database.jobs.${row.kind}`)
  },
  { title: t("field.format"), key: "format", width: dataJobColumnWidths.format, minWidth: 80, resizable: true, render: (row) => row.format.toUpperCase() },
  {
    title: t("database.jobs.status"),
    key: "status",
    width: dataJobColumnWidths.status,
    minWidth: 90,
    resizable: true,
    render: (row) => h(NTag, { size: "small", type: statusType(row.status) }, () => t(`database.jobs.${row.status}`))
  },
  { title: t("database.jobs.rows"), key: "row_count", width: dataJobColumnWidths.rows, minWidth: 90, resizable: true },
  { title: t("database.jobs.size"), key: "file_size", width: dataJobColumnWidths.size, minWidth: 100, resizable: true, render: (row) => formatSize(row.file_size) },
  {
    title: t("field.createdAt"),
    key: "created_at",
    width: dataJobColumnWidths.createdAt,
    minWidth: 150,
    resizable: true,
    sorter: true,
    sortOrder: filters.sort_order,
    render: (row) => formatDateTime(row.created_at)
  },
  {
    title: t("database.jobs.expiresAt"),
    key: "expires_at",
    width: dataJobColumnWidths.expiresAt,
    minWidth: 150,
    resizable: true,
    render: (row) => (row.expires_at ? formatDateTime(row.expires_at) : "-")
  },
  { title: t("database.jobs.error"), key: "error_code", width: dataJobColumnWidths.error, minWidth: 160, resizable: true, ellipsis: { tooltip: true }, render: (row) => row.error_code || "-" },
  {
    title: t("common.actions"),
    key: "actions",
    fixed: "right",
    width: dataJobColumnWidths.actions,
    render: (row) =>
      h("div", { class: "table-action-group" }, [
        row.kind === "export" && row.status === "success"
          ? h(
              NButton,
              { size: "tiny", quaternary: true, circle: true, title: t("common.download"), onClick: () => void downloadJob(row) },
              { icon: () => h(NIcon, { component: ArrowDownload20Regular }) }
            )
          : null,
        canDeleteJob(row)
          ? h(
              NButton,
              { size: "tiny", quaternary: true, circle: true, type: "error", title: t("common.delete"), onClick: () => confirmDelete(row) },
              { icon: () => h(NIcon, { component: Delete20Regular }) }
            )
          : null
      ])
  }
  ])
);
let timer: number | undefined;

onMounted(() => {
  void loadJobs();
  timer = window.setInterval(() => {
    if (items.value.some((item) => item.status === "pending" || item.status === "running")) {
      void loadJobs();
    }
  }, 5000);
});

onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer);
});

async function loadJobs() {
  loading.value = true;
  try {
    const result = await listDataJobs({
      keyword: filters.keyword,
      connection_id: activeConnectionId.value,
      sort_order: filters.sort_order,
      page: pagination.page,
      page_size: pagination.pageSize
    });
    items.value = result.items;
    pagination.itemCount = result.total;
  } catch (error) {
    showError(message, error);
  } finally {
    loading.value = false;
  }
}

function searchJobs() {
  pagination.page = 1;
  void loadJobs();
}

function resetSearch() {
  filters.keyword = "";
  pagination.page = 1;
  void loadJobs();
}

function clearConnectionScope() {
  activeConnectionId.value = null;
  activeConnectionName.value = "";
  pagination.page = 1;
  void loadJobs();
}

function handleSorter(sorter: DataTableSortState | DataTableSortState[] | null) {
  const state = Array.isArray(sorter) ? sorter[0] : sorter;
  filters.sort_order = state?.order === "ascend" ? "ascend" : "descend";
  pagination.page = 1;
  void loadJobs();
}

async function downloadJob(row: DataJob) {
  try {
    saveBlob(await downloadDataJob(row.job_id), row.file_name || `${row.job_id}.${row.format}`);
    await loadJobs();
  } catch (error) {
    showError(message, error);
  }
}

function confirmDelete(row: DataJob) {
  dialog.warning({
    title: t("common.confirm"),
    content: t("database.jobs.deleteConfirm"),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: async () => {
      try {
        await deleteDataJob(row.job_id);
        await loadJobs();
      } catch (error) {
        showError(message, error);
      }
    }
  });
}

function handlePageChange(page: number) {
  pagination.page = page;
  void loadJobs();
}

function handlePageSizeChange(pageSize: number) {
  pagination.pageSize = pageSize;
  pagination.page = 1;
  void loadJobs();
}

function handleColumnResize(_: number, limitedWidth: number, column: { key?: string | number }) {
  updateColumnWidth(dataJobColumnWidths, column.key, dataJobColumnWidthKeys, limitedWidth);
}

function canDeleteJob(row: DataJob) {
  return authStore.has(DATABASE_MANAGE_OTHERS) || row.created_by === authStore.user?.id;
}

function statusType(status: string) {
  if (status === "success") return "success";
  if (status === "failed") return "error";
  if (status === "running") return "info";
  return "warning";
}

function formatSize(value: number) {
  if (!value) return "-";
  return formatFileSize(value);
}
</script>
