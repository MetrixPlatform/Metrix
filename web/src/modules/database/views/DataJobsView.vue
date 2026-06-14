<template>
  <section class="work-card table-page-card">
    <div class="toolbar">
      <div class="toolbar-title-row">
        <n-button v-if="props.embedded" size="small" quaternary @click="emit('close')">{{ t("common.back") }}</n-button>
        <span class="database-workbench-title">{{ t("database.jobs.view") }}</span>
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
      @update:filters="handleTableFilters"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
      @update:sorter="handleSorter"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, h, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { Delete20Regular, ArrowDownload20Regular } from "@vicons/fluent";
import { NButton, NDataTable, NIcon, NSpace, NTag, useDialog, useMessage } from "naive-ui";
import type { DataTableColumns, DataTableFilterState, DataTableSortState } from "naive-ui";

import { formatDateTime, t } from "../../../i18n";
import { saveBlob } from "../../../utils/download";
import { formatFileSize } from "../../../utils/format";
import { showError } from "../../../utils/message";
import { singleFilterValue } from "../../../utils/table";
import { deleteDataJob, downloadDataJob, listDataJobs, type DataJob } from "../api";

const props = defineProps<{ embedded?: boolean }>();
const emit = defineEmits<{ (event: "close"): void }>();

const message = useMessage();
const dialog = useDialog();
const loading = ref(false);
const items = ref<DataJob[]>([]);
const filters = reactive({
  kind: null as string | null,
  status: null as string | null,
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
  {
    title: t("database.jobs.kind"),
    key: "kind",
    width: 90,
    filterOptions: kindOptions.value,
    filterOptionValue: filters.kind,
    filterMultiple: false,
    filter: true,
    render: (row) => t(`database.jobs.${row.kind}`)
  },
  { title: t("field.format"), key: "format", width: 90, render: (row) => row.format.toUpperCase() },
  {
    title: t("database.jobs.status"),
    key: "status",
    width: 110,
    filterOptions: statusOptions.value,
    filterOptionValue: filters.status,
    filterMultiple: false,
    filter: true,
    render: (row) => h(NTag, { size: "small", type: statusType(row.status) }, () => t(`database.jobs.${row.status}`))
  },
  { title: t("database.jobs.rows"), key: "row_count", width: 100 },
  { title: t("database.jobs.size"), key: "file_size", width: 120, render: (row) => formatSize(row.file_size) },
  { title: t("field.createdAt"), key: "created_at", width: 170, sorter: true, sortOrder: filters.sort_order, render: (row) => formatDateTime(row.created_at) },
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

function handleTableFilters(next: DataTableFilterState) {
  filters.kind = singleFilterValue(next, "kind") as string | null;
  filters.status = singleFilterValue(next, "status") as string | null;
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
  return formatFileSize(value);
}
</script>
