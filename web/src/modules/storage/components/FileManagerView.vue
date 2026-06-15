<template>
  <section class="work-card table-page-card file-manager-view">
    <div class="toolbar file-manager-toolbar">
      <n-button size="small" quaternary @click="emit('close')">
        <template #icon><n-icon :component="ArrowLeft20Regular" /></template>
      </n-button>
      <span class="file-manager-title">{{ connection.name }}</span>
      <n-tag size="small" :bordered="false">{{ connection.protocol.toUpperCase() }}</n-tag>
      <n-breadcrumb class="file-manager-breadcrumb" separator="/">
        <n-breadcrumb-item @click="navigateTo('/')">
          <n-icon :component="Folder20Regular" />
        </n-breadcrumb-item>
        <n-breadcrumb-item v-for="crumb in breadcrumbs" :key="crumb.path" @click="navigateTo(crumb.path)">
          {{ crumb.name }}
        </n-breadcrumb-item>
      </n-breadcrumb>
      <div class="file-manager-spacer" />
      <n-popover trigger="click" placement="bottom-end" :width="280">
        <template #trigger>
          <n-button>
            <template #icon><n-icon :component="Search20Regular" /></template>
            {{ t("common.search") }}
          </n-button>
        </template>
        <div class="file-search-panel">
          <n-input v-model:value="keyword" :placeholder="t('storage.files.search')" clearable @keyup.enter="search" @clear="clearSearch" />
          <n-checkbox v-model:checked="recursive" size="small">{{ t("storage.files.includeSubdirs") }}</n-checkbox>
          <n-button type="primary" block @click="search">{{ t("common.search") }}</n-button>
        </div>
      </n-popover>
      <n-button @click="refresh">{{ t("common.refresh") }}</n-button>
      <permission-button :permission="STORAGE_OPERATE" :loading="uploading" @click="pickFiles">{{ t("storage.files.upload") }}</permission-button>
      <permission-button :permission="STORAGE_OPERATE" @click="openMkdir">{{ t("storage.files.mkdir") }}</permission-button>
      <permission-button v-if="clipboard" :permission="STORAGE_OPERATE" :loading="operating" @click="pasteClipboard">
        {{ pasteButtonText }}
      </permission-button>
      <permission-button :permission="STORAGE_OPERATE" type="error" :disabled="selectedEntries.length === 0" :loading="operating" @click="confirmBatchDelete">
        {{ batchDeleteText }}
      </permission-button>
      <input ref="uploadInput" type="file" multiple hidden @change="handleUpload" />
    </div>

    <n-alert v-if="truncated" type="warning" :bordered="false" class="file-truncated-alert">
      {{ t("storage.files.truncated", { count: entries.length }) }}
    </n-alert>

    <n-data-table
      v-model:checked-row-keys="checkedRowKeys"
      class="page-data-table"
      flex-height
      :columns="columns"
      :data="tableData"
      :loading="loading"
      :row-key="(row) => row.path"
      size="small"
      @update:sorter="handleSorter"
    />

    <n-modal v-model:show="nameModal.show" preset="card" class="modal-card" :title="nameModalTitle">
      <n-form class="form-stack inline-form" @submit.prevent>
        <n-form-item :label="t('storage.files.name')">
          <n-input v-model:value="nameModal.value" placeholder="" @keyup.enter="confirmNameModal" />
        </n-form-item>
        <div class="form-actions">
          <n-button @click="nameModal.show = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" :loading="nameModal.saving" @click="confirmNameModal">{{ t("common.save") }}</n-button>
        </div>
      </n-form>
    </n-modal>

    <n-modal v-model:show="conflictModal.show" preset="card" class="modal-card" :title="t('storage.files.pasteConflictTitle')">
      <p class="modal-description">
        {{ t("storage.files.pasteConflictConfirm", { count: conflictModal.count }) }}
      </p>
      <div class="form-actions modal-fixed-actions">
        <n-button @click="cancelConflictPaste">{{ t("common.cancel") }}</n-button>
        <n-button @click="confirmConflictPaste('rename')">{{ t("storage.files.autoRename") }}</n-button>
        <n-button type="primary" @click="confirmConflictPaste('overwrite')">{{ t("storage.files.overwrite") }}</n-button>
      </div>
    </n-modal>

    <aside v-if="uploadPanelVisible && uploadTasks.length" class="upload-progress-panel" :class="{ collapsed: uploadPanelCollapsed }">
      <div class="upload-progress-header">
        <div class="upload-progress-title">
          <strong>{{ t("storage.files.uploadProgressTitle") }}</strong>
          <span>{{ uploadSummaryText }}</span>
        </div>
        <div class="upload-progress-actions">
          <n-button quaternary circle size="tiny" :title="uploadPanelCollapsed ? t('storage.files.expandUploadPanel') : t('storage.files.collapseUploadPanel')" @click="toggleUploadPanel">
            <template #icon>
              <n-icon :component="uploadPanelCollapsed ? ChevronUp20Regular : ChevronDown20Regular" />
            </template>
          </n-button>
          <n-button quaternary circle size="tiny" :title="t('common.close')" @click="closeUploadPanel">
            <template #icon><n-icon :component="Dismiss20Regular" /></template>
          </n-button>
        </div>
        <n-progress class="upload-progress-total" type="line" :percentage="totalUploadPercent" :show-indicator="false" />
      </div>
      <div v-if="!uploadPanelCollapsed" class="upload-progress-body">
        <div v-for="task in uploadTasks" :key="task.id" class="upload-progress-item">
          <div class="upload-progress-item-top">
            <div class="upload-progress-item-main">
              <span class="upload-progress-file-name" :title="task.name">{{ task.name }}</span>
              <span class="upload-progress-file-meta">{{ uploadTaskMeta(task) }}</span>
            </div>
            <n-button v-if="canCancelUploadTask(task)" size="tiny" quaternary type="error" @click="cancelUploadTask(task)">
              {{ t("common.cancel") }}
            </n-button>
          </div>
          <n-progress
            type="line"
            :percentage="taskProgress(task)"
            :status="taskProgressStatus(task)"
            :show-indicator="false"
          />
          <span v-if="task.error" class="upload-progress-error" :title="task.error">{{ task.error }}</span>
        </div>
      </div>
    </aside>
  </section>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from "vue";
import {
  NAlert,
  NBreadcrumb,
  NBreadcrumbItem,
  NButton,
  NCheckbox,
  NDataTable,
  NDropdown,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NModal,
  NPopover,
  NProgress,
  NTag,
  useDialog,
  useMessage
} from "naive-ui";
import type { DataTableColumns, DataTableRowKey, DataTableSortState, DropdownOption } from "naive-ui";
import {
  ArrowLeft20Regular,
  ArrowUp20Regular,
  ChevronDown20Regular,
  ChevronUp20Regular,
  Dismiss20Regular,
  Document20Regular,
  Folder20Regular,
  MoreHorizontal20Regular,
  Search20Regular
} from "@vicons/fluent";

import PermissionButton from "../../../components/PermissionButton.vue";
import { formatDateTime, t } from "../../../i18n";
import { authStore } from "../../../stores/auth";
import { saveBlob } from "../../../utils/download";
import { formatFileSize } from "../../../utils/format";
import { messageText, showError } from "../../../utils/message";
import { withResizableColumns } from "../../../utils/table";
import {
  deleteStorageEntry,
  downloadStorageArchive,
  downloadStorageFile,
  batchDeleteStorageEntries,
  copyStorageEntries,
  listStorageFiles,
  mkdirStorage,
  moveStorageEntries,
  renameStorageEntry,
  uploadStorageFile,
  type StorageConnection,
  type StorageConflictPolicy,
  type StorageEntry
} from "../api";
import { STORAGE_OPERATE } from "../permissions";

const PARENT_ROW_PATH = "__parent__";

const props = defineProps<{ connection: StorageConnection }>();
const emit = defineEmits<{ (event: "close"): void }>();

const message = useMessage();
const dialog = useDialog();
const loading = ref(false);
const operating = ref(false);
const uploading = ref(false);
const path = ref("/");
const keyword = ref("");
const recursive = ref(true);
const searchActive = ref(false);
const sortState = ref<{ columnKey: string; order: "ascend" | "descend" } | null>(null);
const truncated = ref(false);
const entries = ref<StorageEntry[]>([]);
const checkedRowKeys = ref<DataTableRowKey[]>([]);
const uploadInput = ref<HTMLInputElement | null>(null);
const uploadPanelVisible = ref(false);
const uploadPanelCollapsed = ref(false);
const nameModal = reactive({
  show: false,
  mode: "mkdir" as "mkdir" | "rename",
  value: "",
  target: null as StorageEntry | null,
  saving: false
});
type ClipboardMode = "copy" | "move";
interface StorageClipboard {
  mode: ClipboardMode;
  sources: StorageEntry[];
}
const clipboard = ref<StorageClipboard | null>(null);
const conflictModal = reactive({
  show: false,
  count: 0
});
type UploadTaskStatus = "pending" | "uploading" | "success" | "failed" | "canceled";
interface UploadTask {
  id: number;
  name: string;
  loaded: number;
  total: number;
  status: UploadTaskStatus;
  error: string;
  controller: AbortController | null;
}
const uploadTasks = ref<UploadTask[]>([]);
let uploadTaskId = 0;

const storageId = computed(() => props.connection.storage_id);
const canOperate = computed(() => authStore.has(STORAGE_OPERATE));
const breadcrumbs = computed(() => {
  const segments = path.value.split("/").filter(Boolean);
  return segments.map((name, index) => ({ name, path: "/" + segments.slice(0, index + 1).join("/") }));
});
const nameModalTitle = computed(() =>
  nameModal.mode === "mkdir" ? t("storage.files.mkdir") : t("storage.files.renameTitle")
);
const showParentRow = computed(() => !searchActive.value);
const sortedEntries = computed<StorageEntry[]>(() => {
  const state = sortState.value;
  if (!state) return entries.value;
  const list = [...entries.value];
  list.sort((a, b) => {
    const cmp =
      state.columnKey === "size"
        ? a.size - b.size
        : (a.modified_at || "").localeCompare(b.modified_at || "");
    return state.order === "ascend" ? cmp : -cmp;
  });
  return list;
});
const tableData = computed<StorageEntry[]>(() => {
  if (!showParentRow.value) return sortedEntries.value;
  const parentRow: StorageEntry = { name: "..", path: PARENT_ROW_PATH, is_dir: true, size: -1, modified_at: "" };
  return [parentRow, ...sortedEntries.value];
});
const selectedEntries = computed(() => {
  const selected = new Set(checkedRowKeys.value.map(String));
  return entries.value.filter((entry) => selected.has(entry.path));
});
const batchDeleteText = computed(() =>
  selectedEntries.value.length > 0
    ? t("storage.files.batchDeleteCount", { count: selectedEntries.value.length })
    : t("storage.files.batchDelete")
);
const pasteButtonText = computed(() => {
  if (!clipboard.value) return t("storage.files.paste");
  return clipboard.value.mode === "move"
    ? t("storage.files.pasteMove", { count: clipboard.value.sources.length })
    : t("storage.files.pasteCopy", { count: clipboard.value.sources.length });
});
const totalUploadPercent = computed(() => {
  const total = uploadTasks.value.reduce((sum, task) => sum + task.total, 0);
  if (total <= 0) {
    const finished = uploadTasks.value.filter(isUploadTaskFinished).length;
    return uploadTasks.value.length > 0 ? Math.round((finished / uploadTasks.value.length) * 100) : 0;
  }
  const loaded = uploadTasks.value.reduce((sum, task) => {
    if (isUploadTaskFinished(task)) return sum + task.total;
    return sum + Math.min(task.loaded, task.total);
  }, 0);
  return Math.round((loaded / total) * 100);
});
const uploadSummaryText = computed(() => {
  const finished = uploadTasks.value.filter((task) => task.status === "success").length;
  const failed = uploadTasks.value.filter((task) => task.status === "failed").length;
  const canceled = uploadTasks.value.filter((task) => task.status === "canceled").length;
  const total = uploadTasks.value.length;
  if (failed > 0 && canceled > 0) {
    return t("storage.files.uploadProgressWithIssues", { done: finished, failed, canceled, total });
  }
  if (failed > 0) {
    return t("storage.files.uploadProgressWithFailed", { done: finished, failed, total });
  }
  if (canceled > 0) {
    return t("storage.files.uploadProgressWithCanceled", { done: finished, canceled, total });
  }
  return t("storage.files.uploadProgressCount", { done: finished, total });
});
const columns = computed<DataTableColumns<StorageEntry>>(() => {
  const list: DataTableColumns<StorageEntry> = [
    ...(canOperate.value
      ? [
          {
            type: "selection" as const,
            disabled: (row: StorageEntry) => row.path === PARENT_ROW_PATH
          }
        ]
      : []),
    {
      title: t("storage.files.name"),
      key: "name",
      ellipsis: { tooltip: true },
      render: (row) => {
        if (row.path === PARENT_ROW_PATH) {
          const disabled = path.value === "/";
          return h(
            "span",
            {
              class: disabled
                ? "file-entry file-entry-parent file-entry-disabled"
                : "file-entry file-entry-dir file-entry-parent",
              onClick: disabled ? undefined : goUp
            },
            [h(NIcon, { component: ArrowUp20Regular }), h("span", null, "..")]
          );
        }
        return h(
          "span",
          {
            class: row.is_dir ? "file-entry file-entry-dir" : "file-entry",
            onClick: row.is_dir ? () => openDir(row) : undefined
          },
          [h(NIcon, { component: row.is_dir ? Folder20Regular : Document20Regular }), h("span", null, row.name)]
        );
      }
    },
    {
      title: t("storage.files.size"),
      key: "size",
      width: 96,
      sorter: true,
      sortOrder: sortState.value?.columnKey === "size" ? sortState.value.order : false,
      render: (row) => (row.path === PARENT_ROW_PATH || row.is_dir ? "-" : formatSize(row.size))
    },
    {
      title: t("storage.files.modifiedAt"),
      key: "modified_at",
      width: 160,
      sorter: true,
      sortOrder: sortState.value?.columnKey === "modified_at" ? sortState.value.order : false,
      render: (row) => (row.modified_at ? formatDateTime(row.modified_at) : "-")
    },
    {
      title: t("common.actions"),
      key: "actions",
      width: 88,
      align: "center",
      render: (row) => {
        if (row.path === PARENT_ROW_PATH) return null;
        const options = rowActionOptions();
        return h(
          NDropdown,
          { trigger: "click", placement: "bottom-end", options, onSelect: (key) => handleRowAction(row, String(key)) },
          {
            default: () =>
              h(
                NButton,
                { class: "row-action-button", size: "small", quaternary: true, circle: true, title: t("common.moreActions") },
                { icon: () => h(NIcon, { component: MoreHorizontal20Regular }) }
              )
          }
        );
      }
    }
  ];
  if (searchActive.value) {
    list.splice(1, 0, {
      title: t("storage.files.location"),
      key: "path",
      ellipsis: { tooltip: true },
      render: (row) => parentPath(row.path)
    });
  }
  return withResizableColumns(list);
});

onMounted(load);

async function load() {
  loading.value = true;
  try {
    const useRecursive = searchActive.value && recursive.value;
    const searchPath = useRecursive ? "/" : path.value;
    const result = await listStorageFiles(storageId.value, searchPath, searchActive.value ? keyword.value : "", useRecursive);
    entries.value = result.entries;
    truncated.value = result.truncated;
    syncCheckedRows();
  } catch (error) {
    showError(message, error);
  } finally {
    loading.value = false;
  }
}

function refresh() {
  void load();
}

function search() {
  if (!keyword.value.trim()) {
    clearSearch();
    return;
  }
  searchActive.value = true;
  void load();
}

function clearSearch() {
  keyword.value = "";
  if (searchActive.value) {
    searchActive.value = false;
    void load();
  }
}

function navigateTo(target: string) {
  path.value = target;
  keyword.value = "";
  searchActive.value = false;
  void load();
}

function openDir(entry: StorageEntry) {
  navigateTo(entry.path);
}

function goUp() {
  navigateTo(parentPath(path.value));
}

function handleSorter(options: DataTableSortState | DataTableSortState[] | null) {
  const state = Array.isArray(options) ? options[0] : options;
  if (!state || !state.order) {
    sortState.value = null;
    return;
  }
  sortState.value = { columnKey: String(state.columnKey), order: state.order };
}

function rowActionOptions(): DropdownOption[] {
  const options: DropdownOption[] = [{ label: t("common.download"), key: "download" }];
  if (canOperate.value) {
    options.push(
      { label: t("storage.files.renameTitle"), key: "rename" },
      { label: t("common.copy"), key: "copy" },
      { label: t("storage.files.move"), key: "move" },
      { label: t("common.delete"), key: "delete" }
    );
  }
  return options;
}

function handleRowAction(row: StorageEntry, key: string) {
  if (key === "download") {
    void downloadEntry(row);
    return;
  }
  if (key === "rename") {
    openRename(row);
    return;
  }
  if (key === "copy" || key === "move") {
    setClipboard(key, [row]);
    return;
  }
  if (key === "delete") {
    confirmDelete(row);
  }
}

function setClipboard(mode: ClipboardMode, sources: StorageEntry[]) {
  clipboard.value = { mode, sources: sources.map((entry) => ({ ...entry })) };
  message.success(
    mode === "move"
      ? t("storage.files.movePrepared", { count: sources.length })
      : t("storage.files.copyPrepared", { count: sources.length })
  );
}

function pasteClipboard() {
  if (!clipboard.value) return;
  const conflicts = pasteConflictCount();
  if (conflicts > 0) {
    conflictModal.count = conflicts;
    conflictModal.show = true;
    return;
  }
  void executePaste("error");
}

function confirmConflictPaste(policy: Exclude<StorageConflictPolicy, "error">) {
  conflictModal.show = false;
  void executePaste(policy);
}

function cancelConflictPaste() {
  conflictModal.show = false;
}

async function executePaste(conflictPolicy: StorageConflictPolicy) {
  const current = clipboard.value;
  if (!current) return;
  operating.value = true;
  try {
    const payload = {
      paths: current.sources.map((entry) => entry.path),
      target_dir: path.value,
      conflict_policy: conflictPolicy
    };
    const result =
      current.mode === "move"
        ? await moveStorageEntries(storageId.value, payload)
        : await copyStorageEntries(storageId.value, payload);
    if (current.mode === "move") {
      clipboard.value = null;
    }
    checkedRowKeys.value = [];
    await load();
    message.success(
      current.mode === "move"
        ? t("storage.files.moved", { count: result.length })
        : t("storage.files.copied", { count: result.length })
    );
  } catch (error) {
    showError(message, error);
  } finally {
    operating.value = false;
  }
}

function pasteConflictCount() {
  if (!clipboard.value) return 0;
  const names = new Set(entries.value.map((entry) => entry.name));
  return clipboard.value.sources.filter((entry) => names.has(baseName(entry.path))).length;
}

function confirmBatchDelete() {
  if (selectedEntries.value.length === 0) return;
  dialog.warning({
    title: t("storage.files.batchDeleteTitle"),
    content: t("storage.files.batchDeleteConfirm", { count: selectedEntries.value.length }),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: () => void removeSelectedEntries()
  });
}

async function removeSelectedEntries() {
  const paths = selectedEntries.value.map((entry) => entry.path);
  if (!paths.length) return;
  operating.value = true;
  try {
    const result = await batchDeleteStorageEntries(storageId.value, paths);
    checkedRowKeys.value = [];
    await load();
    message.success(messageText(result, "storage.entriesDeleted"));
  } catch (error) {
    showError(message, error);
  } finally {
    operating.value = false;
  }
}

function syncCheckedRows() {
  const available = new Set(entries.value.map((entry) => entry.path));
  checkedRowKeys.value = checkedRowKeys.value.filter((key) => available.has(String(key)));
}

function pickFiles() {
  uploadInput.value?.click();
}

async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files ?? []);
  input.value = "";
  if (!files.length) return;
  uploadTasks.value = files.map((file) => ({
    id: ++uploadTaskId,
    name: file.name,
    loaded: 0,
    total: file.size,
    status: "pending",
    error: "",
    controller: null
  }));
  uploadPanelVisible.value = true;
  uploadPanelCollapsed.value = false;
  uploading.value = true;
  let uploaded = 0;
  try {
    for (const [index, file] of files.entries()) {
      const task = uploadTasks.value[index];
      if (task.status === "canceled") continue;
      const controller = new AbortController();
      task.controller = controller;
      task.status = "uploading";
      try {
        await uploadStorageFile(storageId.value, path.value, file, (progress) => {
          task.loaded = progress.loaded;
          task.total = progress.total || file.size || progress.loaded;
        }, controller.signal);
        task.loaded = task.total || file.size;
        task.status = "success";
        uploaded += 1;
      } catch (error) {
        if (isUploadCanceled(error)) {
          task.status = "canceled";
          task.error = "";
          continue;
        }
        const reason = error instanceof Error ? error.message : "";
        task.status = "failed";
        task.error = reason || t("api.requestFailed");
        task.loaded = 0;
        message.error(t("storage.files.uploadFailed", { name: file.name }) + (reason ? t("common.labelSeparator") + reason : ""));
      } finally {
        task.controller = null;
      }
    }
    if (uploaded > 0) {
      message.success(t("storage.files.uploaded", { count: uploaded }));
      await load();
    }
  } finally {
    uploading.value = false;
    if (!uploadPanelVisible.value) {
      uploadTasks.value = [];
    }
  }
}

function taskProgress(task: UploadTask) {
  if (task.status === "success") return 100;
  return task.total > 0 ? Math.round((Math.min(task.loaded, task.total) / task.total) * 100) : 0;
}

function taskProgressStatus(task: UploadTask) {
  if (task.status === "failed") return "error";
  if (task.status === "success") return "success";
  if (task.status === "canceled") return "warning";
  return "default";
}

function uploadTaskMeta(task: UploadTask) {
  if (task.status === "canceled") return t("storage.files.uploadStatusCanceled");
  if (task.status === "failed") return t("storage.files.uploadStatusFailed");
  if (task.status === "success") return t("storage.files.uploadStatusSuccess");
  if (task.status === "pending") return t("storage.files.uploadStatusPending");
  return `${formatSize(Math.min(task.loaded, task.total))} / ${formatSize(task.total)}`;
}

function canCancelUploadTask(task: UploadTask) {
  return task.status === "pending" || task.status === "uploading";
}

function cancelUploadTask(task: UploadTask) {
  if (task.status === "pending") {
    task.status = "canceled";
    return;
  }
  task.controller?.abort();
}

function toggleUploadPanel() {
  uploadPanelCollapsed.value = !uploadPanelCollapsed.value;
}

function closeUploadPanel() {
  uploadPanelVisible.value = false;
  if (!uploadTasks.value.some((task) => !isUploadTaskFinished(task))) {
    uploadTasks.value = [];
  }
}

function isUploadTaskFinished(task: UploadTask) {
  return task.status === "success" || task.status === "failed" || task.status === "canceled";
}

function isUploadCanceled(error: unknown) {
  return error instanceof Error && error.name === "AbortError";
}

async function downloadEntry(entry: StorageEntry) {
  try {
    if (entry.is_dir) {
      saveBlob(await downloadStorageArchive(storageId.value, entry.path), `${entry.name}.zip`);
    } else {
      saveBlob(await downloadStorageFile(storageId.value, entry.path), entry.name);
    }
  } catch (error) {
    showError(message, error);
  }
}

function openMkdir() {
  nameModal.mode = "mkdir";
  nameModal.value = "";
  nameModal.target = null;
  nameModal.show = true;
}

function openRename(entry: StorageEntry) {
  nameModal.mode = "rename";
  nameModal.value = entry.name;
  nameModal.target = entry;
  nameModal.show = true;
}

async function confirmNameModal() {
  const name = nameModal.value.trim();
  if (!name) return;
  nameModal.saving = true;
  try {
    if (nameModal.mode === "mkdir") {
      await mkdirStorage(storageId.value, joinPath(path.value, name));
      message.success(t("storage.files.created"));
    } else if (nameModal.target) {
      await renameStorageEntry(storageId.value, nameModal.target.path, name);
      message.success(t("storage.files.renamed"));
    }
    nameModal.show = false;
    await load();
  } catch (error) {
    showError(message, error);
  } finally {
    nameModal.saving = false;
  }
}

function confirmDelete(entry: StorageEntry) {
  dialog.warning({
    title: t("storage.files.deleteTitle"),
    content: entry.is_dir
      ? t("storage.files.deleteDirConfirm", { name: entry.name })
      : t("storage.files.deleteFileConfirm", { name: entry.name }),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: () => void removeEntry(entry)
  });
}

async function removeEntry(entry: StorageEntry) {
  try {
    const result = await deleteStorageEntry(storageId.value, entry.path);
    message.success(messageText(result, "storage.entryDeleted"));
    await load();
  } catch (error) {
    showError(message, error);
  }
}

function joinPath(parent: string, name: string) {
  return parent === "/" ? `/${name}` : `${parent}/${name}`;
}

function parentPath(value: string) {
  const index = value.lastIndexOf("/");
  return index <= 0 ? "/" : value.slice(0, index);
}

function baseName(value: string) {
  const parts = value.split("/").filter(Boolean);
  return parts[parts.length - 1] || "";
}

const formatSize = formatFileSize;
</script>
