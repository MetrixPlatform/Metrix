<template>
  <section class="work-card table-page-card">
    <div class="toolbar">
      <div class="toolbar-group">
        <n-input v-model:value="filters.keyword" class="filter-keyword" :placeholder="t('storage.searchPlaceholder')" clearable />
        <n-select
          v-model:value="filters.protocol"
          class="storage-protocol-filter"
          :options="protocolOptions"
          :placeholder="t('storage.protocolAll')"
          clearable
        />
        <n-button @click="searchConnections">{{ t("common.search") }}</n-button>
      </div>
      <permission-button :permission="STORAGE_CREATE" type="primary" @click="openCreate">{{ t("storage.add") }}</permission-button>
    </div>

    <n-data-table
      class="page-data-table"
      flex-height
      remote
      :columns="columns"
      :data="items"
      :loading="loading"
      :pagination="pagination"
      :row-key="(row) => row.id"
      :scroll-x="tableScrollX"
      @unstable-column-resize="handleColumnResize"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
    />

    <n-modal v-model:show="showModal" preset="card" class="modal-card" :title="editingItem ? t('storage.edit') : t('storage.add')">
      <n-form ref="formRef" class="form-stack inline-form" :model="form" :rules="rules" label-placement="left" label-width="auto">
        <n-form-item :label="t('storage.field.name')" path="name">
          <n-input v-model:value="form.name" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('field.storageId')" path="storage_id">
          <n-input
            v-model:value="form.storage_id"
            :disabled="editingItem !== null"
            :placeholder="editingItem ? '' : t('storage.idPlaceholder')"
          />
        </n-form-item>
        <n-form-item :label="t('field.protocol')" path="protocol">
          <n-radio-group v-model:value="form.protocol" @update:value="handleProtocolChange">
            <n-radio-button value="ftp" label="FTP" />
            <n-radio-button value="sftp" label="SFTP" />
          </n-radio-group>
        </n-form-item>
        <n-form-item :label="t('field.host')" path="host">
          <n-input v-model:value="form.host" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('field.port')" path="port">
          <n-input-number v-model:value="form.port" :min="1" :max="65535" :show-button="false" />
        </n-form-item>
        <n-form-item :label="t('field.username')" path="username">
          <n-input v-model:value="form.username" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('field.password')" path="password">
          <n-input
            v-model:value="form.password"
            type="password"
            show-password-on="click"
            :placeholder="editingItem ? t('storage.passwordKeep') : ''"
          />
        </n-form-item>
        <n-form-item :label="t('field.basePath')" path="base_path">
          <n-input v-model:value="form.base_path" placeholder="/" />
        </n-form-item>
        <n-form-item :label="t('storage.field.shared')" path="is_shared">
          <n-switch v-model:value="form.is_shared">
            <template #checked>{{ t("storage.shared") }}</template>
            <template #unchecked>{{ t("storage.private") }}</template>
          </n-switch>
        </n-form-item>
        <n-form-item :label="t('field.status')" path="is_active">
          <n-switch v-model:value="form.is_active">
            <template #checked>{{ t("common.enabled") }}</template>
            <template #unchecked>{{ t("common.disabled") }}</template>
          </n-switch>
        </n-form-item>
        <div class="form-actions">
          <n-button :loading="testing" @click="testConnection">{{ t("common.test") }}</n-button>
          <n-button @click="showModal = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" :loading="saving" @click="saveConnection">{{ t("common.save") }}</n-button>
        </div>
      </n-form>
    </n-modal>

    <file-manager-modal v-model:show="showFiles" :connection="managingItem" />
  </section>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from "vue";
import {
  NButton,
  NDataTable,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NModal,
  NRadioButton,
  NRadioGroup,
  NSelect,
  NSpace,
  NSwitch,
  NTag,
  useDialog,
  useMessage
} from "naive-ui";
import type { DataTableColumns, FormInst, FormItemRule, FormRules } from "naive-ui";

import PermissionButton from "../../../components/PermissionButton.vue";
import StatusTag from "../../../components/StatusTag.vue";
import { t } from "../../../i18n";
import { authStore } from "../../../stores/auth";
import { copyText } from "../../../utils/clipboard";
import { messageText, showError } from "../../../utils/message";
import { sumColumnWidths, updateColumnWidth, withResizableColumns } from "../../../utils/table";
import { maxLengthRule, numberRequiredRule, requiredRule, validateForm } from "../../../utils/validation";
import {
  createStorage,
  deleteStorage,
  listStorages,
  testStorage,
  updateStorage,
  type StorageConnection,
  type StorageConnectionPayload,
  type StorageProtocol
} from "../api";
import FileManagerModal from "../components/FileManagerModal.vue";
import { STORAGE_CREATE, STORAGE_DELETE, STORAGE_MANAGE_OTHERS, STORAGE_UPDATE } from "../permissions";

const STORAGE_ID_RE = /^[A-Za-z0-9][A-Za-z0-9_-]{2,63}$/;
const DEFAULT_PORTS: Record<StorageProtocol, number> = { ftp: 21, sftp: 22 };

const message = useMessage();
const dialog = useDialog();
const loading = ref(false);
const saving = ref(false);
const testing = ref(false);
const showModal = ref(false);
const showFiles = ref(false);
const formRef = ref<FormInst | null>(null);
const editingItem = ref<StorageConnection | null>(null);
const managingItem = ref<StorageConnection | null>(null);
const items = ref<StorageConnection[]>([]);
const filters = reactive<{ keyword: string; protocol: StorageProtocol | null }>({
  keyword: "",
  protocol: null
});
const form = reactive<StorageConnectionPayload>({
  name: "",
  storage_id: "",
  protocol: "ftp",
  host: "",
  port: 21,
  username: "",
  password: "",
  base_path: "/",
  is_shared: false,
  is_active: true
});
const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  pageSizes: [20, 50, 100, 500],
  showSizePicker: true,
  prefix: ({ itemCount }: { itemCount: number | undefined }) => t("common.total", { count: itemCount ?? 0 })
});
const protocolOptions = computed(() => [
  { label: "FTP", value: "ftp" },
  { label: "SFTP", value: "sftp" }
]);
const rules = computed<FormRules>(() => ({
  name: [requiredRule(t("storage.field.name")), maxLengthRule(t("storage.field.name"), 120)],
  storage_id: storageIdRule(),
  host: [requiredRule(t("field.host")), maxLengthRule(t("field.host"), 255)],
  port: numberRequiredRule(t("field.port")),
  username: [requiredRule(t("field.username")), maxLengthRule(t("field.username"), 120)],
  password: editingItem.value ? maxLengthRule(t("field.password"), 255) : requiredRule(t("field.password")),
  base_path: maxLengthRule(t("field.basePath"), 500)
}));
const columnWidths = reactive<Record<string, number>>({
  name: 150,
  storageId: 190,
  protocol: 90,
  address: 180,
  basePath: 130,
  shared: 90,
  isActive: 90,
  creator: 110,
  actions: 200
});
const columnWidthKeys: Record<string, string> = {
  name: "name",
  storage_id: "storageId",
  protocol: "protocol",
  address: "address",
  base_path: "basePath",
  is_shared: "shared",
  is_active: "isActive",
  created_by_username: "creator"
};
const tableScrollX = computed(() => sumColumnWidths(columnWidths));
const statusLabels = computed(() => ({ true: t("common.enabled"), false: t("common.disabled") }));
const columns = computed<DataTableColumns<StorageConnection>>(() =>
  withResizableColumns([
    { title: t("storage.field.name"), key: "name", width: columnWidths.name, ellipsis: { tooltip: true } },
    {
      title: t("field.storageId"),
      key: "storage_id",
      width: columnWidths.storageId,
      render: (row) =>
        h("span", { class: "copyable-cell" }, [
          h("code", null, row.storage_id),
          h(
            NButton,
            { size: "tiny", quaternary: true, onClick: () => copyStorageId(row.storage_id) },
            () => t("common.copy")
          )
        ])
    },
    {
      title: t("field.protocol"),
      key: "protocol",
      width: columnWidths.protocol,
      render: (row) => h(NTag, { size: "small", bordered: false }, () => row.protocol.toUpperCase())
    },
    { title: t("storage.field.address"), key: "address", width: columnWidths.address, ellipsis: { tooltip: true }, render: (row) => `${row.host}:${row.port}` },
    { title: t("field.basePath"), key: "base_path", width: columnWidths.basePath, ellipsis: { tooltip: true } },
    {
      title: t("storage.field.shared"),
      key: "is_shared",
      width: columnWidths.shared,
      render: (row) =>
        h(
          NTag,
          { size: "small", bordered: false, type: row.is_shared ? "info" : "default" },
          () => (row.is_shared ? t("storage.shared") : t("storage.private"))
        )
    },
    {
      title: t("field.status"),
      key: "is_active",
      width: columnWidths.isActive,
      render: (row) => h(StatusTag, { status: row.is_active, labels: statusLabels.value })
    },
    {
      title: t("field.creator"),
      key: "created_by_username",
      width: columnWidths.creator,
      render: (row) => row.created_by_username || t("common.none")
    },
    {
      title: t("common.actions"),
      key: "actions",
      width: columnWidths.actions,
      fixed: "right",
      align: "center",
      render: (row) =>
        h(NSpace, { size: 6, wrap: false, justify: "center" }, () => [
          h(
            NButton,
            { size: "small", quaternary: true, type: "primary", disabled: !row.is_active, onClick: () => openFiles(row) },
            () => t("storage.manage")
          ),
          canManage(row) && authStore.has(STORAGE_UPDATE)
            ? h(NButton, { size: "small", quaternary: true, onClick: () => openEdit(row) }, () => t("common.edit"))
            : null,
          canManage(row) && authStore.has(STORAGE_DELETE)
            ? h(NButton, { size: "small", quaternary: true, type: "error", onClick: () => confirmDelete(row) }, () => t("common.delete"))
            : null
        ])
    }
  ])
);

onMounted(loadConnections);

async function loadConnections() {
  loading.value = true;
  try {
    const result = await listStorages({
      keyword: filters.keyword,
      protocol: filters.protocol || "",
      page: pagination.page,
      page_size: pagination.pageSize
    });
    items.value = result.items;
    pagination.itemCount = result.total;
    pagination.page = result.page;
    pagination.pageSize = result.page_size;
  } catch (error) {
    showError(message, error);
  } finally {
    loading.value = false;
  }
}

function searchConnections() {
  pagination.page = 1;
  void loadConnections();
}

function handlePageChange(page: number) {
  pagination.page = page;
  void loadConnections();
}

function handlePageSizeChange(pageSize: number) {
  pagination.pageSize = pageSize;
  pagination.page = 1;
  void loadConnections();
}

function handleColumnResize(_: number, limitedWidth: number, column: { key?: string | number }) {
  updateColumnWidth(columnWidths, column.key, columnWidthKeys, limitedWidth);
}

function openCreate() {
  editingItem.value = null;
  Object.assign(form, {
    name: "",
    storage_id: "",
    protocol: "ftp",
    host: "",
    port: 21,
    username: "",
    password: "",
    base_path: "/",
    is_shared: false,
    is_active: true
  });
  showModal.value = true;
}

function openEdit(item: StorageConnection) {
  editingItem.value = item;
  Object.assign(form, {
    name: item.name,
    storage_id: item.storage_id,
    protocol: item.protocol,
    host: item.host,
    port: item.port,
    username: item.username,
    password: "",
    base_path: item.base_path,
    is_shared: item.is_shared,
    is_active: item.is_active
  });
  showModal.value = true;
}

function openFiles(item: StorageConnection) {
  managingItem.value = item;
  showFiles.value = true;
}

function handleProtocolChange(protocol: StorageProtocol) {
  const other: StorageProtocol = protocol === "ftp" ? "sftp" : "ftp";
  if (form.port === DEFAULT_PORTS[other]) {
    form.port = DEFAULT_PORTS[protocol];
  }
}

async function saveConnection() {
  if (!(await validateForm(formRef.value))) return;
  saving.value = true;
  try {
    if (editingItem.value) {
      await updateStorage(editingItem.value.id, { ...form });
    } else {
      await createStorage({ ...form });
    }
    showModal.value = false;
    await loadConnections();
    message.success(t("storage.saved"));
  } catch (error) {
    showError(message, error);
  } finally {
    saving.value = false;
  }
}

async function testConnection() {
  if (!(await validateForm(formRef.value))) return;
  testing.value = true;
  try {
    const result = await testStorage({
      id: editingItem.value?.id ?? null,
      protocol: form.protocol,
      host: form.host,
      port: form.port,
      username: form.username,
      password: form.password,
      base_path: form.base_path
    });
    message.success(messageText(result, "storage.connectionOk"));
  } catch (error) {
    showError(message, error);
  } finally {
    testing.value = false;
  }
}

function confirmDelete(item: StorageConnection) {
  dialog.warning({
    title: t("storage.deleteTitle"),
    content: t("storage.deleteConfirm", { name: item.name }),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: () => void removeConnection(item)
  });
}

async function removeConnection(item: StorageConnection) {
  try {
    const result = await deleteStorage(item.id);
    await loadConnections();
    message.success(messageText(result, "storage.deleted"));
  } catch (error) {
    showError(message, error);
  }
}

async function copyStorageId(storageId: string) {
  try {
    await copyText(storageId);
    message.success(t("common.copied"));
  } catch {
    message.error(t("message.operationFailed"));
  }
}

function canManage(item: StorageConnection) {
  return item.created_by === authStore.user?.id || authStore.has(STORAGE_MANAGE_OTHERS);
}

function storageIdRule(): FormItemRule {
  return {
    validator: (_rule, value: string) => !value || STORAGE_ID_RE.test(value),
    message: t("validation.storageId", { label: t("field.storageId") }),
    trigger: ["input", "blur"]
  };
}
</script>
