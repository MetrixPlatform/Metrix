<template>
  <section class="work-card table-page-card container-page">
    <div class="container-engine-card">
      <div>
        <div class="container-engine-title">{{ t("container.engine") }}</div>
        <div class="container-engine-meta">
          <n-tag :type="engineStatus.available ? 'success' : 'error'" size="small">
            {{ engineStatus.available ? t("container.connected") : t("container.disconnected") }}
          </n-tag>
          <span>{{ t("container.dockerHost") }}: {{ engineStatus.docker_host || "-" }}</span>
          <span v-if="engineStatus.version">{{ t("container.version") }}: {{ engineStatus.version }}</span>
          <span v-if="engineStatus.os_type">{{ t("container.osType") }}: {{ engineStatus.os_type }}</span>
        </div>
        <n-alert v-if="!engineStatus.available" class="container-engine-alert" type="warning" :show-icon="false">
          <div>{{ engineStatus.message || t("container.emptyHint") }}</div>
          <div>{{ t("container.socketHint") }}</div>
        </n-alert>
      </div>
      <n-button :loading="statusLoading" @click="refreshAll">{{ t("common.refresh") }}</n-button>
    </div>

    <n-tabs v-model:value="activeTab" type="line" animated>
      <n-tab-pane name="containers" :tab="t('container.tabContainers')">
        <div class="toolbar">
          <div class="table-filter-row">
            <n-input
              v-model:value="containerFilters.keyword"
              class="filter-keyword"
              clearable
              :placeholder="t('container.searchContainer')"
              @clear="() => void loadContainers()"
              @keyup.enter="() => void loadContainers()"
            />
            <n-select
              v-model:value="containerFilters.status"
              class="container-filter-select"
              clearable
              :placeholder="t('container.statusAll')"
              :options="statusOptions"
              @update:value="() => void loadContainers()"
            />
            <n-button @click="() => void loadContainers()">{{ t("common.search") }}</n-button>
          </div>
          <permission-button :permission="CONTAINER_CREATE" type="primary" @click="showCreate = true">{{ t("container.create") }}</permission-button>
        </div>
        <n-data-table
          class="page-data-table"
          remote
          :columns="containerColumns"
          :data="containers"
          :loading="containersLoading"
          :pagination="containerPagination"
          :row-key="(row) => row.id"
          :scroll-x="containerTableScrollX"
          @unstable-column-resize="handleContainerColumnResize"
          @update:page="(page) => loadContainers(page)"
          @update:page-size="handleContainerPageSize"
        />
      </n-tab-pane>

      <n-tab-pane name="images" :tab="t('container.tabImages')">
        <div class="toolbar">
          <div class="table-filter-row">
            <n-input
              v-model:value="imageFilters.keyword"
              class="filter-keyword"
              clearable
              :placeholder="t('container.searchImage')"
              @clear="() => void loadImages()"
              @keyup.enter="() => void loadImages()"
            />
            <n-button @click="() => void loadImages()">{{ t("common.search") }}</n-button>
          </div>
          <permission-button :permission="CONTAINER_CREATE" type="primary" @click="showImport = true">{{ t("container.importImage") }}</permission-button>
        </div>
        <n-data-table
          class="page-data-table"
          remote
          :columns="imageColumns"
          :data="images"
          :loading="imagesLoading"
          :pagination="imagePagination"
          :row-key="(row) => row.id"
          :scroll-x="imageTableScrollX"
          @unstable-column-resize="handleImageColumnResize"
          @update:page="(page) => loadImages(page)"
          @update:page-size="handleImagePageSize"
        />
      </n-tab-pane>

      <n-tab-pane name="jobs" :tab="t('container.tabJobs')">
        <div class="toolbar">
          <div class="table-filter-row">
            <n-input
              v-model:value="jobFilters.keyword"
              class="filter-keyword"
              clearable
              :placeholder="t('container.searchJob')"
              @clear="() => void loadJobs()"
              @keyup.enter="() => void loadJobs()"
            />
            <n-button @click="() => void loadJobs()">{{ t("common.search") }}</n-button>
          </div>
        </div>
        <n-data-table
          class="page-data-table"
          remote
          :columns="jobColumns"
          :data="jobs"
          :loading="jobsLoading"
          :pagination="jobPagination"
          :row-key="(row) => row.job_id"
          :scroll-x="jobTableScrollX"
          @unstable-column-resize="handleJobColumnResize"
          @update:page="(page) => loadJobs(page)"
          @update:page-size="handleJobPageSize"
        />
      </n-tab-pane>
    </n-tabs>

    <container-create-modal v-model:show="showCreate" :images="images" @saved="handleContainerSaved" />
    <container-log-modal v-model:show="showLogs" :container="logContainer" />
    <image-import-modal v-model:show="showImport" @submitted="handleJobSubmitted" />
  </section>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from "vue";
import { NAlert, NButton, NDataTable, NDropdown, NInput, NSelect, NTabPane, NTabs, NTag, useDialog, useMessage } from "naive-ui";
import type { DataTableColumns, DropdownOption } from "naive-ui";

import PermissionButton from "../../../components/PermissionButton.vue";
import { formatDateTime, t, translateMessage } from "../../../i18n";
import { authStore } from "../../../stores/auth";
import { saveBlob } from "../../../utils/download";
import { formatFileSize } from "../../../utils/format";
import { showError } from "../../../utils/message";
import { sumColumnWidths, updateColumnWidth, withResizableColumns } from "../../../utils/table";
import {
  deleteContainer,
  deleteImage,
  downloadContainerJob,
  exportImage,
  getContainerEngineStatus,
  listContainerJobs,
  listContainers,
  listImages,
  restartContainer,
  startContainer,
  stopContainer,
  updateImageVisibility,
  type ContainerEngineStatus,
  type ContainerItem,
  type ContainerJobItem,
  type ImageItem
} from "../api";
import ContainerCreateModal from "../components/ContainerCreateModal.vue";
import ContainerLogModal from "../components/ContainerLogModal.vue";
import ImageImportModal from "../components/ImageImportModal.vue";
import { CONTAINER_CREATE, CONTAINER_DELETE, CONTAINER_MANAGE_OTHERS, CONTAINER_OPERATE, CONTAINER_UPDATE } from "../permissions";

const message = useMessage();
const dialog = useDialog();
const activeTab = ref("containers");
const statusLoading = ref(false);
const containersLoading = ref(false);
const imagesLoading = ref(false);
const jobsLoading = ref(false);
const showCreate = ref(false);
const showImport = ref(false);
const showLogs = ref(false);
const logContainer = ref<ContainerItem | null>(null);
const engineStatus = reactive<ContainerEngineStatus>({
  available: false,
  message: "",
  version: "",
  os_type: "",
  architecture: "",
  docker_host: "",
  containers: 0,
  images: 0
});
const containers = ref<ContainerItem[]>([]);
const images = ref<ImageItem[]>([]);
const jobs = ref<ContainerJobItem[]>([]);
const containerFilters = reactive<{ keyword: string; status: string | null; pageSize: number }>({ keyword: "", status: null, pageSize: 20 });
const imageFilters = reactive({ keyword: "", pageSize: 20 });
const jobFilters = reactive({ keyword: "", pageSize: 20 });
const containerPagination = reactive({ page: 1, pageSize: 20, itemCount: 0, showSizePicker: true, pageSizes: [20, 50, 100, 500] });
const imagePagination = reactive({ page: 1, pageSize: 20, itemCount: 0, showSizePicker: true, pageSizes: [20, 50, 100, 500] });
const jobPagination = reactive({ page: 1, pageSize: 20, itemCount: 0, showSizePicker: true, pageSizes: [20, 50, 100, 500] });
const containerWidths = reactive({ name: 200, id: 160, image: 220, status: 120, ports: 180, owner: 140, created_at: 180, actions: 150 });
const imageWidths = reactive({ repo_tags: 280, id: 180, size: 120, visibility: 120, owner: 140, created_at: 180, actions: 160 });
const jobWidths = reactive({ job_id: 180, kind: 100, image_ref: 220, status: 120, file_name: 220, file_size: 120, created_at: 180, actions: 120 });
const statusOptions = computed(() => ["created", "running", "paused", "restarting", "exited", "dead"].map((value) => ({ label: containerStatus(value), value })));
const canManageOthers = computed(() => authStore.has(CONTAINER_MANAGE_OTHERS));
const containerTableScrollX = computed(() => sumColumnWidths(containerWidths));
const imageTableScrollX = computed(() => sumColumnWidths(imageWidths));
const jobTableScrollX = computed(() => sumColumnWidths(jobWidths));

const containerColumns = computed<DataTableColumns<ContainerItem>>(() =>
  withResizableColumns([
    { title: t("container.field.name"), key: "name", width: containerWidths.name, ellipsis: { tooltip: true } },
    { title: t("container.field.containerId"), key: "id", width: containerWidths.id, ellipsis: { tooltip: true } },
    { title: t("container.field.image"), key: "image", width: containerWidths.image, ellipsis: { tooltip: true } },
    { title: t("container.field.status"), key: "status", width: containerWidths.status, render: (row) => statusTag(row.status) },
    { title: t("container.field.ports"), key: "ports", width: containerWidths.ports, render: (row) => row.ports.join(", ") || "-" },
    { title: t("container.field.owner"), key: "owner", width: containerWidths.owner, render: (row) => row.owner_username || row.owner_user_id || "-" },
    { title: t("container.field.createdAt"), key: "created_at", width: containerWidths.created_at, render: (row) => safeDate(row.created_at) },
    { title: t("common.actions"), key: "actions", width: containerWidths.actions, fixed: "right", render: (row) => actionDropdown(containerActionOptions(row), (key) => handleContainerAction(String(key), row)) }
  ])
);
const imageColumns = computed<DataTableColumns<ImageItem>>(() =>
  withResizableColumns([
    { title: t("container.field.repoTags"), key: "repo_tags", width: imageWidths.repo_tags, render: (row) => row.repo_tags.join(", ") || t("common.none") },
    { title: t("container.field.imageId"), key: "id", width: imageWidths.id, ellipsis: { tooltip: true } },
    { title: t("container.field.size"), key: "size", width: imageWidths.size, render: (row) => formatFileSize(row.size) },
    {
      title: t("container.field.visibility"),
      key: "visibility",
      width: imageWidths.visibility,
      render: (row) => h(NTag, { size: "small", type: row.is_public ? "success" : "default" }, () => row.is_public ? t("container.visibilityPublic") : t("container.visibilityPrivate"))
    },
    { title: t("container.field.owner"), key: "owner", width: imageWidths.owner, render: (row) => row.owner_username || row.owner_user_id || t("container.publicSystemImage") },
    { title: t("container.field.createdAt"), key: "created_at", width: imageWidths.created_at, render: (row) => safeDate(row.created_at) },
    { title: t("common.actions"), key: "actions", width: imageWidths.actions, fixed: "right", render: (row) => actionDropdown(imageActionOptions(row), (key) => handleImageAction(String(key), row)) }
  ])
);
const jobColumns = computed<DataTableColumns<ContainerJobItem>>(() =>
  withResizableColumns([
    { title: t("container.field.jobId"), key: "job_id", width: jobWidths.job_id, ellipsis: { tooltip: true } },
    { title: t("container.field.kind"), key: "kind", width: jobWidths.kind, render: (row) => jobKind(row.kind) },
    { title: t("container.field.image"), key: "image_ref", width: jobWidths.image_ref, ellipsis: { tooltip: true } },
    { title: t("container.field.status"), key: "status", width: jobWidths.status, render: (row) => statusTag(row.status) },
    { title: t("container.field.fileName"), key: "file_name", width: jobWidths.file_name, ellipsis: { tooltip: true } },
    { title: t("container.field.fileSize"), key: "file_size", width: jobWidths.file_size, render: (row) => formatFileSize(row.file_size) },
    { title: t("container.field.createdAt"), key: "created_at", width: jobWidths.created_at, render: (row) => safeDate(row.created_at) },
    { title: t("common.actions"), key: "actions", width: jobWidths.actions, fixed: "right", render: (row) => row.status === "success" && row.kind === "export" ? h(NButton, { size: "tiny", onClick: () => void downloadJob(row) }, () => t("container.download")) : "-" }
  ])
);

onMounted(() => {
  void refreshAll();
});

async function refreshAll() {
  await loadStatus();
  await Promise.all([loadContainers(), loadImages(), loadJobs()]);
}

async function loadStatus() {
  statusLoading.value = true;
  try {
    Object.assign(engineStatus, await getContainerEngineStatus());
  } catch (error) {
    showError(message, error);
  } finally {
    statusLoading.value = false;
  }
}

async function loadContainers(page = 1) {
  containersLoading.value = true;
  try {
    const result = await listContainers({ keyword: containerFilters.keyword, status: containerFilters.status ?? "", page, page_size: containerFilters.pageSize });
    containers.value = result.items;
    containerPagination.page = result.page;
    containerPagination.pageSize = result.page_size;
    containerPagination.itemCount = result.total;
  } catch (error) {
    showError(message, error);
  } finally {
    containersLoading.value = false;
  }
}

async function loadImages(page = 1) {
  imagesLoading.value = true;
  try {
    const result = await listImages({ keyword: imageFilters.keyword, page, page_size: imageFilters.pageSize });
    images.value = result.items;
    imagePagination.page = result.page;
    imagePagination.pageSize = result.page_size;
    imagePagination.itemCount = result.total;
  } catch (error) {
    showError(message, error);
  } finally {
    imagesLoading.value = false;
  }
}

async function loadJobs(page = 1) {
  jobsLoading.value = true;
  try {
    const result = await listContainerJobs({ keyword: jobFilters.keyword, page, page_size: jobFilters.pageSize });
    jobs.value = result.items;
    jobPagination.page = result.page;
    jobPagination.pageSize = result.page_size;
    jobPagination.itemCount = result.total;
  } catch (error) {
    showError(message, error);
  } finally {
    jobsLoading.value = false;
  }
}

function handleContainerPageSize(pageSize: number) {
  containerFilters.pageSize = pageSize;
  void loadContainers(1);
}

function handleImagePageSize(pageSize: number) {
  imageFilters.pageSize = pageSize;
  void loadImages(1);
}

function handleJobPageSize(pageSize: number) {
  jobFilters.pageSize = pageSize;
  void loadJobs(1);
}

async function handleContainerAction(key: string, row: ContainerItem) {
  try {
    if (key === "logs") {
      logContainer.value = row;
      showLogs.value = true;
      return;
    }
    if (key === "start") await startContainer(row.id);
    else if (key === "stop") await stopContainer(row.id);
    else if (key === "restart") await restartContainer(row.id);
    else if (key === "delete") {
      confirm(t("container.deleteContainerConfirm", { name: row.name }), async () => {
        await deleteContainer(row.id, true);
        message.success(t("container.deleted"));
        await loadContainers(containerPagination.page);
      });
      return;
    }
    message.success(t(containerActionMessage(key)));
    await loadContainers(containerPagination.page);
  } catch (error) {
    showError(message, error);
  }
}

async function handleImageAction(key: string, row: ImageItem) {
  try {
    const ref = imageRef(row);
    if (key === "export") {
      await exportImage(ref);
      message.success(t("container.submitted"));
      await loadJobs(1);
      activeTab.value = "jobs";
      return;
    }
    if (key === "public" || key === "private") {
      await updateImageVisibility(ref, key === "public");
      message.success(t("container.visibilityUpdated"));
      await loadImages(imagePagination.page);
      return;
    }
    if (key === "delete") {
      confirm(t("container.deleteImageConfirm", { name: ref }), async () => {
        await deleteImage(ref);
        message.success(t("container.imageDeleted"));
        await loadImages(imagePagination.page);
      });
    }
  } catch (error) {
    showError(message, error);
  }
}

async function downloadJob(row: ContainerJobItem) {
  try {
    saveBlob(await downloadContainerJob(row.job_id), row.file_name || `${row.job_id}.tar`);
  } catch (error) {
    showError(message, error);
  }
}

function handleContainerSaved() {
  void loadContainers(1);
}

function handleJobSubmitted() {
  activeTab.value = "jobs";
  void loadJobs(1);
  void loadImages(1);
}

function actionDropdown(options: DropdownOption[], onSelect: (key: string | number) => void) {
  return h(NDropdown, { trigger: "click", options, onSelect }, { default: () => h(NButton, { size: "tiny" }, () => t("common.actions")) });
}

function containerActionOptions(row: ContainerItem): DropdownOption[] {
  const options: DropdownOption[] = [{ label: t("container.logs"), key: "logs" }];
  if (authStore.has(CONTAINER_OPERATE)) {
    if (row.status !== "running") options.push({ label: t("container.start"), key: "start" });
    if (row.status === "running") options.push({ label: t("container.stop"), key: "stop" });
    options.push({ label: t("container.restart"), key: "restart" });
  }
  if (authStore.has(CONTAINER_DELETE)) options.push({ label: t("container.deleteContainer"), key: "delete" });
  return options;
}

function imageActionOptions(row: ImageItem): DropdownOption[] {
  const options: DropdownOption[] = [];
  options.push({ label: t("container.exportImage"), key: "export" });
  if (canManageOthers.value && authStore.has(CONTAINER_UPDATE)) {
    options.push({ label: row.is_public ? t("container.setPrivate") : t("container.setPublic"), key: row.is_public ? "private" : "public" });
  }
  if (canDeleteImage(row)) options.push({ label: t("container.deleteImage"), key: "delete" });
  return options;
}

function canDeleteImage(row: ImageItem) {
  if (!authStore.has(CONTAINER_DELETE)) return false;
  if (canManageOthers.value) return true;
  return row.owner_user_id !== null && row.owner_user_id === authStore.user?.id;
}

function confirm(content: string, onConfirm: () => Promise<void>) {
  dialog.warning({ title: t("common.confirm"), content, positiveText: t("common.delete"), negativeText: t("common.cancel"), onPositiveClick: onConfirm });
}

function statusTag(status: string) {
  const type = status === "running" || status === "success" ? "success" : status === "failed" || status === "dead" ? "error" : "default";
  return h(NTag, { size: "small", type }, () => containerStatus(status));
}

function jobKind(kind: string) {
  return translateMessage(`container.jobKind${capitalize(kind)}`, {}, kind);
}

function containerStatus(status: string) {
  return translateMessage(`container.status${capitalize(status)}`, {}, translateMessage(`container.jobStatus${capitalize(status)}`, {}, status));
}

function containerActionMessage(key: string) {
  if (key === "start") return "container.started";
  if (key === "stop") return "container.stopped";
  if (key === "restart") return "container.restarted";
  return "message.operationSuccess";
}

function capitalize(value: string) {
  return value ? `${value[0].toUpperCase()}${value.slice(1)}` : value;
}

function safeDate(value: string | null | undefined) {
  return value ? formatDateTime(value) : "-";
}

function imageRef(row: ImageItem) {
  return row.repo_tags[0] || row.id;
}

function handleContainerColumnResize(_: number, limitedWidth: number, column: { key?: string | number }) {
  updateColumnWidth(containerWidths, column.key, Object.fromEntries(Object.keys(containerWidths).map((key) => [key, key])), limitedWidth);
}

function handleImageColumnResize(_: number, limitedWidth: number, column: { key?: string | number }) {
  updateColumnWidth(imageWidths, column.key, Object.fromEntries(Object.keys(imageWidths).map((key) => [key, key])), limitedWidth);
}

function handleJobColumnResize(_: number, limitedWidth: number, column: { key?: string | number }) {
  updateColumnWidth(jobWidths, column.key, Object.fromEntries(Object.keys(jobWidths).map((key) => [key, key])), limitedWidth);
}
</script>

<style scoped>
.container-page {
  gap: 14px;
}

.container-engine-card {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--card-color);
}

.container-engine-title {
  margin-bottom: 8px;
  font-weight: 600;
}

.container-engine-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  align-items: center;
  color: var(--text-color-2);
}

.container-engine-alert {
  margin-top: 10px;
}

.container-filter-select {
  width: 160px;
}
</style>
