<template>
  <sql-workbench-view v-if="workingItem" :connection="workingItem" @close="closeWorkbench" @jobs="openJobs" />

  <data-jobs-view v-else-if="showJobs" embedded :connection-id="jobScope.connectionId" :connection-name="jobScope.connectionName" @close="closeJobs" />

  <section v-else class="work-card table-page-card">
    <div class="toolbar">
      <div class="storage-filter-row">
        <n-input
          v-model:value="filters.keyword"
          class="filter-keyword"
          :placeholder="t('database.searchPlaceholder')"
          clearable
          @clear="searchConnections"
          @keyup.enter="searchConnections"
        />
        <n-button @click="searchConnections">{{ t("common.search") }}</n-button>
      </div>
      <div class="toolbar-actions">
        <n-badge :value="pendingDownloadCount" :max="99" type="success" :show="pendingDownloadCount > 0">
          <n-button @click="() => openJobs()">{{ t("database.jobs.view") }}</n-button>
        </n-badge>
        <permission-button :permission="DATABASE_CREATE" type="primary" @click="openCreate">{{ t("database.add") }}</permission-button>
      </div>
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

    <n-modal v-model:show="showModal" preset="card" class="modal-card" :title="editingItem ? t('database.edit') : t('database.add')">
      <n-form ref="formRef" class="form-stack inline-form" :model="form" :rules="rules" label-placement="left" label-width="auto">
        <n-form-item :label="t('field.name')" path="name">
          <n-input v-model:value="form.name" />
        </n-form-item>
        <n-form-item :label="t('field.connId')" path="conn_id">
          <n-input v-model:value="form.conn_id" :disabled="editingItem !== null" :placeholder="editingItem ? '' : t('database.idPlaceholder')" />
        </n-form-item>
        <n-form-item :label="t('field.type')" path="db_type">
          <n-radio-group v-model:value="form.db_type" @update:value="handleTypeChange">
            <n-radio-button value="mysql" label="MySQL" />
            <n-radio-button value="mariadb" label="MariaDB" />
          </n-radio-group>
        </n-form-item>
        <n-form-item :label="t('field.host')" path="host">
          <n-input v-model:value="form.host" />
        </n-form-item>
        <n-form-item :label="t('field.port')" path="port">
          <n-input-number v-model:value="form.port" :min="1" :max="65535" :show-button="false" />
        </n-form-item>
        <n-form-item :label="t('field.username')" path="username">
          <n-input v-model:value="form.username" />
        </n-form-item>
        <n-form-item :label="t('field.password')" path="password">
          <n-input v-model:value="form.password" type="password" show-password-on="click" :placeholder="editingItem ? t('database.passwordKeep') : ''" />
        </n-form-item>
        <n-form-item :label="t('field.database')" path="default_database">
          <n-input v-model:value="form.default_database" :placeholder="t('database.defaultDatabaseHint')" />
        </n-form-item>
        <n-form-item :label="t('database.shared')" path="is_shared">
          <n-switch v-model:value="form.is_shared">
            <template #checked>{{ t("database.shared") }}</template>
            <template #unchecked>{{ t("database.private") }}</template>
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
import { Copy20Regular, Delete20Regular, Edit20Regular, PlugConnected20Regular, Table20Regular } from "@vicons/fluent";
import {
  NButton,
  NBadge,
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
  createDatabaseConnection,
  deleteDatabaseConnection,
  getDataJobDownloadCount,
  listDatabaseConnections,
  testDatabaseConnection,
  updateDatabaseConnection,
  type DatabaseConnection,
  type DatabaseConnectionPayload,
  type DatabaseType
} from "../api";
import DataJobsView from "./DataJobsView.vue";
import SqlWorkbenchView from "../components/SqlWorkbenchView.vue";
import { DATABASE_CREATE, DATABASE_MANAGE_OTHERS } from "../permissions";

type SharedFilter = "shared" | "private";
type ActiveFilter = "true" | "false";
type CreatorFilter = "all" | "me";

const CONN_ID_RE = /^[A-Za-z0-9][A-Za-z0-9_-]{2,63}$/;
const DEFAULT_PORTS: Record<DatabaseType, number> = { mysql: 3306, mariadb: 3306 };

const message = useMessage();
const dialog = useDialog();
const loading = ref(false);
const saving = ref(false);
const testing = ref(false);
const testingRowId = ref<number | null>(null);
const showModal = ref(false);
const formRef = ref<FormInst | null>(null);
const editingItem = ref<DatabaseConnection | null>(null);
const workingItem = ref<DatabaseConnection | null>(null);
const showJobs = ref(false);
const jobScope = reactive<{ connectionId: number | null; connectionName: string }>({ connectionId: null, connectionName: "" });
const items = ref<DatabaseConnection[]>([]);
const pendingDownloadCount = ref(0);
const filters = reactive<{
  keyword: string;
  db_type: DatabaseType | null;
  shared: SharedFilter | null;
  is_active: ActiveFilter | null;
  created_by: CreatorFilter | null;
  sort_order: "ascend" | "descend";
}>({
  keyword: "",
  db_type: null,
  shared: null,
  is_active: null,
  created_by: null,
  sort_order: "descend"
});
const form = reactive<DatabaseConnectionPayload>({
  name: "",
  conn_id: "",
  db_type: "mysql",
  host: "",
  port: 3306,
  username: "",
  password: "",
  default_database: "",
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
const connectionColumnWidths = reactive<Record<string, number>>({
  name: 160,
  connId: 180,
  dbType: 90,
  host: 190,
  database: 150,
  shared: 100,
  status: 100,
  creator: 120,
  createdAt: 180,
  actions: 190
});
const connectionColumnWidthKeys: Record<string, string> = {
  name: "name",
  conn_id: "connId",
  db_type: "dbType",
  host: "host",
  default_database: "database",
  shared: "shared",
  is_active: "status",
  created_by: "creator",
  created_at: "createdAt"
};
const tableScrollX = computed(() => sumColumnWidths(connectionColumnWidths));
const rules = computed<FormRules>(() => ({
  name: [requiredRule(t("field.name")), maxLengthRule(t("field.name"), 120)],
  conn_id: connIdRule(),
  host: [requiredRule(t("field.host")), maxLengthRule(t("field.host"), 255)],
  port: numberRequiredRule(t("field.port")),
  username: [requiredRule(t("field.username")), maxLengthRule(t("field.username"), 120)],
  password: editingItem.value ? maxLengthRule(t("field.password"), 255) : requiredRule(t("field.password")),
  default_database: maxLengthRule(t("field.database"), 128)
}));
const dbTypeOptions = [
  { label: "MySQL", value: "mysql" },
  { label: "MariaDB", value: "mariadb" }
];
const sharedOptions = computed(() => [
  { label: t("database.shared"), value: "shared" },
  { label: t("database.private"), value: "private" }
]);
const activeOptions = computed(() => [
  { label: t("common.enabled"), value: "true" },
  { label: t("common.disabled"), value: "false" }
]);
const creatorOptions = computed(() => [
  { label: t("database.creatorAll"), value: "all" },
  { label: t("database.creatorMe"), value: "me" }
]);
const columns = computed<DataTableColumns<DatabaseConnection>>(() =>
  withResizableColumns([
  {
    title: t("field.name"),
    key: "name",
    width: connectionColumnWidths.name,
    minWidth: 120,
    resizable: true,
    ellipsis: { tooltip: true },
    render: (row) => h("span", { class: "storage-name-link", title: row.name, onClick: () => openWorkbench(row) }, row.name)
  },
  {
    title: t("field.connId"),
    key: "conn_id",
    width: connectionColumnWidths.connId,
    minWidth: 140,
    resizable: true,
    render: (row) =>
      h("span", { class: "copyable-cell" }, [
        h("span", null, row.conn_id),
        h(NButton, { quaternary: true, size: "tiny", onClick: () => void copyText(row.conn_id) }, () => h(NIcon, { component: Copy20Regular }))
      ])
  },
  {
    title: t("field.type"),
    key: "db_type",
    width: connectionColumnWidths.dbType,
    minWidth: 80,
    resizable: true,
    filterOptions: dbTypeOptions,
    filterOptionValue: filters.db_type,
    filterMultiple: false,
    filter: true,
    render: (row) => row.db_type.toUpperCase()
  },
  { title: t("field.host"), key: "host", width: connectionColumnWidths.host, minWidth: 140, resizable: true, ellipsis: { tooltip: true }, render: (row) => `${row.host}:${row.port}` },
  {
    title: t("field.database"),
    key: "default_database",
    width: connectionColumnWidths.database,
    minWidth: 120,
    resizable: true,
    ellipsis: { tooltip: true },
    render: (row) => row.default_database || t("database.allSchemas")
  },
  {
    title: t("database.shared"),
    key: "shared",
    width: connectionColumnWidths.shared,
    minWidth: 90,
    resizable: true,
    filterOptions: sharedOptions.value,
    filterOptionValue: filters.shared,
    filterMultiple: false,
    filter: true,
    render: (row) => h(NTag, { size: "small", type: row.is_shared ? "success" : "default" }, () => (row.is_shared ? t("database.shared") : t("database.private")))
  },
  {
    title: t("field.status"),
    key: "is_active",
    width: connectionColumnWidths.status,
    minWidth: 90,
    resizable: true,
    filterOptions: activeOptions.value,
    filterOptionValue: filters.is_active,
    filterMultiple: false,
    filter: true,
    render: (row) => h(StatusTag, { status: row.is_active })
  },
  {
    title: t("field.creator"),
    key: "created_by",
    width: connectionColumnWidths.creator,
    minWidth: 100,
    resizable: true,
    filterOptions: creatorOptions.value,
    filterOptionValue: filters.created_by,
    filterMultiple: false,
    filter: true,
    render: (row) => row.created_by_username || "-"
  },
  {
    title: t("field.createdAt"),
    key: "created_at",
    width: connectionColumnWidths.createdAt,
    minWidth: 150,
    resizable: true,
    sorter: true,
    sortOrder: filters.sort_order,
    render: (row) => formatDateTime(row.created_at)
  },
  {
    title: t("common.actions"),
    key: "actions",
    width: connectionColumnWidths.actions,
    minWidth: 170,
    fixed: "right",
    align: "center",
    render: (row) =>
      h("div", { class: "table-action-group" }, [
        h(
          NButton,
          { size: "small", quaternary: true, circle: true, type: "primary", title: t("database.manage"), onClick: () => openWorkbench(row) },
          { icon: () => h(NIcon, { component: Table20Regular }) }
        ),
        h(
          NButton,
          { size: "small", quaternary: true, circle: true, title: t("common.test"), loading: testingRowId.value === row.id, onClick: () => testExisting(row) },
          { icon: () => h(NIcon, { component: PlugConnected20Regular }) }
        ),
        canManage(row)
          ? h(
              NButton,
              { size: "small", quaternary: true, circle: true, title: t("common.edit"), onClick: () => openEdit(row) },
              { icon: () => h(NIcon, { component: Edit20Regular }) }
            )
          : null,
        canManage(row)
          ? h(
              NButton,
              { size: "small", quaternary: true, circle: true, type: "error", title: t("common.delete"), onClick: () => confirmDelete(row) },
              { icon: () => h(NIcon, { component: Delete20Regular }) }
            )
          : null
      ])
  }
  ])
);

onMounted(() => {
  void loadConnections();
  void loadDownloadCount();
});

async function loadConnections() {
  loading.value = true;
  try {
    const result = await listDatabaseConnections({
      keyword: filters.keyword,
      db_type: filters.db_type || "",
      shared: filters.shared || "",
      is_active: filters.is_active === null ? null : filters.is_active === "true",
      created_by: filters.created_by === "me" ? "me" : "",
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

async function loadDownloadCount() {
  try {
    pendingDownloadCount.value = (await getDataJobDownloadCount()).count;
  } catch {
    pendingDownloadCount.value = 0;
  }
}

function searchConnections() {
  pagination.page = 1;
  void loadConnections();
}

function handleTableFilters(next: DataTableFilterState) {
  filters.db_type = singleFilterValue(next, "db_type") as DatabaseType | null;
  filters.shared = singleFilterValue(next, "shared") as SharedFilter | null;
  filters.is_active = singleFilterValue(next, "is_active") as ActiveFilter | null;
  filters.created_by = singleFilterValue(next, "created_by") as CreatorFilter | null;
  pagination.page = 1;
  void loadConnections();
}

function handleSorter(sorter: DataTableSortState | DataTableSortState[] | null) {
  const state = Array.isArray(sorter) ? sorter[0] : sorter;
  filters.sort_order = state?.order === "ascend" ? "ascend" : "descend";
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
  updateColumnWidth(connectionColumnWidths, column.key, connectionColumnWidthKeys, limitedWidth);
}

function openCreate() {
  editingItem.value = null;
  Object.assign(form, { name: "", conn_id: "", db_type: "mysql", host: "", port: 3306, username: "", password: "", default_database: "", is_shared: false, is_active: true });
  showModal.value = true;
}

function openEdit(row: DatabaseConnection) {
  editingItem.value = row;
  Object.assign(form, { ...row, password: "" });
  showModal.value = true;
}

async function saveConnection() {
  if (!(await validateForm(formRef.value))) return;
  saving.value = true;
  try {
    if (editingItem.value) {
      await updateDatabaseConnection(editingItem.value.id, form);
    } else {
      await createDatabaseConnection(form);
    }
    showModal.value = false;
    await loadConnections();
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
    const response = await testDatabaseConnection({ id: editingItem.value?.id ?? null, ...form });
    message.success(messageText(response));
  } catch (error) {
    showError(message, error);
  } finally {
    testing.value = false;
  }
}

async function testExisting(row: DatabaseConnection) {
  testingRowId.value = row.id;
  try {
    const response = await testDatabaseConnection({ id: row.id, db_type: row.db_type, host: row.host, port: row.port, username: row.username, password: "", default_database: row.default_database });
    message.success(messageText(response));
  } catch (error) {
    showError(message, error);
  } finally {
    testingRowId.value = null;
  }
}

function confirmDelete(row: DatabaseConnection) {
  dialog.warning({
    title: t("common.confirm"),
    content: t("database.deleteConfirm", { name: row.name }),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: async () => {
      await deleteDatabaseConnection(row.id);
      await loadConnections();
    }
  });
}

function openWorkbench(row: DatabaseConnection) {
  showJobs.value = false;
  workingItem.value = row;
}

function closeWorkbench() {
  workingItem.value = null;
  void loadDownloadCount();
}

function openJobs(scope?: { connectionId?: number | null; connectionName?: string }) {
  workingItem.value = null;
  jobScope.connectionId = scope?.connectionId ?? null;
  jobScope.connectionName = scope?.connectionName ?? "";
  showJobs.value = true;
  void loadDownloadCount();
}

function closeJobs() {
  showJobs.value = false;
  jobScope.connectionId = null;
  jobScope.connectionName = "";
  void loadDownloadCount();
}

function handleTypeChange(value: DatabaseType) {
  form.port = DEFAULT_PORTS[value];
}

function canManage(row: DatabaseConnection) {
  return authStore.has(DATABASE_MANAGE_OTHERS) || authStore.user?.id === row.created_by;
}

function connIdRule(): FormItemRule {
  return {
    trigger: ["input", "blur"],
    validator: (_rule, value: string) => {
      if (!value) return true;
      if (!CONN_ID_RE.test(value)) {
        return new Error(t("validation.connId"));
      }
      return true;
    }
  };
}
</script>
