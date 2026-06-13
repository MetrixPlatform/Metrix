<template>
  <section class="work-card table-page-card">
    <div class="toolbar">
      <div class="storage-filter-row">
        <n-select v-model:value="filters.kind" class="database-toolbar-select" :options="kindOptions" clearable :placeholder="t('database.jobs.kind')" />
        <n-select v-model:value="filters.status" class="database-toolbar-select" :options="statusOptions" clearable :placeholder="t('database.jobs.status')" />
        <n-button @click="search">{{ t("common.search") }}</n-button>
      </div>
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
      :scroll-x="1050"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, h, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { Delete20Regular, ArrowDownload20Regular } from "@vicons/fluent";
import { NButton, NDataTable, NIcon, NSelect, NSpace, NTag, useDialog, useMessage } from "naive-ui";
import type { DataTableColumns } from "naive-ui";

import { formatDateTime, t } from "../../../i18n";
import { saveBlob } from "../../../utils/download";
import { showError } from "../../../utils/message";
import { deleteDataJob, downloadDataJob, listDataJobs, type DataJob } from "../api";

const message = useMessage();
const dialog = useDialog();
const loading = ref(false);
const items = ref<DataJob[]>([]);
const filters = reactive({ kind: null as string | null, status: null as string | null });
const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  pageSizes: [20, 50, 100, 500],
  showSizePicker: true,
  prefix: ({ itemCount }: { itemCount: number | undefined }) => t("common.total", { count: itemCount ?? 0 })
});
const kindOptions = computed(() => [
  { label: t("database.jobs.export"), value: "export" },
  { label: t("database.jobs.import"), value: "import" }
]);
const statusOptions = computed(() => [
  { label: t("database.jobs.pending"), value: "pending" },
  { label: t("database.jobs.running"), value: "running" },
  { label: t("database.jobs.success"), value: "success" },
  { label: t("database.jobs.failed"), value: "failed" }
]);
const columns = computed<DataTableColumns<DataJob>>(() => [
  { title: t("database.jobs.id"), key: "job_id", width: 260, ellipsis: { tooltip: true } },
  { title: t("database.connection"), key: "connection_name", width: 160, render: (row) => row.connection_name || row.conn_id },
  { title: t("database.jobs.kind"), key: "kind", width: 90, render: (row) => t(`database.jobs.${row.kind}`) },
  { title: t("field.format"), key: "format", width: 90, render: (row) => row.format.toUpperCase() },
  {
    title: t("database.jobs.status"),
    key: "status",
    width: 110,
    render: (row) => h(NTag, { size: "small", type: statusType(row.status) }, () => t(`database.jobs.${row.status}`))
  },
  { title: t("database.jobs.rows"), key: "row_count", width: 100 },
  { title: t("database.jobs.size"), key: "file_size", width: 120, render: (row) => formatSize(row.file_size) },
  { title: t("field.createdAt"), key: "created_at", width: 170, render: (row) => formatDateTime(row.created_at) },
  { title: t("database.jobs.expiresAt"), key: "expires_at", width: 170, render: (row) => (row.expires_at ? formatDateTime(row.expires_at) : "-") },
  { title: t("database.jobs.error"), key: "error_code", minWidth: 160, ellipsis: { tooltip: true }, render: (row) => row.error_code || "-" },
  {
    title: t("common.actions"),
    key: "actions",
    fixed: "right",
    width: 130,
    render: (row) =>
      h(NSpace, { size: 4, justify: "center" }, () => [
        row.kind === "export" && row.status === "success"
          ? h(NButton, { size: "tiny", quaternary: true, onClick: () => void downloadJob(row) }, () => h(NIcon, { component: ArrowDownload20Regular }))
          : null,
        h(NButton, { size: "tiny", quaternary: true, type: "error", onClick: () => confirmDelete(row) }, () => h(NIcon, { component: Delete20Regular }))
      ])
  }
]);
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
      kind: filters.kind || "",
      status: filters.status || "",
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

function search() {
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
      await deleteDataJob(row.job_id);
      await loadJobs();
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

function statusType(status: string) {
  if (status === "success") return "success";
  if (status === "failed") return "error";
  if (status === "running") return "info";
  return "warning";
}

function formatSize(value: number) {
  if (!value) return "-";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(1)} MB`;
}
</script>
