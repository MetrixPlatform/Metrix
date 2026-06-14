<template>
  <section class="work-card database-workbench">
    <div class="toolbar database-workbench-toolbar">
      <n-button size="small" quaternary :title="t('common.back')" :aria-label="t('common.back')" @click="emit('close')">
        <template #icon><n-icon :component="ArrowLeft20Regular" /></template>
      </n-button>
      <span class="database-workbench-title">{{ connection.name }}</span>
      <n-tag size="small" :bordered="false">{{ connection.db_type.toUpperCase() }}</n-tag>
      <span class="muted-text">{{ connection.host }}:{{ connection.port }}</span>
      <div class="file-manager-spacer" />
      <n-button @click="goJobs">{{ t("database.jobs.view") }}</n-button>
    </div>

    <div class="database-workbench-body">
      <aside class="database-sidebar">
        <div class="database-sidebar-actions">
          <n-button
            class="database-icon-button"
            quaternary
            circle
            size="small"
            :loading="loadingMeta"
            :title="t('common.refresh')"
            :aria-label="t('common.refresh')"
            @click="refreshMetadata"
          >
            <template #icon><n-icon :component="ArrowClockwise20Regular" /></template>
          </n-button>
          <n-dropdown trigger="click" :options="createOptions" @select="handleCreateSelect">
            <permission-button class="database-action-button" :permission="DATABASE_OPERATE" size="small">
              <template #icon><n-icon :component="Add20Regular" /></template>
              {{ t("database.create") }}
            </permission-button>
          </n-dropdown>
          <n-dropdown trigger="click" :options="dropOptions" @select="handleDropSelect">
            <permission-button class="database-action-button" :permission="DATABASE_OPERATE" size="small">
              <template #icon><n-icon :component="Delete20Regular" /></template>
              {{ t("common.delete") }}
            </permission-button>
          </n-dropdown>
        </div>
        <n-tree
          v-if="treeData.length"
          block-line
          class="database-tree"
          :data="treeData"
          :expanded-keys="expandedKeys"
          :selected-keys="selectedKeys"
          :on-load="handleTreeLoad"
          :render-prefix="renderTreePrefix"
          @update:expanded-keys="handleExpand"
          @update:selected-keys="handleTreeSelect"
        />
        <n-empty v-else class="database-tree-empty" :description="t('database.treeEmpty')" />
      </aside>

      <main class="database-main">
        <n-tabs v-model:value="activeTab" type="line" animated>
          <n-tab-pane class="database-tab-pane" name="data" :tab="t('database.tabs.data')" display-directive="show">
            <div class="database-sub-toolbar">
              <n-input v-model:value="tableFilter" class="filter-keyword" clearable :placeholder="t('database.table.search')" @keyup.enter="loadTableData" />
              <n-button :disabled="!selectedTable" @click="loadTableData">{{ t("common.search") }}</n-button>
              <permission-button :permission="DATABASE_OPERATE" :disabled="!selectedTable" @click="openAddRow">{{ t("database.row.add") }}</permission-button>
              <permission-button :permission="DATABASE_OPERATE" :disabled="!selectedTable" @click="showImport = true">{{ t("database.import.title") }}</permission-button>
              <n-dropdown :options="exportOptions" :disabled="!selectedTable" @select="exportTable">
                <n-button>{{ t("database.export.title") }}</n-button>
              </n-dropdown>
            </div>
            <n-data-table
              class="page-data-table database-result-table"
              flex-height
              remote
              size="small"
              :columns="dataColumns"
              :data="tableRows"
              :loading="loadingData"
              :pagination="dataPagination"
              :scroll-x="Math.max(900, dataColumns.length * 160)"
              @update:page="handleDataPage"
              @update:page-size="handleDataPageSize"
            />
          </n-tab-pane>

          <n-tab-pane class="database-tab-pane" name="sql" :tab="t('database.tabs.sql')" display-directive="show">
            <div class="database-sub-toolbar">
              <n-tag class="database-active-schema" size="small" :bordered="false" type="primary">
                <template #icon><n-icon :component="Database20Regular" /></template>
                {{ selectedDatabase || t("database.allSchemas") }}
              </n-tag>
              <n-button type="primary" :loading="executing" @click="executeSql">{{ t("database.sql.execute") }}</n-button>
              <n-dropdown :options="exportOptions" @select="exportQuery">
                <n-button>{{ t("database.export.result") }}</n-button>
              </n-dropdown>
              <permission-button :permission="SQL_SCRIPT_CREATE" @click="openSaveScript">{{ t("database.script.save") }}</permission-button>
            </div>
            <monaco-editor v-model="sql" class="database-sql-editor" :suggestions="suggestions" />
            <n-data-table
              class="page-data-table database-query-table"
              flex-height
              size="small"
              :columns="queryColumns"
              :data="queryRows"
              :loading="executing"
              :scroll-x="Math.max(900, queryColumns.length * 160)"
            />
          </n-tab-pane>

          <n-tab-pane class="database-tab-pane" name="scripts" :tab="t('database.tabs.scripts')" display-directive="show">
            <div class="database-sub-toolbar">
              <n-input v-model:value="scriptKeyword" class="filter-keyword" clearable :placeholder="t('database.script.search')" @keyup.enter="loadScripts" />
              <n-button @click="loadScripts">{{ t("common.search") }}</n-button>
            </div>
            <n-data-table class="page-data-table database-script-table" flex-height size="small" :columns="scriptColumns" :data="scripts" :loading="loadingScripts" />
          </n-tab-pane>
        </n-tabs>
      </main>
    </div>

    <n-modal v-model:show="rowModal.show" preset="card" class="modal-card" :title="rowModal.mode === 'add' ? t('database.row.add') : t('database.row.edit')">
      <n-input v-model:value="rowModal.json" type="textarea" :autosize="{ minRows: 8, maxRows: 16 }" />
      <template #action>
        <div class="form-actions modal-fixed-actions">
          <n-button @click="rowModal.show = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" :loading="savingRow" @click="saveRow">{{ t("common.save") }}</n-button>
        </div>
      </template>
    </n-modal>

    <n-modal v-model:show="scriptModal.show" preset="card" class="modal-card" :title="t('database.script.save')">
      <n-form class="form-stack inline-form" label-placement="left" label-width="auto">
        <n-form-item :label="t('field.name')">
          <n-input v-model:value="scriptModal.name" />
        </n-form-item>
        <n-form-item :label="t('field.description')">
          <n-input v-model:value="scriptModal.description" />
        </n-form-item>
        <n-form-item :label="t('database.shared')">
          <n-switch v-model:value="scriptModal.is_shared" />
        </n-form-item>
      </n-form>
      <template #action>
        <div class="form-actions modal-fixed-actions">
          <n-button @click="scriptModal.show = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" :loading="savingScript" @click="saveScript">{{ t("common.save") }}</n-button>
        </div>
      </template>
    </n-modal>

    <n-modal v-model:show="objectModal.show" preset="card" class="modal-card" :title="objectModalTitle">
      <n-form class="form-stack inline-form" label-placement="left" label-width="auto" @keyup.enter="saveObject">
        <n-form-item :label="objectModal.kind === 'schema' ? t('database.schema.name') : t('database.table.name')">
          <n-input v-model:value="objectModal.name" />
        </n-form-item>
      </n-form>
      <template #action>
        <div class="form-actions modal-fixed-actions">
          <n-button @click="objectModal.show = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" :loading="objectModal.saving" @click="saveObject">{{ t("common.save") }}</n-button>
        </div>
      </template>
    </n-modal>

    <import-wizard
      v-model:show="showImport"
      :conn-id="connection.conn_id"
      :database="selectedDatabase || ''"
      :table="selectedTable || ''"
      @submitted="handleJobSubmitted"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from "vue";
import { Add20Regular, ArrowClockwise20Regular, ArrowLeft20Regular, Database20Regular, Delete20Regular, Table20Regular } from "@vicons/fluent";
import {
  NButton,
  NDataTable,
  NDropdown,
  NEmpty,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NModal,
  NSwitch,
  NTabPane,
  NTabs,
  NTag,
  NTree,
  useDialog,
  useMessage
} from "naive-ui";
import type { DataTableColumns, DropdownOption, TreeOption } from "naive-ui";

import PermissionButton from "../../../components/PermissionButton.vue";
import { formatDateTime, t } from "../../../i18n";
import { showError } from "../../../utils/message";
import {
  createRow,
  createSchema,
  createSqlScript,
  createTable,
  deleteRow,
  dropSchema,
  dropTable,
  getTableData,
  listSchemas,
  listSqlScripts,
  listTables,
  queryDatabase,
  runSqlScript,
  submitExport,
  updateRow,
  type ColumnItem,
  type DatabaseConnection,
  type DataFormat,
  type QueryResult,
  type SqlScript,
  type TableItem
} from "../api";
import { DATABASE_OPERATE, SQL_SCRIPT_CREATE } from "../permissions";
import ImportWizard from "./ImportWizard.vue";
import MonacoEditor from "./MonacoEditor.vue";

const props = defineProps<{ connection: DatabaseConnection }>();
const emit = defineEmits<{ (event: "close"): void; (event: "jobs"): void }>();

const message = useMessage();
const dialog = useDialog();
const activeTab = ref<"data" | "sql" | "scripts">("data");
const schemas = ref<{ name: string }[]>([]);
const tables = ref<TableItem[]>([]);
const treeData = ref<TreeOption[]>([]);
const expandedKeys = ref<string[]>([]);
const selectedKeys = ref<string[]>([]);
const loadingMeta = ref(false);
const selectedDatabase = ref(props.connection.default_database || "");
const selectedTable = ref("");
const tableColumns = ref<ColumnItem[]>([]);
const tableRows = ref<Record<string, unknown>[]>([]);
const primaryKeys = ref<string[]>([]);
const tableFilter = ref("");
const loadingData = ref(false);
const executing = ref(false);
const sql = ref("SELECT 1;");
const queryResult = ref<QueryResult | null>(null);
const scripts = ref<SqlScript[]>([]);
const scriptKeyword = ref("");
const loadingScripts = ref(false);
const savingRow = ref(false);
const savingScript = ref(false);
const showImport = ref(false);
const rowModal = reactive({
  show: false,
  mode: "add" as "add" | "edit",
  json: "{}",
  original: null as Record<string, unknown> | null
});
const scriptModal = reactive({
  show: false,
  name: "",
  description: "",
  is_shared: false
});
const objectModal = reactive({
  show: false,
  kind: "schema" as "schema" | "table",
  name: "",
  saving: false
});
const dataPagination = reactive({
  page: 1,
  pageSize: 100,
  itemCount: 0,
  pageSizes: [50, 100, 200, 500],
  showSizePicker: true,
  prefix: ({ itemCount }: { itemCount: number | undefined }) => t("common.total", { count: itemCount ?? 0 })
});
const exportOptions = [
  { label: "CSV", key: "csv" },
  { label: "XLSX", key: "xlsx" },
  { label: "SQLite", key: "sqlite" },
  { label: "SQL", key: "sql" }
];
const createOptions = computed<DropdownOption[]>(() => [
  { label: t("database.schema.create"), key: "schema" },
  { label: t("database.table.create"), key: "table", disabled: !selectedDatabase.value }
]);
const dropOptions = computed<DropdownOption[]>(() => [
  { label: t("database.schema.drop"), key: "schema", disabled: !selectedDatabase.value },
  { label: t("database.table.drop"), key: "table", disabled: !selectedTable.value }
]);
const objectModalTitle = computed(() => (objectModal.kind === "schema" ? t("database.schema.create") : t("database.table.create")));

function renderTreePrefix({ option }: { option: TreeOption }) {
  const icon = option.kind === "schema" ? Database20Regular : Table20Regular;
  return h(NIcon, { component: icon });
}
const suggestions = computed(() => [
  ...schemas.value.map((item) => item.name),
  ...tables.value.map((item) => item.name),
  ...tableColumns.value.map((item) => item.name)
]);
const dataColumns = computed<DataTableColumns<Record<string, unknown>>>(() => [
  ...tableColumns.value.map((column) => ({
    title: column.name,
    key: column.name,
    minWidth: 140,
    ellipsis: { tooltip: true },
    render: (row: Record<string, unknown>) => formatCell(row[column.name])
  })),
  {
    title: t("common.actions"),
    key: "actions",
    fixed: "right",
    width: 150,
    render: (row: Record<string, unknown>) =>
      h("div", { class: "table-actions" }, [
        h(NButton, { size: "tiny", quaternary: true, onClick: () => openEditRow(row) }, () => t("common.edit")),
        h(NButton, { size: "tiny", quaternary: true, type: "error", onClick: () => confirmDeleteRow(row) }, () => t("common.delete"))
      ])
  }
]);
const queryColumns = computed<DataTableColumns<Record<string, unknown>>>(() => {
  const columns = queryResult.value?.columns || [];
  if (!columns.length && queryResult.value?.statement_type === "write") {
    return [{ title: t("database.sql.affectedRows"), key: "affected_rows", render: () => queryResult.value?.affected_rows ?? 0 }];
  }
  return columns.map((column) => ({ title: column, key: column, minWidth: 140, ellipsis: { tooltip: true }, render: (row) => formatCell(row[column]) }));
});
const queryRows = computed(() => queryResult.value?.rows || []);
const scriptColumns = computed<DataTableColumns<SqlScript>>(() => [
  { title: t("field.name"), key: "name", ellipsis: { tooltip: true } },
  { title: t("field.description"), key: "description", ellipsis: { tooltip: true } },
  { title: t("database.connection"), key: "connection_name", render: (row) => row.connection_name || "-" },
  { title: t("field.updatedAt"), key: "updated_at", width: 170, render: (row) => formatDateTime(row.updated_at) },
  {
    title: t("common.actions"),
    key: "actions",
    width: 180,
    render: (row) =>
      h("div", { class: "table-actions" }, [
        h(NButton, { size: "tiny", quaternary: true, onClick: () => loadScript(row) }, () => t("database.script.load")),
        h(NButton, { size: "tiny", quaternary: true, type: "primary", onClick: () => executeScript(row) }, () => t("database.script.run"))
      ])
  }
]);

onMounted(async () => {
  await refreshMetadata();
  await loadScripts();
});

function schemaKey(name: string) {
  return `schema:${name}`;
}

function tableKey(database: string, table: string) {
  return `table:${database}:${table}`;
}

async function refreshMetadata() {
  loadingMeta.value = true;
  try {
    schemas.value = await listSchemas(props.connection.conn_id);
    const names = schemas.value.map((item) => item.name);
    const initial = selectedDatabase.value && names.includes(selectedDatabase.value) ? selectedDatabase.value : names[0] || "";
    treeData.value = schemas.value.map((schema) => ({
      key: schemaKey(schema.name),
      label: schema.name,
      kind: "schema",
      database: schema.name,
      isLeaf: false
    }));
    expandedKeys.value = [];
    selectedKeys.value = [];
    selectedDatabase.value = initial;
    if (initial) {
      await openSchema(initial);
    } else {
      resetTableView();
    }
  } catch (error) {
    showError(message, error);
  } finally {
    loadingMeta.value = false;
  }
}

async function loadSchemaTables(database: string): Promise<TreeOption[]> {
  const items = await listTables(props.connection.conn_id, database);
  return items.map((item) => ({
    key: tableKey(database, item.name),
    label: item.name,
    kind: "table",
    database,
    table: item.name,
    isLeaf: true
  }));
}

async function handleTreeLoad(node: TreeOption) {
  const children = await loadSchemaTables(node.database as string);
  node.children = children;
  if (node.database === selectedDatabase.value) {
    tables.value = children.map((child) => ({ name: child.table as string }));
  }
}

async function openSchema(database: string) {
  const node = treeData.value.find((item) => item.database === database);
  if (!node) return;
  node.children = await loadSchemaTables(database);
  tables.value = node.children.map((child) => ({ name: child.table as string }));
  expandedKeys.value = [schemaKey(database)];
  const match = node.children.find((child) => child.table === selectedTable.value) || node.children[0];
  if (match) {
    selectedKeys.value = [String(match.key)];
    await selectTable(match.table as string);
  } else {
    selectedKeys.value = [schemaKey(database)];
    resetTableView();
  }
}

function handleExpand(keys: Array<string | number>) {
  expandedKeys.value = keys.map(String);
}

async function handleTreeSelect(keys: Array<string | number>, options: Array<TreeOption | null>) {
  const node = options[0];
  if (!node) return;
  selectedKeys.value = keys.map(String);
  if (node.kind === "table") {
    selectedDatabase.value = node.database as string;
    tables.value = (treeData.value.find((item) => item.database === node.database)?.children || []).map((child) => ({ name: child.table as string }));
    await selectTable(node.table as string);
    return;
  }
  selectedDatabase.value = node.database as string;
  selectedTable.value = "";
  resetTableView();
  const key = String(node.key);
  if (!expandedKeys.value.includes(key)) {
    expandedKeys.value = [...expandedKeys.value, key];
    if (!node.children) await handleTreeLoad(node);
  }
}

async function selectTable(table: string) {
  selectedTable.value = table;
  dataPagination.page = 1;
  await loadTableData();
}

function resetTableView() {
  selectedTable.value = "";
  tableRows.value = [];
  tableColumns.value = [];
  dataPagination.itemCount = 0;
}

async function loadTableData() {
  if (!selectedTable.value) return;
  loadingData.value = true;
  try {
    const result = await getTableData(
      props.connection.conn_id,
      selectedDatabase.value || "",
      selectedTable.value,
      dataPagination.page,
      dataPagination.pageSize,
      "",
      tableFilter.value
    );
    tableColumns.value = result.columns;
    tableRows.value = result.rows;
    primaryKeys.value = result.primary_keys;
    dataPagination.itemCount = result.total;
  } catch (error) {
    showError(message, error);
  } finally {
    loadingData.value = false;
  }
}

async function executeSql() {
  executing.value = true;
  try {
    queryResult.value = await queryDatabase(props.connection.conn_id, { sql: sql.value, database: selectedDatabase.value || "" });
    message.success(t("database.sql.executed"));
  } catch (error) {
    showError(message, error);
  } finally {
    executing.value = false;
  }
}

function openAddRow() {
  rowModal.mode = "add";
  rowModal.original = null;
  rowModal.json = JSON.stringify(Object.fromEntries(tableColumns.value.map((column) => [column.name, null])), null, 2);
  rowModal.show = true;
}

function openEditRow(row: Record<string, unknown>) {
  rowModal.mode = "edit";
  rowModal.original = row;
  rowModal.json = JSON.stringify(row, null, 2);
  rowModal.show = true;
}

async function saveRow() {
  if (!selectedTable.value) return;
  savingRow.value = true;
  try {
    const values = JSON.parse(rowModal.json) as Record<string, unknown>;
    if (rowModal.mode === "add") {
      await createRow(props.connection.conn_id, { database: selectedDatabase.value, table: selectedTable.value, values });
    } else {
      await updateRow(props.connection.conn_id, {
        database: selectedDatabase.value,
        table: selectedTable.value,
        keys: rowKeys(rowModal.original || {}),
        values
      });
    }
    rowModal.show = false;
    await loadTableData();
  } catch (error) {
    showError(message, error);
  } finally {
    savingRow.value = false;
  }
}

function confirmDeleteRow(row: Record<string, unknown>) {
  dialog.warning({
    title: t("common.confirm"),
    content: t("database.row.deleteConfirm"),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: async () => {
      await deleteRow(props.connection.conn_id, { database: selectedDatabase.value, table: selectedTable.value, keys: rowKeys(row) });
      await loadTableData();
    }
  });
}

function rowKeys(row: Record<string, unknown>) {
  const keys = primaryKeys.value.length ? primaryKeys.value : tableColumns.value.map((column) => column.name);
  return Object.fromEntries(keys.map((key) => [key, row[key]]));
}

async function exportTable(format: string | number) {
  const result = await submitExport(props.connection.conn_id, {
    format: format as DataFormat,
    database: selectedDatabase.value,
    tables: selectedTable.value ? [selectedTable.value] : []
  });
  handleJobSubmitted(result.job_id);
}

async function exportQuery(format: string | number) {
  const result = await submitExport(props.connection.conn_id, {
    format: format as DataFormat,
    database: selectedDatabase.value,
    sql: sql.value
  });
  handleJobSubmitted(result.job_id);
}

function handleJobSubmitted(jobId: string) {
  message.success(t("database.jobs.submitted", { id: jobId }));
}

function createSchemaPrompt() {
  Object.assign(objectModal, { show: true, kind: "schema", name: "", saving: false });
}

function createTablePrompt() {
  if (!selectedDatabase.value) return;
  Object.assign(objectModal, { show: true, kind: "table", name: "", saving: false });
}

function handleCreateSelect(key: string) {
  if (key === "schema") createSchemaPrompt();
  else createTablePrompt();
}

function handleDropSelect(key: string) {
  if (key === "schema") dropSelectedSchema();
  else dropSelectedTable();
}

async function saveObject() {
  const name = objectModal.name.trim();
  if (!name) return;
  objectModal.saving = true;
  try {
    if (objectModal.kind === "schema") {
      await createSchema(props.connection.conn_id, { name });
    } else {
      await createTable(props.connection.conn_id, {
        database: selectedDatabase.value,
        name,
        columns: [
          { name: "id", type: "INT", nullable: false, primary_key: true, autoincrement: true },
          { name: "name", type: "VARCHAR(255)", nullable: true }
        ]
      });
    }
    objectModal.show = false;
    await refreshMetadata();
  } catch (error) {
    showError(message, error);
  } finally {
    objectModal.saving = false;
  }
}

function dropSelectedTable() {
  if (!selectedTable.value) return;
  const database = selectedDatabase.value;
  const table = selectedTable.value;
  dialog.warning({
    title: t("common.confirm"),
    content: t("database.table.dropConfirm"),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: async () => {
      await dropTable(props.connection.conn_id, database, table);
      selectedTable.value = "";
      await refreshMetadata();
    }
  });
}

function dropSelectedSchema() {
  if (!selectedDatabase.value) return;
  const database = selectedDatabase.value;
  dialog.warning({
    title: t("common.confirm"),
    content: t("database.schema.dropConfirm", { name: database }),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: async () => {
      await dropSchema(props.connection.conn_id, database);
      selectedDatabase.value = "";
      selectedTable.value = "";
      await refreshMetadata();
    }
  });
}

async function loadScripts() {
  loadingScripts.value = true;
  try {
    const result = await listSqlScripts({ keyword: scriptKeyword.value, connection_id: props.connection.id, page_size: 100 });
    scripts.value = result.items;
  } catch (error) {
    showError(message, error);
  } finally {
    loadingScripts.value = false;
  }
}

function loadScript(script: SqlScript) {
  sql.value = script.content;
  activeTab.value = "sql";
}

async function executeScript(script: SqlScript) {
  const result = await runSqlScript(props.connection.conn_id, { script_id: script.id, database: selectedDatabase.value });
  message.success(t("database.script.result", { count: result.results.length }));
}

function openSaveScript() {
  scriptModal.name = "";
  scriptModal.description = "";
  scriptModal.is_shared = false;
  scriptModal.show = true;
}

async function saveScript() {
  savingScript.value = true;
  try {
    await createSqlScript({
      name: scriptModal.name || t("database.script.untitled"),
      content: sql.value,
      connection_id: props.connection.id,
      description: scriptModal.description,
      is_shared: scriptModal.is_shared
    });
    scriptModal.show = false;
    await loadScripts();
  } catch (error) {
    showError(message, error);
  } finally {
    savingScript.value = false;
  }
}

function handleDataPage(page: number) {
  dataPagination.page = page;
  void loadTableData();
}

function handleDataPageSize(pageSize: number) {
  dataPagination.pageSize = pageSize;
  dataPagination.page = 1;
  void loadTableData();
}

function formatCell(value: unknown) {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function goJobs() {
  emit("jobs");
}
</script>
