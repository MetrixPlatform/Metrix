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
      <n-badge :value="pendingDownloadCount" :max="99" type="success" :show="pendingDownloadCount > 0">
        <n-button @click="goJobs">{{ t("database.jobs.view") }}</n-button>
      </n-badge>
    </div>

    <div class="database-workbench-body">
      <aside class="database-sidebar">
        <n-tree
          v-if="treeData.length"
          block-line
          class="database-tree"
          :data="treeData"
          :expanded-keys="expandedKeys"
          :selected-keys="selectedKeys"
          :on-load="handleTreeLoad"
          :render-prefix="renderTreePrefix"
          :render-suffix="renderTreeSuffix"
          @update:expanded-keys="handleExpand"
          @update:selected-keys="handleTreeSelect"
        />
        <n-empty v-else class="database-tree-empty" :description="t('database.treeEmpty')">
          <template #extra>
            <permission-button :permission="DATABASE_OPERATE" size="small" @click="createSchemaPrompt">
              {{ t("database.schema.create") }}
            </permission-button>
          </template>
        </n-empty>
      </aside>

      <main class="database-main">
        <n-tabs v-model:value="activeTab" type="line" animated>
          <n-tab-pane class="database-tab-pane" name="data" :tab="t('database.tabs.data')" display-directive="show">
            <div class="database-sub-toolbar">
              <n-input v-model:value="tableFilter" class="filter-keyword" clearable :placeholder="t('database.table.search')" @keyup.enter="loadTableData" />
              <n-button :disabled="!selectedTable" @click="loadTableData">{{ t("common.search") }}</n-button>
              <permission-button :permission="DATABASE_OPERATE" :disabled="!selectedTable" @click="openAddRow">{{ t("database.row.add") }}</permission-button>
              <permission-button :permission="DATABASE_OPERATE" :disabled="!selectedTable" @click="openImport">{{ t("database.import.title") }}</permission-button>
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
              :scroll-x="Math.max(960, dataColumns.length * 180)"
              @update:sorter="handleDataSorter"
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
              <n-button @click="openResultExport">{{ t("database.export.result") }}</n-button>
              <permission-button :permission="SQL_SCRIPT_CREATE" @click="openSaveScript">{{ t("database.script.save") }}</permission-button>
            </div>
            <monaco-editor v-model="sql" class="database-sql-editor" :suggestions="suggestions" />
            <div class="database-result-bar">
              <span class="database-result-title">{{ t("database.sql.resultTitle") }}</span>
              <n-button
                quaternary
                size="small"
                :title="resultCollapsed ? t('database.sql.showResult') : t('database.sql.hideResult')"
                @click="resultCollapsed = !resultCollapsed"
              >
                <template #icon><n-icon :component="resultCollapsed ? ChevronUp20Regular : ChevronDown20Regular" /></template>
                {{ resultCollapsed ? t("database.sql.showResult") : t("database.sql.hideResult") }}
              </n-button>
            </div>
            <n-data-table
              v-show="!resultCollapsed"
              class="page-data-table database-query-table"
              flex-height
              size="small"
              :columns="queryColumns"
              :data="queryRows"
              :loading="executing"
              :scroll-x="Math.max(960, queryColumns.length * 180)"
            />
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

    <n-modal v-model:show="exportModal.show" preset="card" class="modal-card" :title="t('database.export.selectTitle')">
      <div class="form-stack database-export-form">
        <n-empty v-if="!exportModal.statements.length" :description="t('database.export.noQueries')" />
        <n-checkbox-group v-else v-model:value="exportModal.selected" class="database-export-list">
          <n-checkbox v-for="(statement, index) in exportModal.statements" :key="index" :value="index" class="database-export-item">
            {{ exportLabel(index, statement) }}
          </n-checkbox>
        </n-checkbox-group>
        <n-form class="form-stack inline-form" label-placement="left" label-width="auto">
          <n-form-item :label="t('field.format')">
            <n-select v-model:value="exportModal.format" :options="exportFormatOptions" />
          </n-form-item>
        </n-form>
        <span v-if="exportModal.selected.length > 1" class="muted-text">{{ t("database.export.multiHint") }}</span>
      </div>
      <template #action>
        <div class="form-actions modal-fixed-actions">
          <n-button @click="exportModal.show = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" :disabled="!exportModal.selected.length" @click="submitResultExport">{{ t("database.export.title") }}</n-button>
        </div>
      </template>
    </n-modal>

    <import-wizard
      v-model:show="showImport"
      :conn-id="connection.conn_id"
      :database="importTarget.database"
      :table="importTarget.table"
      @submitted="handleJobSubmitted"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref, watch, type Component, type VNode } from "vue";
import {
  ArrowClockwise20Regular,
  ArrowLeft20Regular,
  ChevronDown20Regular,
  ChevronUp20Regular,
  Database20Regular,
  DocumentText20Regular,
  Folder20Regular,
  MoreHorizontal20Regular,
  Table20Regular
} from "@vicons/fluent";
import {
  NButton,
  NBadge,
  NCheckbox,
  NCheckboxGroup,
  NDataTable,
  NDropdown,
  NEmpty,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NModal,
  NSelect,
  NSwitch,
  NTabPane,
  NTabs,
  NTag,
  NTree,
  useDialog,
  useMessage
} from "naive-ui";
import type { DataTableColumns, DataTableSortState, DropdownOption, TreeOption } from "naive-ui";

import PermissionButton from "../../../components/PermissionButton.vue";
import { t } from "../../../i18n";
import { authStore } from "../../../stores/auth";
import { showError } from "../../../utils/message";
import {
  createRow,
  createSchema,
  createSqlScript,
  createTable,
  deleteRow,
  deleteSqlScript,
  dropSchema,
  dropTable,
  getDataJobDownloadCount,
  getTableData,
  listSchemas,
  listSqlScripts,
  listTables,
  queryDatabase,
  runSqlScript,
  submitExport,
  truncateTable,
  updateRow,
  type ColumnItem,
  type DatabaseConnection,
  type DataFormat,
  type QueryResult,
  type SqlScript,
  type TableItem
} from "../api";
import { DATABASE_OPERATE, SQL_SCRIPT_CREATE, SQL_SCRIPT_DELETE } from "../permissions";
import ImportWizard from "./ImportWizard.vue";
import MonacoEditor from "./MonacoEditor.vue";

const props = defineProps<{ connection: DatabaseConnection }>();
const emit = defineEmits<{
  (event: "close"): void;
  (event: "jobs", scope: { connectionId: number; connectionName: string }): void;
}>();

const message = useMessage();
const dialog = useDialog();
const activeTab = ref<"data" | "sql">("data");
const schemas = ref<{ name: string }[]>([]);
const tables = ref<TableItem[]>([]);
const treeData = ref<TreeOption[]>([]);
const expandedKeys = ref<string[]>([]);
const selectedKeys = ref<string[]>([]);
const selectedDatabase = ref(props.connection.default_database || "");
const selectedTable = ref("");
const tableColumns = ref<ColumnItem[]>([]);
const tableRows = ref<Record<string, unknown>[]>([]);
const primaryKeys = ref<string[]>([]);
const tableFilter = ref("");
const dataSort = reactive<{ columnKey: string | null; order: "ascend" | "descend" | false }>({ columnKey: null, order: false });
const loadingData = ref(false);
const executing = ref(false);
const resultCollapsed = ref(false);
const sql = ref("SELECT 1;");
const queryResult = ref<QueryResult | null>(null);
const savingRow = ref(false);
const savingScript = ref(false);
const showImport = ref(false);
const importTarget = reactive({ database: "", table: "" });
const pendingDownloadCount = ref(0);
const exportModal = reactive({
  show: false,
  format: "xlsx" as DataFormat,
  statements: [] as string[],
  selected: [] as number[]
});
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

const canOperate = computed(() => authStore.has(DATABASE_OPERATE));
const canDeleteScript = computed(() => authStore.has(SQL_SCRIPT_DELETE));
const exportFormatOptions = computed(() => {
  const all = [
    { label: "CSV", value: "csv" },
    { label: "XLSX", value: "xlsx" },
    { label: "SQLite", value: "sqlite" },
    { label: "SQL", value: "sql" }
  ];
  return exportModal.selected.length > 1 ? all.filter((option) => option.value !== "csv") : all;
});

watch(
  () => exportModal.selected.length,
  (count) => {
    if (count > 1 && exportModal.format === "csv") exportModal.format = "xlsx";
  }
);
const objectModalTitle = computed(() => (objectModal.kind === "schema" ? t("database.schema.create") : t("database.table.create")));
const suggestions = computed(() => [
  ...schemas.value.map((item) => item.name),
  ...tables.value.map((item) => item.name),
  ...tableColumns.value.map((item) => item.name)
]);

const PREFIX_ICONS: Record<string, Component> = {
  schema: Database20Regular,
  tablesCat: Folder20Regular,
  scriptsCat: Folder20Regular,
  table: Table20Regular,
  script: DocumentText20Regular
};

const dataColumns = computed<DataTableColumns<Record<string, unknown>>>(() => [
  ...tableColumns.value.map((column) => ({
    title: column.name,
    key: column.name,
    width: 180,
    minWidth: 80,
    resizable: true,
    sorter: true,
    sortOrder: dataSort.columnKey === column.name ? dataSort.order : false,
    ellipsis: { tooltip: true },
    render: (row: Record<string, unknown>) => formatCell(row[column.name])
  })),
  {
    title: t("common.actions"),
    key: "actions",
    fixed: "right",
    width: 150,
    resizable: false,
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
  return columns.map((column) => ({
    title: column,
    key: column,
    width: 180,
    minWidth: 80,
    resizable: true,
    sorter: "default" as const,
    ellipsis: { tooltip: true },
    render: (row) => formatCell(row[column])
  }));
});
const queryRows = computed(() => queryResult.value?.rows || []);

onMounted(async () => {
  await refreshMetadata();
  await loadDownloadCount();
});

function schemaKey(name: string) {
  return `schema:${name}`;
}
function tablesCatKey(database: string) {
  return `tables:${database}`;
}
function scriptsCatKey(database: string) {
  return `scripts:${database}`;
}
function tableNodeKey(database: string, table: string) {
  return `table:${database}:${table}`;
}
function scriptNodeKey(database: string, id: number) {
  return `script:${database}:${id}`;
}

function renderTreePrefix({ option }: { option: TreeOption }) {
  return h(NIcon, { component: PREFIX_ICONS[String(option.kind)] || Table20Regular });
}

function renderTreeSuffix({ option }: { option: TreeOption }) {
  if (option.kind === "schema") {
    const database = option.database as string;
    const actions: VNode[] = [iconButton(ArrowClockwise20Regular, t("common.refresh"), () => void reloadSchema(database))];
    if (canOperate.value) {
      actions.push(
        opsButton(
          [
            { label: t("database.schema.create"), key: "schema-create" },
            { label: t("database.table.create"), key: "table-create" },
            { label: t("database.schema.drop"), key: "schema-drop" }
          ],
          (key) => handleSchemaOp(key, database)
        )
      );
    }
    return nodeActions(actions);
  }
  if (option.kind === "table" && canOperate.value) {
    const database = option.database as string;
    const table = option.table as string;
    return nodeActions([
      opsButton(
        [
          { label: t("database.import.title"), key: "import" },
          { label: t("database.table.truncate"), key: "truncate" },
          { label: t("database.table.drop"), key: "drop" }
        ],
        (key) => handleTableOp(key, database, table)
      )
    ]);
  }
  if (option.kind === "script") {
    const script = option.script as SqlScript;
    const options: DropdownOption[] = [
      { label: t("database.script.load"), key: "load" },
      { label: t("database.script.run"), key: "run" }
    ];
    if (canDeleteScript.value) options.push({ label: t("common.delete"), key: "delete" });
    return nodeActions([opsButton(options, (key) => handleScriptOp(key, script))]);
  }
  return null;
}

function nodeActions(children: VNode[]) {
  return h("div", { class: "database-node-actions", onClick: (event: MouseEvent) => event.stopPropagation() }, children);
}

function iconButton(icon: Component, title: string, onClick: () => void): VNode {
  return h(
    NButton,
    { size: "tiny", quaternary: true, circle: true, title, onClick },
    { icon: () => h(NIcon, { component: icon }) }
  );
}

function opsButton(options: DropdownOption[], onSelect: (key: string) => void): VNode {
  return h(
    NDropdown,
    { trigger: "click", placement: "bottom-end", options, onSelect: (key: string | number) => onSelect(String(key)) },
    {
      default: () =>
        h(
          NButton,
          { size: "tiny", quaternary: true, circle: true, title: t("common.actions") },
          { icon: () => h(NIcon, { component: MoreHorizontal20Regular }) }
        )
    }
  );
}

async function refreshMetadata() {
  try {
    schemas.value = await listSchemas(props.connection.conn_id);
    const names = schemas.value.map((item) => item.name);
    const initial = selectedDatabase.value && names.includes(selectedDatabase.value) ? selectedDatabase.value : names[0] || "";
    treeData.value = schemas.value.map((schema) => ({
      key: schemaKey(schema.name),
      label: schema.name,
      kind: "schema",
      database: schema.name,
      isLeaf: false,
      children: [
        { key: tablesCatKey(schema.name), label: t("database.tree.tables"), kind: "tablesCat", database: schema.name, isLeaf: false },
        { key: scriptsCatKey(schema.name), label: t("database.tree.scripts"), kind: "scriptsCat", database: schema.name, isLeaf: false }
      ]
    }));
    expandedKeys.value = [];
    selectedKeys.value = [];
    selectedDatabase.value = initial;
    if (initial) await openSchemaTables(initial);
    else resetTableView();
  } catch (error) {
    showError(message, error);
  }
}

function findSchemaNode(database: string) {
  return treeData.value.find((node) => node.kind === "schema" && node.database === database);
}

function findCategory(database: string, kind: "tablesCat" | "scriptsCat") {
  return findSchemaNode(database)?.children?.find((node) => node.kind === kind);
}

async function loadTableNodes(database: string): Promise<TreeOption[]> {
  const items = await listTables(props.connection.conn_id, database);
  return items.map((item) => ({
    key: tableNodeKey(database, item.name),
    label: item.name,
    kind: "table",
    database,
    table: item.name,
    isLeaf: true
  }));
}

async function loadScriptNodes(database: string): Promise<TreeOption[]> {
  const result = await listSqlScripts({ connection_id: props.connection.id, database, page_size: 100 });
  return result.items.map((item) => ({
    key: scriptNodeKey(database, item.id),
    label: item.name,
    kind: "script",
    database,
    script: item,
    isLeaf: true
  }));
}

async function handleTreeLoad(node: TreeOption) {
  if (node.kind === "tablesCat") {
    node.children = await loadTableNodes(node.database as string);
    if (node.database === selectedDatabase.value) updateTablesForDb(node.database as string);
  } else if (node.kind === "scriptsCat") {
    node.children = await loadScriptNodes(node.database as string);
  }
}

async function openSchemaTables(database: string) {
  const cat = findCategory(database, "tablesCat");
  if (!cat) {
    resetTableView();
    return;
  }
  cat.children = await loadTableNodes(database);
  updateTablesForDb(database);
  expandedKeys.value = [schemaKey(database), tablesCatKey(database)];
  const match = cat.children.find((child) => child.table === selectedTable.value) || cat.children[0];
  if (match) {
    selectedKeys.value = [String(match.key)];
    await selectTable(database, match.table as string);
  } else {
    selectedKeys.value = [schemaKey(database)];
    resetTableView();
  }
}

function updateTablesForDb(database: string) {
  const cat = findCategory(database, "tablesCat");
  tables.value = (cat?.children || []).map((child) => ({ name: child.table as string }));
}

function handleExpand(keys: Array<string | number>) {
  expandedKeys.value = keys.map(String);
}

async function handleTreeSelect(keys: Array<string | number>, options: Array<TreeOption | null>) {
  const node = options[0];
  if (!node) return;
  selectedKeys.value = keys.map(String);
  if (node.kind === "table") {
    updateTablesForDb(node.database as string);
    await selectTable(node.database as string, node.table as string);
    return;
  }
  if (node.kind === "script") {
    loadScriptIntoEditor(node.script as SqlScript);
    return;
  }
  selectedDatabase.value = node.database as string;
  if (node.kind === "schema") {
    selectedTable.value = "";
    resetTableView();
  }
  await toggleNode(node);
}

async function toggleNode(node: TreeOption) {
  const key = String(node.key);
  if (expandedKeys.value.includes(key)) {
    expandedKeys.value = expandedKeys.value.filter((item) => item !== key);
    return;
  }
  expandedKeys.value = [...expandedKeys.value, key];
  if (!node.children && !node.isLeaf) await handleTreeLoad(node);
}

async function reloadSchema(database: string) {
  try {
    const tablesCat = findCategory(database, "tablesCat");
    if (tablesCat?.children) {
      tablesCat.children = await loadTableNodes(database);
      if (database === selectedDatabase.value) updateTablesForDb(database);
    }
    const scriptsCat = findCategory(database, "scriptsCat");
    if (scriptsCat?.children) scriptsCat.children = await loadScriptNodes(database);
  } catch (error) {
    showError(message, error);
  }
}

async function reloadScripts() {
  for (const schema of treeData.value) {
    const cat = schema.children?.find((node) => node.kind === "scriptsCat");
    if (cat?.children) cat.children = await loadScriptNodes(schema.database as string);
  }
}

async function selectTable(database: string, table: string) {
  selectedDatabase.value = database;
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

function handleDataSorter(sorter: DataTableSortState | DataTableSortState[] | null) {
  const state = Array.isArray(sorter) ? sorter[0] : sorter;
  if (!state || !state.order) {
    dataSort.columnKey = null;
    dataSort.order = false;
  } else {
    dataSort.columnKey = String(state.columnKey);
    dataSort.order = state.order;
  }
  dataPagination.page = 1;
  void loadTableData();
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
      dataSort.columnKey || "",
      dataSort.order === "descend",
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
    resultCollapsed.value = false;
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

function confirmAction(content: string, onConfirm: () => Promise<void>, positiveText: string = t("common.delete")) {
  dialog.warning({
    title: t("common.confirm"),
    content,
    positiveText,
    negativeText: t("common.cancel"),
    onPositiveClick: onConfirm
  });
}

function confirmDeleteRow(row: Record<string, unknown>) {
  confirmAction(t("database.row.deleteConfirm"), async () => {
    await deleteRow(props.connection.conn_id, { database: selectedDatabase.value, table: selectedTable.value, keys: rowKeys(row) });
    await loadTableData();
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

function openResultExport() {
  const statements = splitReadStatements(sql.value);
  exportModal.statements = statements;
  exportModal.selected = statements.map((_, index) => index);
  exportModal.format = statements.length > 1 ? "xlsx" : "csv";
  exportModal.show = true;
}

function exportLabel(index: number, statement: string) {
  const oneLine = statement.replace(/\s+/g, " ").trim();
  const preview = oneLine.length > 60 ? `${oneLine.slice(0, 60)}…` : oneLine;
  return `${t("database.export.resultItem", { index: index + 1 })}: ${preview}`;
}

async function submitResultExport() {
  const picked = exportModal.selected
    .slice()
    .sort((a, b) => a - b)
    .map((index) => exportModal.statements[index])
    .filter(Boolean);
  if (!picked.length) return;
  const result = await submitExport(props.connection.conn_id, {
    format: exportModal.format,
    database: selectedDatabase.value,
    queries: picked.map((statement, index) => ({ name: `result_${index + 1}`, sql: statement }))
  });
  exportModal.show = false;
  handleJobSubmitted(result.job_id);
}

function splitReadStatements(text: string): string[] {
  return splitSqlStatements(text).filter((statement) => /^\s*(select|with)\b/i.test(statement));
}

function splitSqlStatements(text: string): string[] {
  const statements: string[] = [];
  let buffer = "";
  let quote = "";
  let index = 0;
  while (index < text.length) {
    const char = text[index];
    const next = text[index + 1];
    if (quote) {
      buffer += char;
      if (char === "\\" && quote !== "`") {
        buffer += next ?? "";
        index += 2;
        continue;
      }
      if (char === quote) quote = "";
      index += 1;
      continue;
    }
    if (char === "'" || char === '"' || char === "`") {
      quote = char;
      buffer += char;
      index += 1;
      continue;
    }
    if (char === "-" && next === "-") {
      while (index < text.length && text[index] !== "\n") {
        buffer += text[index];
        index += 1;
      }
      continue;
    }
    if (char === "/" && next === "*") {
      buffer += "/*";
      index += 2;
      while (index < text.length && !(text[index] === "*" && text[index + 1] === "/")) {
        buffer += text[index];
        index += 1;
      }
      buffer += "*/";
      index += 2;
      continue;
    }
    if (char === ";") {
      if (buffer.trim()) statements.push(buffer.trim());
      buffer = "";
      index += 1;
      continue;
    }
    buffer += char;
    index += 1;
  }
  if (buffer.trim()) statements.push(buffer.trim());
  return statements;
}

function handleJobSubmitted(jobId: string) {
  message.success(t("database.jobs.submitted", { id: jobId }));
  void loadDownloadCount();
}

function createSchemaPrompt() {
  Object.assign(objectModal, { show: true, kind: "schema", name: "", saving: false });
}

function createTablePrompt() {
  if (!selectedDatabase.value) return;
  Object.assign(objectModal, { show: true, kind: "table", name: "", saving: false });
}

function handleSchemaOp(key: string, database: string) {
  if (key === "schema-create") createSchemaPrompt();
  else if (key === "table-create") {
    selectedDatabase.value = database;
    createTablePrompt();
  } else if (key === "schema-drop") dropSchemaByName(database);
}

function handleTableOp(key: string, database: string, table: string) {
  if (key === "import") openImportForTable(database, table);
  else if (key === "truncate") truncateTableByName(database, table);
  else if (key === "drop") dropTableByName(database, table);
}

function openImport() {
  importTarget.database = selectedDatabase.value;
  importTarget.table = selectedTable.value;
  showImport.value = true;
}

function openImportForTable(database: string, table: string) {
  importTarget.database = database;
  importTarget.table = table;
  showImport.value = true;
}

function handleScriptOp(key: string, script: SqlScript) {
  if (key === "load") loadScriptIntoEditor(script);
  else if (key === "run") void executeScript(script);
  else if (key === "delete") confirmDeleteScript(script);
}

async function saveObject() {
  const name = objectModal.name.trim();
  if (!name) return;
  objectModal.saving = true;
  try {
    if (objectModal.kind === "schema") {
      await createSchema(props.connection.conn_id, { name });
      objectModal.show = false;
      selectedDatabase.value = name;
      selectedTable.value = "";
      await refreshMetadata();
    } else {
      const database = selectedDatabase.value;
      await createTable(props.connection.conn_id, {
        database,
        name,
        columns: [
          { name: "id", type: "INT", nullable: false, primary_key: true, autoincrement: true },
          { name: "name", type: "VARCHAR(255)", nullable: true }
        ]
      });
      objectModal.show = false;
      selectedTable.value = name;
      await openSchemaTables(database);
    }
  } catch (error) {
    showError(message, error);
  } finally {
    objectModal.saving = false;
  }
}

function dropTableByName(database: string, table: string) {
  confirmAction(t("database.table.dropConfirm", { name: table }), async () => {
    await dropTable(props.connection.conn_id, database, table);
    if (selectedDatabase.value === database && selectedTable.value === table) resetTableView();
    await reloadSchema(database);
  });
}

function truncateTableByName(database: string, table: string) {
  confirmAction(
    t("database.table.truncateConfirm", { name: table }),
    async () => {
      await truncateTable(props.connection.conn_id, database, table);
      if (selectedDatabase.value === database && selectedTable.value === table) await loadTableData();
    },
    t("common.confirm")
  );
}

function dropSchemaByName(database: string) {
  confirmAction(t("database.schema.dropConfirm", { name: database }), async () => {
    await dropSchema(props.connection.conn_id, database);
    if (selectedDatabase.value === database) {
      selectedDatabase.value = "";
      selectedTable.value = "";
    }
    await refreshMetadata();
  });
}

function loadScriptIntoEditor(script: SqlScript) {
  sql.value = script.content;
  activeTab.value = "sql";
}

async function executeScript(script: SqlScript) {
  try {
    const result = await runSqlScript(props.connection.conn_id, { script_id: script.id, database: selectedDatabase.value });
    message.success(t("database.script.result", { count: result.results.length }));
  } catch (error) {
    showError(message, error);
  }
}

function confirmDeleteScript(script: SqlScript) {
  confirmAction(t("database.script.deleteConfirm", { name: script.name }), async () => {
    await deleteSqlScript(script.id);
    await reloadScripts();
  });
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
      database: selectedDatabase.value,
      description: scriptModal.description,
      is_shared: scriptModal.is_shared
    });
    scriptModal.show = false;
    await reloadScripts();
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
  emit("jobs", { connectionId: props.connection.id, connectionName: props.connection.name });
}

async function loadDownloadCount() {
  try {
    pendingDownloadCount.value = (await getDataJobDownloadCount({ connection_id: props.connection.id })).count;
  } catch {
    pendingDownloadCount.value = 0;
  }
}
</script>
