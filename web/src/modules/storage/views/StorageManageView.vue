<template>
  <file-manager-view v-if="managingItem" :connection="managingItem" @close="closeFiles" />

  <section v-else class="work-card table-page-card">
    <div class="toolbar">
      <div class="storage-filter-row">
        <n-input
          v-model:value="filters.keyword"
          class="filter-keyword"
          :placeholder="t('storage.searchPlaceholder')"
          clearable
          @clear="searchConnections"
          @keyup.enter="searchConnections"
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
      @update:filters="handleTableFilters"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
      @update:sorter="handleSorter"
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
      </n-form>
      <template #action>
        <div class="form-actions modal-fixed-actions">
          <n-button :loading="testing" @click="testFormConnection">{{ t("common.test") }}</n-button>
          <n-button @click="showModal = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" :loading="saving" @click="saveConnection">{{ t("common.save") }}</n-button>
        </div>
      </template>
    </n-modal>
  </section>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from "vue";
import { Copy20Regular, Delete20Regular, Edit20Regular, FolderOpen20Regular, PlugConnected20Regular } from "@vicons/fluent";
import {
  NButton,
  NDataTable,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NInputNumber,
  NModal,
  NRadioButton,
  NRadioGroup,
  NSwitch,
  NTag,
  useDialog,
  useMessage
} from "naive-ui";
import type { DataTableColumns, DataTableFilterState, DataTableSortState, FormInst, FormItemRule, FormRules } from "naive-ui";

import PermissionButton from "../../../components/PermissionButton.vue";
import StatusTag from "../../../components/StatusTag.vue";
import { formatDateTime, t } from "../../../i18n";
import { authStore } from "../../../stores/auth";
import { copyText } from "../../../utils/clipboard";
import { messageText, showError } from "../../../utils/message";
import { singleFilterValue, sumColumnWidths, updateColumnWidth, withResizableColumns } from "../../../utils/table";
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
import FileManagerView from "../components/FileManagerView.vue";
import { STORAGE_CREATE, STORAGE_DELETE, STORAGE_MANAGE_OTHERS, STORAGE_UPDATE } from "../permissions";

type SharedFilter = "shared" | "private";
type ActiveFilter = "true" | "false";
type CreatorFilter = "all" | "me";

const STORAGE_ID_RE = /^[A-Za-z0-9][A-Za-z0-9_-]{2,63}$/;
const DEFAULT_PORTS: Record<StorageProtocol, number> = { ftp: 21, sftp: 22 };

const message = useMessage();
const dialog = useDialog();
const loading = ref(false);
const saving = ref(false);
const testing = ref(false);
const testingRowId = ref<number | null>(null);
const showModal = ref(false);
const formRef = ref<FormInst | null>(null);
const editingItem = ref<StorageConnection | null>(null);
const managingItem = ref<StorageConnection | null>(null);
const items = ref<StorageConnection[]>([]);
const filters = reactive<{
  keyword: string;
  protocol: StorageProtocol | null;
  shared: SharedFilter | null;
  is_active: ActiveFilter | null;
  created_by: CreatorFilter | null;
  sort_order: "ascend" | "descend";
}>({
  keyword: "",
  protocol: null,
  shared: null,
  is_active: null,
  created_by: null,
  sort_order: "descend"
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
const rules = computed<FormRules>(() => ({
  name: [requiredRule(t("storage.field.name")), maxLengthRule(t("storage.field.name"), 120)],
  storage_id: storageIdRule(),
  host: [requiredRule(t("field.host")), maxLengthRule(t("field.host"), 255)],
  port: numberRequiredRule(t("field.port")),
  username: [requiredRule(t("field.username")), maxLengthRule(t("field.username"), 120)],
  password: editingItem.value ? maxLengthRule(t("field.password"), 255) : requiredRule(t("field.password")),
  base_path: maxLengthRule(t("field.basePath"), 500)
}));
const protocolOptions = computed(() => [
  { label: "FTP", value: "ftp" },
  { label: "SFTP", value: "sftp" }
]);
const sharedOptions = computed(() => [
  { label: t("storage.shared"), value: "shared" },
  { label: t("storage.private"), value: "private" }
]);
const activeOptions = computed(() => [
  { label: t("common.enabled"), value: "true" },
  { label: t("common.disabled"), value: "false" }
]);
const creatorOptions = computed(() => [
  { label: t("storage.creatorAll"), value: "all" },
  { label: t("storage.creatorMe"), value: "me" }
]);
const columnWidths = reactive<Record<string, number>>({
  name: 140,
  storageId: 180,
  protocol: 96,
  address: 170,
  basePath: 120,
  shared: 96,
  isActive: 96,
  creator: 120,
  createdAt: 170,
  actions: 150
});
const columnWidthKeys: Record<string, string> = {
  name: "name",
  storage_id: "storageId",
  protocol: "protocol",
  address: "address",
  base_path: "basePath",
  is_shared: "shared",
  is_active: "isActive",
  created_by_username: "creator",
  created_at: "createdAt"
};
const tableScrollX = computed(() => sumColumnWidths(columnWidths));
const statusLabels = computed(() => ({ true: t("common.enabled"), false: t("common.disabled") }));
const columns = computed<DataTableColumns<StorageConnection>>(() =>
  withResizableColumns([
    {
      title: t("storage.field.name"),
      key: "name",
      width: columnWidths.name,
      ellipsis: { tooltip: true },
      render: (row) =>
        row.is_active
          ? h("span", { class: "storage-name-link", onClick: () => openFiles(row) }, row.name)
          : row.name
    },
    {
      title: t("field.storageId"),
      key: "storage_id",
      width: columnWidths.storageId,
      render: (row) =>
        h("span", { class: "copyable-cell" }, [
          h("code", null, row.storage_id),
          h(
            NButton,
            { size: "tiny", quaternary: true, circle: true, title: t("common.copy"), onClick: () => copyStorageId(row.storage_id) },
            { icon: () => h(NIcon, { component: Copy20Regular }) }
          )
        ])
    },
    {
      title: t("field.protocol"),
      key: "protocol",
      width: columnWidths.protocol,
      filter: (value, row) => row.protocol === value,
      filterMultiple: false,
      filterOptionValue: filters.protocol,
      filterOptions: protocolOptions.value,
      render: (row) => h(NTag, { size: "small", bordered: false }, () => row.protocol.toUpperCase())
    },
    {
      title: t("storage.field.address"),
      key: "address",
      width: columnWidths.address,
      ellipsis: { tooltip: true },
      render: (row) => `${row.host}:${row.port}`
    },
    { title: t("field.basePath"), key: "base_path", width: columnWidths.basePath, ellipsis: { tooltip: true } },
    {
      title: t("storage.field.shared"),
      key: "is_shared",
      width: columnWidths.shared,
      filter: (value, row) => row.is_shared === (value === "shared"),
      filterMultiple: false,
      filterOptionValue: filters.shared,
      filterOptions: sharedOptions.value,
      render: (row) =>
        h(NTag, { size: "small", bordered: false, type: row.is_shared ? "info" : "default" }, () =>
          row.is_shared ? t("storage.shared") : t("storage.private")
        )
    },
    {
      title: t("field.status"),
      key: "is_active",
      width: columnWidths.isActive,
      filter: (value, row) => row.is_active === (value === "true"),
      filterMultiple: false,
      filterOptionValue: filters.is_active,
      filterOptions: activeOptions.value,
      render: (row) => h(StatusTag, { status: row.is_active, labels: statusLabels.value })
    },
    {
      title: t("field.creator"),
      key: "created_by_username",
      width: columnWidths.creator,
      filter: () => true,
      filterMultiple: false,
      filterOptionValue: filters.created_by,
      filterOptions: creatorOptions.value,
      render: (row) => row.created_by_username || t("common.none")
    },
    {
      title: t("field.createdAt"),
      key: "created_at",
      width: columnWidths.createdAt,
      sorter: true,
      sortOrder: filters.sort_order,
      render: (row) => formatDateTime(row.created_at)
    },
    {
      title: t("common.actions"),
      key: "actions",
      width: columnWidths.actions,
      fixed: "right",
      render: (row) =>
        h(
          "div",
          { class: "table-action-group" },
          [
            h(
              NButton,
              {
                size: "small",
                quaternary: true,
                circle: true,
                type: "primary",
                title: t("storage.manage"),
                disabled: !row.is_active,
                onClick: () => openFiles(row)
              },
              { icon: () => h(NIcon, { component: FolderOpen20Regular }) }
            ),
            canManage(row) && authStore.has(STORAGE_UPDATE)
              ? h(
                  NButton,
                  {
                    size: "small",
                    quaternary: true,
                    circle: true,
                    title: t("common.test"),
                    loading: testingRowId.value === row.id,
                    onClick: () => void testRowConnection(row)
                  },
                  { icon: () => h(NIcon, { component: PlugConnected20Regular }) }
                )
              : null,
            canManage(row) && authStore.has(STORAGE_UPDATE)
              ? h(
                  NButton,
                  { size: "small", quaternary: true, circle: true, title: t("common.edit"), onClick: () => openEdit(row) },
                  { icon: () => h(NIcon, { component: Edit20Regular }) }
                )
              : null,
            canManage(row) && authStore.has(STORAGE_DELETE)
              ? h(
                  NButton,
                  { size: "small", quaternary: true, circle: true, type: "error", title: t("common.delete"), onClick: () => confirmDelete(row) },
                  { icon: () => h(NIcon, { component: Delete20Regular }) }
                )
              : null
          ].filter(Boolean)
        )
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
      shared: filters.shared || "",
      is_active: filters.is_active ? filters.is_active === "true" : null,
      created_by: filters.created_by || "",
      sort_order: filters.sort_order,
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

function handleTableFilters(filterState: DataTableFilterState) {
  const protocol = singleFilterValue(filterState, "protocol");
  const shared = singleFilterValue(filterState, "is_shared");
  const active = singleFilterValue(filterState, "is_active");
  const creator = singleFilterValue(filterState, "created_by_username");
  filters.protocol = protocol === "ftp" || protocol === "sftp" ? protocol : null;
  filters.shared = shared === "shared" || shared === "private" ? shared : null;
  filters.is_active = active === "true" || active === "false" ? active : null;
  filters.created_by = creator === "all" || creator === "me" ? creator : null;
  pagination.page = 1;
  void loadConnections();
}

function handleSorter(sortState: DataTableSortState | DataTableSortState[] | null) {
  const state = Array.isArray(sortState) ? sortState[0] : sortState;
  filters.sort_order = state?.order === "ascend" ? "ascend" : "descend";
  pagination.page = 1;
  void loadConnections();
}

function handleColumnResize(_: number, limitedWidth: number, column: { key?: string | number }) {
  updateColumnWidth(columnWidths, column.key, columnWidthKeys, limitedWidth);
}

function openCreate() {
  editingItem.value = null;
  Object.assign(form, {
    name: "", storage_id: "", protocol: "ftp", host: "", port: 21,
    username: "", password: "", base_path: "/", is_shared: false, is_active: true
  });
  showModal.value = true;
}

function openEdit(item: StorageConnection) {
  editingItem.value = item;
  Object.assign(form, {
    name: item.name, storage_id: item.storage_id, protocol: item.protocol,
    host: item.host, port: item.port, username: item.username, password: "",
    base_path: item.base_path, is_shared: item.is_shared, is_active: item.is_active
  });
  showModal.value = true;
}

function openFiles(item: StorageConnection) {
  managingItem.value = item;
}

function closeFiles() {
  managingItem.value = null;
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

async function testFormConnection() {
  if (!(await validateForm(formRef.value))) return;
  testing.value = true;
  try {
    const result = await testStorage({
      id: editingItem.value?.id ?? null,
      protocol: form.protocol, host: form.host, port: form.port,
      username: form.username, password: form.password, base_path: form.base_path
    });
    message.success(messageText(result, "storage.connectionOk"));
  } catch (error) {
    showError(message, error);
  } finally {
    testing.value = false;
  }
}

async function testRowConnection(item: StorageConnection) {
  testingRowId.value = item.id;
  try {
    const result = await testStorage({
      id: item.id, protocol: item.protocol, host: item.host, port: item.port,
      username: item.username, password: "", base_path: item.base_path
    });
    message.success(messageText(result, "storage.connectionOk"));
  } catch (error) {
    showError(message, error);
  } finally {
    testingRowId.value = null;
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
