<template>
  <n-modal
    :show="show"
    preset="card"
    class="modal-card storage-file-modal"
    :title="connection ? `${connection.name} (${connection.storage_id})` : ''"
    @update:show="emit('update:show', $event)"
  >
    <div class="file-manager">
      <div class="toolbar">
        <div class="toolbar-group file-breadcrumb">
          <n-breadcrumb>
            <n-breadcrumb-item @click="navigateTo('/')">/</n-breadcrumb-item>
            <n-breadcrumb-item v-for="crumb in breadcrumbs" :key="crumb.path" @click="navigateTo(crumb.path)">
              {{ crumb.name }}
            </n-breadcrumb-item>
          </n-breadcrumb>
        </div>
        <div class="toolbar-group">
          <n-input
            v-model:value="keyword"
            class="filter-keyword"
            :placeholder="t('storage.files.search')"
            clearable
            @keyup.enter="search"
            @clear="clearSearch"
          />
          <n-button @click="search">{{ t("common.search") }}</n-button>
          <n-button @click="refresh">{{ t("common.refresh") }}</n-button>
          <permission-button :permission="STORAGE_OPERATE" :loading="uploading" @click="pickFiles">
            {{ t("storage.files.upload") }}
          </permission-button>
          <permission-button :permission="STORAGE_OPERATE" @click="openMkdir">{{ t("storage.files.mkdir") }}</permission-button>
          <input ref="uploadInput" type="file" multiple hidden @change="handleUpload" />
        </div>
      </div>

      <n-alert v-if="truncated" type="warning" :bordered="false" class="file-truncated-alert">
        {{ t("storage.files.truncated", { count: entries.length }) }}
      </n-alert>

      <n-data-table
        :columns="columns"
        :data="entries"
        :loading="loading"
        :row-key="(row) => row.path"
        :max-height="420"
        size="small"
      />
    </div>

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
  </n-modal>
</template>

<script setup lang="ts">
import { computed, h, reactive, ref, watch } from "vue";
import {
  NAlert,
  NBreadcrumb,
  NBreadcrumbItem,
  NButton,
  NDataTable,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NModal,
  NSpace,
  useDialog,
  useMessage
} from "naive-ui";
import type { DataTableColumns } from "naive-ui";
import { Document20Regular, Folder20Regular } from "@vicons/fluent";

import PermissionButton from "../../../components/PermissionButton.vue";
import { formatDateTime, t } from "../../../i18n";
import { authStore } from "../../../stores/auth";
import { saveBlob } from "../../../utils/download";
import { messageText, showError } from "../../../utils/message";
import {
  deleteStorageEntry,
  downloadStorageFile,
  listStorageFiles,
  mkdirStorage,
  renameStorageEntry,
  uploadStorageFile,
  type StorageConnection,
  type StorageEntry
} from "../api";
import { STORAGE_OPERATE } from "../permissions";

const props = defineProps<{
  show: boolean;
  connection: StorageConnection | null;
}>();
const emit = defineEmits<{ (event: "update:show", value: boolean): void }>();

const message = useMessage();
const dialog = useDialog();
const loading = ref(false);
const uploading = ref(false);
const path = ref("/");
const keyword = ref("");
const searchActive = ref(false);
const truncated = ref(false);
const entries = ref<StorageEntry[]>([]);
const uploadInput = ref<HTMLInputElement | null>(null);
const nameModal = reactive({
  show: false,
  mode: "mkdir" as "mkdir" | "rename",
  value: "",
  target: null as StorageEntry | null,
  saving: false
});

const storageId = computed(() => props.connection?.storage_id ?? "");
const canOperate = computed(() => authStore.has(STORAGE_OPERATE));
const breadcrumbs = computed(() => {
  const segments = path.value.split("/").filter(Boolean);
  return segments.map((name, index) => ({ name, path: "/" + segments.slice(0, index + 1).join("/") }));
});
const nameModalTitle = computed(() =>
  nameModal.mode === "mkdir" ? t("storage.files.mkdir") : t("storage.files.renameTitle")
);
const columns = computed<DataTableColumns<StorageEntry>>(() => {
  const list: DataTableColumns<StorageEntry> = [
    {
      title: t("storage.files.name"),
      key: "name",
      ellipsis: { tooltip: true },
      render: (row) =>
        h(
          "span",
          {
            class: row.is_dir ? "file-entry file-entry-dir" : "file-entry",
            onClick: row.is_dir ? () => openDir(row) : undefined
          },
          [h(NIcon, { component: row.is_dir ? Folder20Regular : Document20Regular }), h("span", null, row.name)]
        )
    },
    { title: t("storage.files.size"), key: "size", width: 96, render: (row) => (row.is_dir ? "-" : formatSize(row.size)) },
    {
      title: t("storage.files.modifiedAt"),
      key: "modified_at",
      width: 160,
      render: (row) => (row.modified_at ? formatDateTime(row.modified_at) : "-")
    },
    {
      title: t("common.actions"),
      key: "actions",
      width: 168,
      align: "center",
      render: (row) =>
        h(NSpace, { size: 4, wrap: false, justify: "center" }, () => [
          row.is_dir
            ? null
            : h(NButton, { size: "tiny", quaternary: true, onClick: () => void downloadEntry(row) }, () => t("common.download")),
          canOperate.value
            ? h(NButton, { size: "tiny", quaternary: true, onClick: () => openRename(row) }, () => t("storage.files.renameTitle"))
            : null,
          canOperate.value
            ? h(NButton, { size: "tiny", quaternary: true, type: "error", onClick: () => confirmDelete(row) }, () => t("common.delete"))
            : null
        ])
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
  return list;
});

watch(
  () => props.show,
  (visible) => {
    if (visible && props.connection) {
      path.value = "/";
      keyword.value = "";
      searchActive.value = false;
      void load();
    }
  }
);

async function load() {
  if (!storageId.value) return;
  loading.value = true;
  try {
    const result = await listStorageFiles(storageId.value, path.value, searchActive.value ? keyword.value : "", searchActive.value);
    entries.value = result.entries;
    truncated.value = result.truncated;
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
  searchActive.value = Boolean(keyword.value.trim());
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

function pickFiles() {
  uploadInput.value?.click();
}

async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files ?? []);
  input.value = "";
  if (!files.length || !storageId.value) return;
  uploading.value = true;
  let uploaded = 0;
  try {
    for (const file of files) {
      try {
        await uploadStorageFile(storageId.value, path.value, file);
        uploaded += 1;
      } catch (error) {
        const reason = error instanceof Error ? error.message : "";
        message.error(t("storage.files.uploadFailed", { name: file.name }) + (reason ? t("common.labelSeparator") + reason : ""));
      }
    }
    if (uploaded > 0) {
      message.success(t("storage.files.uploaded", { count: uploaded }));
      await load();
    }
  } finally {
    uploading.value = false;
  }
}

async function downloadEntry(entry: StorageEntry) {
  try {
    saveBlob(await downloadStorageFile(storageId.value, entry.path), entry.name);
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

function formatSize(size: number) {
  if (size < 1024) return `${size} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let value = size;
  let unit = "B";
  for (const next of units) {
    if (value < 1024) break;
    value /= 1024;
    unit = next;
  }
  return `${value >= 100 ? Math.round(value) : value.toFixed(1)} ${unit}`;
}
</script>
