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

    <div ref="workbenchBodyRef" class="database-workbench-body" :style="workbenchBodyStyle">
      <aside class="database-sidebar">
        <n-tree
          v-if="treeData.length"
          block-line
          class="database-tree"
          :data="treeData"
          :expanded-keys="expandedKeys"
          :selected-keys="selectedKeys"
          :on-load="handleTreeLoad"
          :render-label="renderTreeLabel"
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
      <div
        class="database-sidebar-resizer"
        role="separator"
        aria-orientation="vertical"
        :aria-valuenow="sidebarWidth"
        :aria-valuemin="SIDEBAR_MIN_WIDTH"
        :aria-valuemax="SIDEBAR_MAX_WIDTH"
        @mousedown="startSidebarResize"
        @dblclick="resetSidebarWidth"
      />

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
              :scroll-x="Math.max(960, dataColumns.length * 180 + TABLE_SCROLL_END_BUFFER)"
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
              <n-tag v-if="currentScript" class="database-active-schema" size="small" :bordered="false">
                {{ currentScript.name }}
              </n-tag>
              <n-button v-if="currentScript" @click="scriptDetailModal.show = true">{{ t("database.script.detail") }}</n-button>
              <n-button type="primary" :loading="executing" @click="executeSql">{{ t("database.sql.execute") }}</n-button>
              <n-button @click="openResultExport">{{ t("database.export.result") }}</n-button>
              <permission-button :permission="scriptSavePermission" @click="openSaveScript">{{ scriptSaveText }}</permission-button>
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
              :scroll-x="Math.max(960, queryColumns.length * 180 + TABLE_SCROLL_END_BUFFER)"
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

    <n-modal v-model:show="scriptModal.show" preset="card" class="modal-card" :title="scriptModalTitle">
      <n-form class="form-stack inline-form" label-placement="left" label-width="auto">
        <n-form-item :label="t('field.name')">
          <n-input v-model:value="scriptModal.name" />
        </n-form-item>
        <n-form-item :label="t('field.description')">
          <n-input v-model:value="scriptModal.description" />
        </n-form-item>
        <n-form-item :label="t('database.script.content')">
          <n-input v-model:value="scriptModal.content" type="textarea" :autosize="{ minRows: 8, maxRows: 16 }" />
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

    <n-modal v-model:show="scriptDetailModal.show" preset="card" class="modal-card" :title="t('database.script.detail')">
      <div v-if="currentScript" class="database-detail-list">
        <div><span>{{ t("database.script.id") }}</span><strong>{{ currentScript.id }}</strong></div>
        <div><span>{{ t("database.script.statementCount") }}</span><strong>{{ currentScript.statement_count }}</strong></div>
        <div><span>{{ t("field.createdAt") }}</span><strong>{{ formatDateTime(currentScript.created_at) }}</strong></div>
        <div><span>{{ t("field.updatedAt") }}</span><strong>{{ formatDateTime(currentScript.updated_at) }}</strong></div>
      </div>
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

    <n-modal v-model:show="tableDesigner.show" preset="card" class="modal-card table-designer-modal" :title="tableDesignerTitle">
      <div class="table-designer">
        <n-form class="form-stack inline-form" label-placement="left" label-width="auto">
          <n-form-item :label="t('database.table.name')">
            <n-input v-model:value="tableDesigner.name" />
          </n-form-item>
        </n-form>
        <section class="table-designer-section">
          <div class="table-designer-section-head">
            <strong>{{ t("database.table.columns") }}</strong>
            <n-button size="small" @click="addDesignerColumn">{{ t("database.table.addColumn") }}</n-button>
          </div>
          <div class="table-designer-grid table-designer-columns">
            <span>{{ t("field.name") }}</span>
            <span>{{ t("database.table.columnType") }}</span>
            <span>{{ t("database.table.nullable") }}</span>
            <span>{{ t("database.table.primaryKey") }}</span>
            <span>{{ t("database.table.autoincrement") }}</span>
            <span>{{ t("database.table.defaultValue") }}</span>
            <span>{{ t("field.description") }}</span>
            <span>{{ t("common.actions") }}</span>
            <template v-for="column in tableDesigner.columns" :key="column.key">
              <n-input v-model:value="column.name" size="small" :disabled="column.drop" :class="{ 'database-dropped-row': column.drop }" />
              <div class="table-designer-type-control">
                <n-select v-model:value="column.typeName" size="small" :options="columnTypeOptions" :disabled="column.drop" @update:value="syncColumnType(column)" />
                <n-input-number
                  v-if="column.typeName !== CUSTOM_COLUMN_TYPE"
                  v-model:value="column.typeLength"
                  size="small"
                  :show-button="false"
                  :min="1"
                  :max="65535"
                  :disabled="column.drop || !typeAllowsLength(column.typeName)"
                  :placeholder="t('database.table.typeLength')"
                  @update:value="syncColumnType(column)"
                />
                <n-input
                  v-else
                  v-model:value="column.customType"
                  size="small"
                  :disabled="column.drop"
                  :placeholder="t('database.table.customType')"
                  @update:value="syncColumnType(column)"
                />
              </div>
              <n-checkbox v-model:checked="column.nullable" :disabled="column.drop" />
              <n-checkbox v-model:checked="column.primary_key" :disabled="column.drop" />
              <n-checkbox v-model:checked="column.autoincrement" :disabled="column.drop" />
              <n-input v-model:value="column.default" size="small" :disabled="column.drop" />
              <n-input v-model:value="column.comment" size="small" :disabled="column.drop" />
              <n-button size="tiny" quaternary :type="column.drop ? 'default' : 'error'" @click="toggleDesignerColumnDrop(column)">
                {{ column.drop ? t("database.table.restore") : t("common.delete") }}
              </n-button>
            </template>
          </div>
        </section>
        <section class="table-designer-section">
          <div class="table-designer-section-head">
            <strong>{{ t("database.table.indexes") }}</strong>
            <n-button size="small" @click="addDesignerIndex">{{ t("database.table.addIndex") }}</n-button>
          </div>
          <div class="table-designer-grid table-designer-indexes">
            <span>{{ t("field.name") }}</span>
            <span>{{ t("database.table.indexColumns") }}</span>
            <span>{{ t("database.table.unique") }}</span>
            <span>{{ t("common.actions") }}</span>
            <template v-for="index in tableDesigner.indexes" :key="index.key">
              <n-input v-model:value="index.name" size="small" :disabled="index.existing || index.drop" :class="{ 'database-dropped-row': index.drop }" />
              <n-input v-model:value="index.columns" size="small" :disabled="index.drop" :placeholder="t('database.table.indexColumnsPlaceholder')" />
              <n-checkbox v-model:checked="index.unique" :disabled="index.drop" />
              <n-button size="tiny" quaternary :type="index.drop ? 'default' : 'error'" @click="toggleDesignerIndexDrop(index)">
                {{ index.drop ? t("database.table.restore") : t("common.delete") }}
              </n-button>
            </template>
          </div>
        </section>
      </div>
      <template #action>
        <div class="form-actions modal-fixed-actions">
          <n-button @click="tableDesigner.show = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" :loading="tableDesigner.saving" @click="saveTableDesigner">{{ t("common.save") }}</n-button>
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
import { computed, h, onBeforeUnmount, onMounted, reactive, ref, watch, type Component, type VNode } from "vue";
import {
  Add20Regular,
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
  NInputNumber,
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
import { formatDateTime, t } from "../../../i18n";
import { authStore } from "../../../stores/auth";
import { showError } from "../../../utils/message";
import { withResizableColumns } from "../../../utils/table";
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
  getSqlScript,
  getTableStructure,
  getTableData,
  listSchemas,
  listSqlScripts,
  listTables,
  queryDatabase,
  runSqlScript,
  submitExport,
  truncateTable,
  alterTable,
  renameTable,
  updateRow,
  updateSqlScript,
  type AlterTablePayload,
  type ColumnItem,
  type ColumnDefinition,
  type DatabaseConnection,
  type DataFormat,
  type IndexDefinition,
  type QueryResult,
  type SqlScript,
  type TableIndexItem,
  type TableItem
} from "../api";
import { DATABASE_OPERATE, SQL_SCRIPT_CREATE, SQL_SCRIPT_DELETE, SQL_SCRIPT_UPDATE } from "../permissions";
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
const SIDEBAR_DEFAULT_WIDTH = 280;
const SIDEBAR_MIN_WIDTH = 220;
const SIDEBAR_MAX_WIDTH = 560;
const SIDEBAR_MIN_MAIN_WIDTH = 520;
const SIDEBAR_WIDTH_STORAGE_KEY = "metrix.databaseWorkbench.sidebarWidth";
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
const dataTotalExact = ref(true);
const dataSort = reactive<{ columnKey: string | null; order: "ascend" | "descend" | false }>({ columnKey: null, order: false });
const loadingData = ref(false);
const executing = ref(false);
const resultCollapsed = ref(false);
const sql = ref("SELECT 1;");
const queryResult = ref<QueryResult | null>(null);
const currentScript = ref<SqlScript | null>(null);
const savingRow = ref(false);
const savingScript = ref(false);
const showImport = ref(false);
const importTarget = reactive({ database: "", table: "" });
const pendingDownloadCount = ref(0);
const workbenchBodyRef = ref<HTMLElement | null>(null);
const sidebarWidth = ref(loadSidebarWidth());
const resizeState = reactive({
  resizing: false,
  startX: 0,
  startWidth: SIDEBAR_DEFAULT_WIDTH
});
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
  mode: "create" as "create" | "update",
  id: null as number | null,
  name: "",
  description: "",
  is_shared: false,
  content: ""
});
const scriptDetailModal = reactive({
  show: false
});
const objectModal = reactive({
  show: false,
  kind: "schema" as "schema" | "table",
  name: "",
  saving: false
});
interface TableColumnDraft {
  key: string;
  existing: boolean;
  original: ColumnDefinition;
  name: string;
  type: string;
  typeName: string;
  typeLength: number | null;
  customType: string;
  typeSuffix: string;
  nullable: boolean;
  primary_key: boolean;
  autoincrement: boolean;
  default: string;
  comment: string;
  drop: boolean;
}
interface TableIndexDraft {
  key: string;
  existing: boolean;
  original: IndexDefinition;
  name: string;
  columns: string;
  unique: boolean;
  drop: boolean;
}
const tableDesigner = reactive({
  show: false,
  mode: "create" as "create" | "edit",
  database: "",
  name: "",
  originalName: "",
  columns: [] as TableColumnDraft[],
  indexes: [] as TableIndexDraft[],
  saving: false
});
const dataPagination = reactive({
  page: 1,
  pageSize: 50,
  itemCount: 0,
  pageSizes: [50, 100, 200, 500],
  showSizePicker: true,
  prefix: ({ itemCount }: { itemCount: number | undefined }) =>
    dataTotalExact.value ? t("common.total", { count: itemCount ?? 0 }) : t("database.table.totalEstimate", { count: itemCount ?? 0 })
});
const exportOptions = [
  { label: "CSV", key: "csv" },
  { label: "XLSX", key: "xlsx" },
  { label: "SQLite", key: "sqlite" },
  { label: "SQL", key: "sql" }
];
const CUSTOM_COLUMN_TYPE = "__custom";
const LENGTH_COLUMN_TYPES = new Set(["VARCHAR", "CHAR", "DECIMAL", "NUMERIC"]);
const COLLATION_COLUMN_TYPES = new Set(["VARCHAR", "CHAR", "TEXT", "LONGTEXT"]);
const columnTypeOptions = [
  { label: "INT", value: "INT" },
  { label: "BIGINT", value: "BIGINT" },
  { label: "TINYINT", value: "TINYINT" },
  { label: "DECIMAL", value: "DECIMAL" },
  { label: "VARCHAR", value: "VARCHAR" },
  { label: "CHAR", value: "CHAR" },
  { label: "TEXT", value: "TEXT" },
  { label: "LONGTEXT", value: "LONGTEXT" },
  { label: "DATE", value: "DATE" },
  { label: "DATETIME", value: "DATETIME" },
  { label: "TIMESTAMP", value: "TIMESTAMP" },
  { label: t("database.table.customType"), value: CUSTOM_COLUMN_TYPE }
];

const canOperate = computed(() => authStore.has(DATABASE_OPERATE));
const canDeleteScript = computed(() => authStore.has(SQL_SCRIPT_DELETE));
const scriptSavePermission = computed(() => (currentScript.value ? SQL_SCRIPT_UPDATE : SQL_SCRIPT_CREATE));
const scriptSaveText = computed(() => (currentScript.value ? t("database.script.update") : t("database.script.save")));
const scriptModalTitle = computed(() => (scriptModal.mode === "update" ? t("database.script.update") : t("database.script.save")));
const tableDesignerTitle = computed(() => (tableDesigner.mode === "edit" ? t("database.table.editStructure") : t("database.table.create")));
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
const workbenchBodyStyle = computed(() => ({ "--database-sidebar-width": `${sidebarWidth.value}px` }));
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
let tableDataRequestId = 0;
const TABLE_SCROLL_END_BUFFER = 64;

const dataColumns = computed<DataTableColumns<Record<string, unknown>>>(() =>
  withResizableColumns([
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
  ])
);
const queryColumns = computed<DataTableColumns<Record<string, unknown>>>(() => {
  const columns = queryResult.value?.columns || [];
  if (!columns.length && queryResult.value?.statement_type === "write") {
    return [{ title: t("database.sql.affectedRows"), key: "affected_rows", render: () => queryResult.value?.affected_rows ?? 0 }];
  }
  return withResizableColumns(
    columns.map((column) => ({
      title: column,
      key: column,
      width: 180,
      minWidth: 80,
      resizable: true,
      sorter: "default" as const,
      ellipsis: { tooltip: true },
      render: (row) => formatCell(row[column])
    }))
  );
});
const queryRows = computed(() => queryResult.value?.rows || []);

onMounted(async () => {
  sidebarWidth.value = clampSidebarWidth(sidebarWidth.value);
  window.addEventListener("resize", clampSidebarWidthToViewport);
  await refreshMetadata();
  await loadDownloadCount();
});

onBeforeUnmount(() => {
  stopSidebarResize();
  window.removeEventListener("resize", clampSidebarWidthToViewport);
});

function loadSidebarWidth() {
  const saved = Number(localStorage.getItem(SIDEBAR_WIDTH_STORAGE_KEY));
  return clampSidebarWidth(Number.isFinite(saved) ? saved : SIDEBAR_DEFAULT_WIDTH);
}

function clampSidebarWidth(width: number) {
  const bodyWidth = workbenchBodyRef.value?.clientWidth ?? 0;
  const layoutMax = bodyWidth > 0 ? Math.max(SIDEBAR_MIN_WIDTH, bodyWidth - SIDEBAR_MIN_MAIN_WIDTH) : SIDEBAR_MAX_WIDTH;
  const maxWidth = Math.min(SIDEBAR_MAX_WIDTH, layoutMax);
  return Math.min(Math.max(Math.round(width), SIDEBAR_MIN_WIDTH), maxWidth);
}

function saveSidebarWidth() {
  localStorage.setItem(SIDEBAR_WIDTH_STORAGE_KEY, String(sidebarWidth.value));
}

function startSidebarResize(event: MouseEvent) {
  event.preventDefault();
  resizeState.resizing = true;
  resizeState.startX = event.clientX;
  resizeState.startWidth = sidebarWidth.value;
  document.body.classList.add("database-sidebar-resizing");
  window.addEventListener("mousemove", handleSidebarResize);
  window.addEventListener("mouseup", stopSidebarResize);
}

function handleSidebarResize(event: MouseEvent) {
  if (!resizeState.resizing) return;
  sidebarWidth.value = clampSidebarWidth(resizeState.startWidth + event.clientX - resizeState.startX);
}

function clampSidebarWidthToViewport() {
  sidebarWidth.value = clampSidebarWidth(sidebarWidth.value);
}

function stopSidebarResize() {
  if (resizeState.resizing) saveSidebarWidth();
  resizeState.resizing = false;
  document.body.classList.remove("database-sidebar-resizing");
  window.removeEventListener("mousemove", handleSidebarResize);
  window.removeEventListener("mouseup", stopSidebarResize);
}

function resetSidebarWidth() {
  sidebarWidth.value = clampSidebarWidth(SIDEBAR_DEFAULT_WIDTH);
  saveSidebarWidth();
}

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

function renderTreeLabel({ option }: { option: TreeOption }) {
  const label = String(option.label ?? "");
  return h("span", { class: "database-tree-label", title: label }, label);
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
  if (option.kind === "tablesCat" && canOperate.value) {
    const database = option.database as string;
    return nodeActions([iconButton(Add20Regular, t("database.table.create"), () => openCreateTableDesigner(database))]);
  }
  if (option.kind === "scriptsCat" && authStore.has(SQL_SCRIPT_CREATE)) {
    const database = option.database as string;
    return nodeActions([iconButton(Add20Regular, t("database.script.create"), () => openCreateScript(database))]);
  }
  if (option.kind === "table" && canOperate.value) {
    const database = option.database as string;
    const table = option.table as string;
    return nodeActions([
      opsButton(
        [
          { label: t("database.table.editStructure"), key: "structure" },
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
      { label: t("database.script.edit"), key: "load" },
      { label: t("database.script.detail"), key: "detail" },
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
    selectTable(database, match.table as string);
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
    selectTable(node.database as string, node.table as string);
    return;
  }
  if (node.kind === "script") {
    await loadScriptIntoEditor(node.script as SqlScript);
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

function selectTable(database: string, table: string) {
  selectedDatabase.value = database;
  selectedTable.value = table;
  dataPagination.page = 1;
  tableRows.value = [];
  tableColumns.value = [];
  primaryKeys.value = [];
  dataPagination.itemCount = 0;
  dataTotalExact.value = true;
  void loadTableData();
}

function resetTableView() {
  selectedTable.value = "";
  tableRows.value = [];
  tableColumns.value = [];
  primaryKeys.value = [];
  dataPagination.itemCount = 0;
  dataTotalExact.value = true;
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
  const requestId = ++tableDataRequestId;
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
      tableFilter.value,
      false
    );
    if (requestId !== tableDataRequestId) return;
    tableColumns.value = result.columns;
    tableRows.value = result.rows;
    primaryKeys.value = result.primary_keys;
    dataPagination.itemCount = result.total;
    dataTotalExact.value = result.total_exact;
  } catch (error) {
    if (requestId !== tableDataRequestId) return;
    showError(message, error);
  } finally {
    if (requestId === tableDataRequestId) loadingData.value = false;
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
  openCreateTableDesigner(selectedDatabase.value);
}

function handleSchemaOp(key: string, database: string) {
  if (key === "schema-create") createSchemaPrompt();
  else if (key === "table-create") {
    selectedDatabase.value = database;
    createTablePrompt();
  } else if (key === "schema-drop") dropSchemaByName(database);
}

function handleTableOp(key: string, database: string, table: string) {
  if (key === "structure") void openEditTableDesigner(database, table);
  else if (key === "import") openImportForTable(database, table);
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
  if (key === "load") void loadScriptIntoEditor(script);
  else if (key === "detail") void showScriptDetail(script);
  else if (key === "run") void executeScript(script);
  else if (key === "delete") confirmDeleteScript(script);
}

function openCreateTableDesigner(database: string) {
  selectedDatabase.value = database;
  Object.assign(tableDesigner, {
    show: true,
    mode: "create",
    database,
    name: "",
    originalName: "",
    saving: false
  });
  tableDesigner.columns = [
    columnDraft({ name: "id", type: "INT", nullable: false, primary_key: true, autoincrement: true, default: "", comment: "" }, false),
    columnDraft({ name: "name", type: "VARCHAR(255)", nullable: true, primary_key: false, autoincrement: false, default: "", comment: "" }, false)
  ];
  tableDesigner.indexes = [];
}

async function openEditTableDesigner(database: string, table: string) {
  selectedDatabase.value = database;
  try {
    const detail = await getTableStructure(props.connection.conn_id, database, table);
    Object.assign(tableDesigner, {
      show: true,
      mode: "edit",
      database,
      name: table,
      originalName: table,
      saving: false
    });
    tableDesigner.columns = detail.columns.map((column) => columnDraft(columnToDefinition(column), true));
    tableDesigner.indexes = detail.indexes.map((index) => indexDraft(indexToDefinition(index), true));
  } catch (error) {
    showError(message, error);
  }
}

function addDesignerColumn() {
  tableDesigner.columns.push(columnDraft({ name: "", type: "VARCHAR(255)", nullable: true, primary_key: false, autoincrement: false, default: "", comment: "" }, false));
}

function addDesignerIndex() {
  tableDesigner.indexes.push(indexDraft({ name: "", columns: [], unique: false }, false));
}

function toggleDesignerColumnDrop(column: TableColumnDraft) {
  if (column.existing) column.drop = !column.drop;
  else tableDesigner.columns = tableDesigner.columns.filter((item) => item.key !== column.key);
}

function toggleDesignerIndexDrop(index: TableIndexDraft) {
  if (index.existing) index.drop = !index.drop;
  else tableDesigner.indexes = tableDesigner.indexes.filter((item) => item.key !== index.key);
}

async function saveTableDesigner() {
  const name = tableDesigner.name.trim();
  if (!name || !activeDesignerColumns().length) return;
  tableDesigner.saving = true;
  try {
    if (tableDesigner.mode === "create") {
      await createTable(props.connection.conn_id, {
        database: tableDesigner.database,
        name,
        columns: activeDesignerColumns().map(draftToColumnDefinition),
        indexes: activeDesignerIndexes().map(draftToIndexDefinition)
      });
      selectedTable.value = name;
    } else {
      let targetTable = tableDesigner.originalName;
      if (name !== tableDesigner.originalName) {
        await renameTable(props.connection.conn_id, tableDesigner.originalName, { database: tableDesigner.database, new_name: name });
        targetTable = name;
      }
      const payload = buildAlterTablePayload();
      if ((payload.actions?.length || 0) > 0 || (payload.index_actions?.length || 0) > 0) {
        await alterTable(props.connection.conn_id, targetTable, payload);
      }
      selectedTable.value = targetTable;
    }
    tableDesigner.show = false;
    await reloadSchema(tableDesigner.database);
    await openSchemaTables(tableDesigner.database);
  } catch (error) {
    showError(message, error);
  } finally {
    tableDesigner.saving = false;
  }
}

function buildAlterTablePayload(): AlterTablePayload {
  const actions: AlterTablePayload["actions"] = [];
  const indexActions: AlterTablePayload["index_actions"] = [];
  for (const column of tableDesigner.columns) {
    if (column.existing && column.drop) {
      actions?.push({ action: "drop_column", name: column.original.name });
    } else if (!column.existing && !column.drop) {
      actions?.push({ action: "add_column", column: draftToColumnDefinition(column) });
    } else if (column.existing && !column.drop && columnChanged(column)) {
      if (column.name.trim() !== column.original.name) {
        actions?.push({ action: "rename_column", name: column.original.name, new_name: column.name.trim() });
      }
      if (columnDefinitionChanged(column)) {
        actions?.push({ action: "modify_column", column: draftToColumnDefinition(column) });
      }
    }
  }
  for (const index of tableDesigner.indexes) {
    if (index.existing && index.drop) {
      indexActions?.push({ action: "drop_index", name: index.original.name });
    } else if (!index.existing && !index.drop) {
      indexActions?.push({ action: "add_index", index: draftToIndexDefinition(index) });
    } else if (index.existing && !index.drop && indexChanged(index)) {
      indexActions?.push({ action: "drop_index", name: index.original.name });
      indexActions?.push({ action: "add_index", index: draftToIndexDefinition(index) });
    }
  }
  return { database: tableDesigner.database, actions, index_actions: indexActions };
}

function activeDesignerColumns() {
  return tableDesigner.columns.filter((column) => !column.drop && column.name.trim());
}

function activeDesignerIndexes() {
  return tableDesigner.indexes.filter((index) => !index.drop && index.name.trim() && splitIndexColumns(index.columns).length);
}

function columnDraft(column: ColumnDefinition, existing: boolean): TableColumnDraft {
  const parsedType = parseColumnType(column.type);
  return {
    key: crypto.randomUUID(),
    existing,
    original: { ...column },
    name: column.name,
    type: column.type,
    typeName: parsedType.typeName,
    typeLength: parsedType.typeLength,
    customType: parsedType.customType,
    typeSuffix: parsedType.typeSuffix,
    nullable: column.nullable,
    primary_key: column.primary_key,
    autoincrement: column.autoincrement,
    default: column.default || "",
    comment: column.comment || "",
    drop: false
  };
}

function indexDraft(index: IndexDefinition, existing: boolean): TableIndexDraft {
  return {
    key: crypto.randomUUID(),
    existing,
    original: { ...index, columns: [...index.columns] },
    name: index.name,
    columns: index.columns.join(", "),
    unique: index.unique,
    drop: false
  };
}

function columnToDefinition(column: ColumnItem): ColumnDefinition {
  return {
    name: column.name,
    type: column.type,
    nullable: column.nullable,
    primary_key: column.primary_key,
    autoincrement: column.autoincrement,
    default: column.default == null ? "" : String(column.default),
    comment: column.comment
  };
}

function indexToDefinition(index: TableIndexItem): IndexDefinition {
  return { name: index.name, columns: index.columns, unique: index.unique };
}

function draftToColumnDefinition(column: TableColumnDraft): ColumnDefinition {
  return {
    name: column.name.trim(),
    type: columnTypeValue(column),
    nullable: column.nullable,
    primary_key: column.primary_key,
    autoincrement: column.autoincrement,
    default: column.default.trim(),
    comment: column.comment.trim()
  };
}

function parseColumnType(type: string) {
  const cleaned = type.trim();
  const match = /^([A-Z]+)(?:\((\d+)\))?(\s+COLLATE\s+["`']?[A-Z0-9_-]+["`']?)?$/i.exec(cleaned);
  if (match && columnTypeOptions.some((option) => option.value === match[1].toUpperCase())) {
    const typeName = match[1].toUpperCase();
    return {
      typeName,
      typeLength: match[2] && typeAllowsLength(typeName) ? Number(match[2]) : defaultTypeLength(typeName),
      customType: "",
      typeSuffix: match[3] || ""
    };
  }
  return { typeName: CUSTOM_COLUMN_TYPE, typeLength: null, customType: cleaned || "VARCHAR(255)", typeSuffix: "" };
}

function syncColumnType(column: TableColumnDraft) {
  if (column.typeName !== CUSTOM_COLUMN_TYPE && typeAllowsLength(column.typeName) && !column.typeLength) {
    column.typeLength = defaultTypeLength(column.typeName);
  }
  if (column.typeName !== CUSTOM_COLUMN_TYPE && !typeAllowsLength(column.typeName)) {
    column.typeLength = null;
  }
  column.type = columnTypeValue(column);
}

function columnTypeValue(column: TableColumnDraft) {
  if (column.typeName === CUSTOM_COLUMN_TYPE) {
    return column.customType.trim() || "VARCHAR(255)";
  }
  const typeName = column.typeName || "VARCHAR";
  if (typeAllowsLength(typeName) && column.typeLength) {
    return `${typeName}(${column.typeLength})${typeAllowsCollation(typeName) ? column.typeSuffix : ""}`;
  }
  return `${typeName}${typeAllowsCollation(typeName) ? column.typeSuffix : ""}`;
}

function typeAllowsLength(typeName: string) {
  return LENGTH_COLUMN_TYPES.has(typeName);
}

function defaultTypeLength(typeName: string) {
  if (typeName === "CHAR") return 1;
  if (typeName === "DECIMAL" || typeName === "NUMERIC") return 10;
  if (typeName === "VARCHAR") return 255;
  return null;
}

function typeAllowsCollation(typeName: string) {
  return COLLATION_COLUMN_TYPES.has(typeName);
}

function draftToIndexDefinition(index: TableIndexDraft): IndexDefinition {
  return { name: index.name.trim(), columns: splitIndexColumns(index.columns), unique: index.unique };
}

function splitIndexColumns(value: string) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function columnChanged(column: TableColumnDraft) {
  return JSON.stringify(draftToColumnDefinition(column)) !== JSON.stringify(column.original);
}

function columnDefinitionChanged(column: TableColumnDraft) {
  const current = draftToColumnDefinition(column);
  return (
    current.type !== column.original.type ||
    current.nullable !== column.original.nullable ||
    current.primary_key !== column.original.primary_key ||
    current.autoincrement !== column.original.autoincrement ||
    (current.default || "") !== (column.original.default || "") ||
    (current.comment || "") !== (column.original.comment || "")
  );
}

function indexChanged(index: TableIndexDraft) {
  return JSON.stringify(draftToIndexDefinition(index)) !== JSON.stringify(index.original);
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
          { name: "name", type: "VARCHAR(255)", nullable: true, primary_key: false, autoincrement: false }
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

async function loadScriptIntoEditor(script: SqlScript) {
  try {
    const detail = await getSqlScript(script.id);
    currentScript.value = detail;
    selectedDatabase.value = detail.database || selectedDatabase.value;
    sql.value = detail.content;
    activeTab.value = "sql";
  } catch (error) {
    showError(message, error);
  }
}

async function showScriptDetail(script: SqlScript) {
  await loadScriptIntoEditor(script);
  scriptDetailModal.show = true;
}

async function executeScript(script: SqlScript) {
  try {
    const result = await runSqlScript(props.connection.conn_id, { script_id: script.id, database: script.database || selectedDatabase.value });
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
  scriptModal.mode = currentScript.value ? "update" : "create";
  scriptModal.id = currentScript.value?.id ?? null;
  scriptModal.name = currentScript.value?.name || "";
  scriptModal.description = currentScript.value?.description || "";
  scriptModal.is_shared = currentScript.value?.is_shared ?? false;
  scriptModal.content = sql.value;
  scriptModal.show = true;
}

function openCreateScript(database: string) {
  selectedDatabase.value = database;
  currentScript.value = null;
  scriptModal.mode = "create";
  scriptModal.id = null;
  scriptModal.name = "";
  scriptModal.description = "";
  scriptModal.is_shared = false;
  scriptModal.content = "SELECT 1;";
  scriptModal.show = true;
}

async function saveScript() {
  savingScript.value = true;
  try {
    const payload = {
      name: scriptModal.name || t("database.script.untitled"),
      content: scriptModal.content,
      connection_id: props.connection.id,
      database: selectedDatabase.value,
      description: scriptModal.description,
      is_shared: scriptModal.is_shared
    };
    const saved =
      scriptModal.mode === "update" && scriptModal.id
        ? await updateSqlScript(scriptModal.id, payload)
        : await createSqlScript(payload);
    currentScript.value = saved;
    selectedDatabase.value = saved.database || selectedDatabase.value;
    sql.value = saved.content;
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
