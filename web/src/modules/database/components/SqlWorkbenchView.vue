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
        <div v-if="serverInfo" class="database-server-info">
          <div class="database-server-info-row">
            <span class="database-server-info-label">{{ t("database.serverInfo.version") }}</span>
            <span class="database-server-info-value" :title="serverInfo.version">{{ serverInfo.version || "-" }}</span>
          </div>
          <div class="database-server-info-row">
            <span class="database-server-info-label">{{ t("database.serverInfo.loadData") }}</span>
            <n-tag size="tiny" :type="serverInfo.load_data_infile ? 'success' : 'default'" :bordered="false">
              {{ serverInfo.load_data_infile ? t("database.serverInfo.loadDataOn") : t("database.serverInfo.loadDataOff") }}
            </n-tag>
          </div>
        </div>
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
        <n-tabs
          v-if="workbenchTabs.length"
          v-model:value="activeTabKey"
          type="card"
          closable
          animated
          @close="closeWorkbenchTab"
          @update:value="activateWorkbenchTab"
        >
          <template #suffix>
            <n-dropdown trigger="click" placement="bottom-end" :options="newTabOptions" @select="handleNewTabSelect">
              <n-button class="database-tab-add" size="small" quaternary circle :title="t('database.tabs.new')" :aria-label="t('database.tabs.new')">
                <template #icon><n-icon :component="Add20Regular" /></template>
              </n-button>
            </n-dropdown>
          </template>

          <n-tab-pane v-for="tab in workbenchTabs" :key="tab.key" class="database-tab-pane" :name="tab.key" display-directive="if">
            <template #tab>
              <span class="database-tab-title" :title="tab.title">
                <span>{{ tab.title }}</span>
                <n-button
                  v-if="tab.type === 'sql-script' && tab.script"
                  class="database-tab-info"
                  size="tiny"
                  text
                  :title="t('database.script.detail')"
                  @click.stop="showScriptDetail(tab.script)"
                >
                  i
                </n-button>
              </span>
            </template>

            <template v-if="tab.type === 'table-data'">
              <div class="database-sub-toolbar">
                <n-input v-model:value="tab.filter" class="filter-keyword" clearable :placeholder="t('database.table.search')" @keyup.enter="searchTableData(tab)" />
                <n-button @click="searchTableData(tab)">{{ t("common.search") }}</n-button>
                <permission-button :permission="DATABASE_OPERATE" @click="openAddRow(tab)">{{ t("database.row.add") }}</permission-button>
                <permission-button :permission="DATABASE_OPERATE" @click="openImport(tab)">{{ t("database.import.title") }}</permission-button>
                <n-dropdown :options="copyDataOptions" @select="(format) => copyTableData(format, tab)">
                  <n-button>{{ t("common.copy") }}</n-button>
                </n-dropdown>
                <n-dropdown :options="exportOptions" @select="(format) => exportTable(format, tab)">
                  <n-button>{{ t("database.export.title") }}</n-button>
                </n-dropdown>
              </div>
              <n-data-table
                class="page-data-table database-result-table"
                flex-height
                remote
                size="small"
                :columns="dataColumns(tab)"
                :data="tab.rows"
                :loading="tab.loading"
                :pagination="tab.pagination"
                :scroll-x="dataTableScrollX(tab)"
                @unstable-column-resize="(_, limitedWidth, column) => handleDataColumnResize(limitedWidth, column, tab)"
                @update:sorter="(sorter) => handleDataSorter(sorter, tab)"
                @update:page="(page) => handleDataPage(page, tab)"
                @update:page-size="(pageSize) => handleDataPageSize(pageSize, tab)"
              />
            </template>

            <template v-else-if="tab.type === 'sql-script'">
              <div class="database-sub-toolbar">
                <n-tag class="database-active-schema" size="small" :bordered="false" type="primary">
                  <template #icon><n-icon :component="Database20Regular" /></template>
                  {{ tab.database || t("database.allSchemas") }}
                </n-tag>
                <permission-button :permission="DATABASE_OPERATE" type="primary" :loading="tab.executing" @click="executeSql(tab)">{{ t("database.sql.execute") }}</permission-button>
                <n-button @click="openResultExport(tab)">{{ t("database.export.result") }}</n-button>
                <permission-button v-if="tab.script" :permission="SQL_SCRIPT_UPDATE" @click="openRenameScript(tab.script)">{{ t("database.script.rename") }}</permission-button>
                <permission-button :permission="scriptSavePermission(tab)" @click="openSaveScript(tab)">{{ scriptSaveText(tab) }}</permission-button>
              </div>
              <monaco-editor v-model="tab.sql" class="database-sql-editor" :suggestions="suggestions" />
              <div class="database-result-bar">
                <span class="database-result-title">{{ t("database.sql.resultTitle") }}</span>
                <n-button
                  quaternary
                  size="small"
                  :title="tab.resultCollapsed ? t('database.sql.showResult') : t('database.sql.hideResult')"
                  @click="tab.resultCollapsed = !tab.resultCollapsed"
                >
                  <template #icon><n-icon :component="tab.resultCollapsed ? ChevronUp20Regular : ChevronDown20Regular" /></template>
                  {{ tab.resultCollapsed ? t("database.sql.showResult") : t("database.sql.hideResult") }}
                </n-button>
              </div>
              <n-data-table
                v-show="!tab.resultCollapsed"
                class="page-data-table database-query-table"
                flex-height
                size="small"
                :columns="queryColumns(tab)"
                :data="queryRows(tab)"
                :loading="tab.executing"
                :scroll-x="queryTableScrollX(tab)"
                @unstable-column-resize="(_, limitedWidth, column) => handleQueryColumnResize(limitedWidth, column, tab)"
              />
            </template>

            <template v-else>
              <div class="table-designer table-designer-tab">
                <n-form class="form-stack inline-form" label-placement="left" label-width="auto">
                  <n-form-item :label="t('database.table.name')">
                    <n-input v-model:value="tab.name" />
                  </n-form-item>
                </n-form>
                <section class="table-designer-section">
                  <div class="table-designer-section-head">
                    <strong>{{ t("database.table.columns") }}</strong>
                    <n-button size="small" @click="addDesignerColumn(tab)">{{ t("database.table.addColumn") }}</n-button>
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
                    <template v-for="column in tab.columns" :key="column.key">
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
                      <n-button size="tiny" quaternary :type="column.drop ? 'default' : 'error'" @click="toggleDesignerColumnDrop(tab, column)">
                        {{ column.drop ? t("database.table.restore") : t("common.delete") }}
                      </n-button>
                    </template>
                  </div>
                </section>
                <section class="table-designer-section">
                  <div class="table-designer-section-head">
                    <strong>{{ t("database.table.indexes") }}</strong>
                    <n-button size="small" @click="addDesignerIndex(tab)">{{ t("database.table.addIndex") }}</n-button>
                  </div>
                  <div class="table-designer-grid table-designer-indexes">
                    <span>{{ t("field.name") }}</span>
                    <span>{{ t("database.table.indexColumns") }}</span>
                    <span>{{ t("database.table.unique") }}</span>
                    <span>{{ t("common.actions") }}</span>
                    <template v-for="index in tab.indexes" :key="index.key">
                      <n-input v-model:value="index.name" size="small" :disabled="index.existing || index.drop" :class="{ 'database-dropped-row': index.drop }" />
                      <n-input v-model:value="index.columns" size="small" :disabled="index.drop" :placeholder="t('database.table.indexColumnsPlaceholder')" />
                      <n-checkbox v-model:checked="index.unique" :disabled="index.drop" />
                      <n-button size="tiny" quaternary :type="index.drop ? 'default' : 'error'" @click="toggleDesignerIndexDrop(tab, index)">
                        {{ index.drop ? t("database.table.restore") : t("common.delete") }}
                      </n-button>
                    </template>
                  </div>
                </section>
                <div class="form-actions table-designer-actions">
                  <n-button @click="closeWorkbenchTab(tab.key)">{{ t("common.cancel") }}</n-button>
                  <n-button type="primary" :loading="tab.saving" @click="saveTableDesigner(tab)">{{ t("common.save") }}</n-button>
                </div>
              </div>
            </template>
          </n-tab-pane>
        </n-tabs>

        <n-empty v-else class="database-workbench-empty" :description="t('database.tabs.empty')">
          <template #extra>
            <n-dropdown trigger="click" placement="bottom" :options="newTabOptions" @select="handleNewTabSelect">
              <n-button type="primary">
                <template #icon><n-icon :component="Add20Regular" /></template>
                {{ t("database.tabs.new") }}
              </n-button>
            </n-dropdown>
          </template>
        </n-empty>
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
      <div v-if="scriptDetailModal.script" class="database-detail-list">
        <div><span>{{ t("database.script.id") }}</span><strong>{{ scriptDetailModal.script.id }}</strong></div>
        <div><span>{{ t("database.script.statementCount") }}</span><strong>{{ scriptDetailModal.script.statement_count }}</strong></div>
        <div><span>{{ t("field.createdAt") }}</span><strong>{{ formatDateTime(scriptDetailModal.script.created_at) }}</strong></div>
        <div><span>{{ t("field.updatedAt") }}</span><strong>{{ formatDateTime(scriptDetailModal.script.updated_at) }}</strong></div>
      </div>
    </n-modal>

    <n-modal v-model:show="scriptRenameModal.show" preset="card" class="modal-card" :title="t('database.script.rename')">
      <n-form class="form-stack inline-form" label-placement="left" label-width="auto" @keyup.enter="renameScript">
        <n-form-item :label="t('field.name')">
          <n-input v-model:value="scriptRenameModal.name" />
        </n-form-item>
      </n-form>
      <template #action>
        <div class="form-actions modal-fixed-actions">
          <n-button @click="scriptRenameModal.show = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" :loading="scriptRenameModal.saving" @click="renameScript">{{ t("common.save") }}</n-button>
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
import { computed, h, onBeforeUnmount, onMounted, reactive, ref, watch, type Component, type VNode } from "vue";
import {
  Add20Regular,
  ArrowClockwise20Regular,
  ArrowLeft20Regular,
  ChevronDown20Regular,
  ChevronUp20Regular,
  Database20Regular,
  Delete20Regular,
  DocumentText20Regular,
  Edit20Regular,
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
import { copyText } from "../../../utils/clipboard";
import { showError } from "../../../utils/message";
import { sumColumnWidths, updateColumnWidth, withResizableColumns } from "../../../utils/table";
import {
  createRow,
  createSchema,
  createSqlScript,
  createTable,
  deleteRow,
  deleteSqlScript,
  dropSchema,
  dropTable,
  getDataJobUnseenCount,
  getDatabaseServerInfo,
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
  type DatabaseServerInfo,
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
const SIDEBAR_DEFAULT_WIDTH = 280;
const SIDEBAR_MIN_WIDTH = 220;
const SIDEBAR_MAX_WIDTH = 560;
const SIDEBAR_MIN_MAIN_WIDTH = 520;
const SIDEBAR_WIDTH_STORAGE_KEY = "metrix.databaseWorkbench.sidebarWidth";
const schemas = ref<{ name: string }[]>([]);
const serverInfo = ref<DatabaseServerInfo | null>(null);
const tables = ref<TableItem[]>([]);
const treeData = ref<TreeOption[]>([]);
const expandedKeys = ref<string[]>([]);
const selectedKeys = ref<string[]>([]);
const selectedDatabase = ref(props.connection.default_database || "");
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
  tabKey: "",
  format: "xlsx" as DataFormat,
  statements: [] as string[],
  selected: [] as number[]
});
const rowModal = reactive({
  show: false,
  mode: "add" as "add" | "edit",
  tabKey: "",
  json: "{}",
  original: null as Record<string, unknown> | null
});
const scriptModal = reactive({
  show: false,
  mode: "create" as "create" | "update",
  tabKey: "",
  id: null as number | null,
  name: "",
  description: "",
  is_shared: false,
  content: ""
});
const scriptDetailModal = reactive({
  show: false,
  script: null as SqlScript | null
});
const scriptRenameModal = reactive({
  show: false,
  id: null as number | null,
  name: "",
  saving: false
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
interface DataPagination {
  page: number;
  pageSize: number;
  itemCount: number;
  pageSizes: number[];
  showSizePicker: boolean;
  prefix: (payload: { itemCount: number | undefined }) => string;
}
interface TableDataTab {
  type: "table-data";
  key: string;
  title: string;
  database: string;
  table: string;
  filter: string;
  columns: ColumnItem[];
  rows: Record<string, unknown>[];
  primaryKeys: string[];
  totalExact: boolean;
  columnWidths: Record<string, number>;
  sort: { columnKey: string | null; order: "ascend" | "descend" | false };
  loading: boolean;
  requestId: number;
  pagination: DataPagination;
}
interface SqlEditorTab {
  type: "sql-script";
  key: string;
  title: string;
  database: string;
  script: SqlScript | null;
  sql: string;
  queryResult: QueryResult | null;
  resultColumnWidths: Record<string, number>;
  executing: boolean;
  resultCollapsed: boolean;
}
interface TableDesignerTab {
  type: "table-designer";
  key: string;
  title: string;
  mode: "create" | "edit";
  database: string;
  name: string;
  originalName: string;
  columns: TableColumnDraft[];
  indexes: TableIndexDraft[];
  saving: boolean;
}
type WorkbenchTab = TableDataTab | SqlEditorTab | TableDesignerTab;
type TableDataSort = TableDataTab["sort"];
type CopyDataFormat = "tsv" | "csv" | "sql";
interface TableDataLoadOptions {
  page?: number;
  pageSize?: number;
  sort?: TableDataSort;
}
const workbenchTabs = ref<WorkbenchTab[]>([]);
const activeTabKey = ref("");
const temporaryScriptCounter = ref(0);
const exportOptions = [
  { label: "CSV", key: "csv" },
  { label: "XLSX", key: "xlsx" },
  { label: "SQLite", key: "sqlite" },
  { label: "SQL", key: "sql" }
];
const copyDataOptions: DropdownOption[] = [
  { label: "EXCEL", key: "tsv" },
  { label: "CSV", key: "csv" },
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
const scriptModalTitle = computed(() => (scriptModal.mode === "update" ? t("database.script.update") : t("database.script.save")));
const newTabOptions = computed<DropdownOption[]>(() => [
  { label: t("database.table.create"), key: "table-create", disabled: !canOperate.value },
  { label: t("database.script.temporary"), key: "temp-sql" }
]);
const activeWorkbenchTab = computed(() => workbenchTabs.value.find((tab) => tab.key === activeTabKey.value) || null);
const activeTableTab = computed(() => (activeWorkbenchTab.value?.type === "table-data" ? activeWorkbenchTab.value : null));
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
  ...(activeTableTab.value?.columns || []).map((item) => item.name)
]);

const PREFIX_ICONS: Record<string, Component> = {
  schema: Database20Regular,
  tablesCat: Folder20Regular,
  scriptsCat: Folder20Regular,
  table: Table20Regular,
  script: DocumentText20Regular
};
const TABLE_MIN_SCROLL_X = 960;
const TABLE_DYNAMIC_COLUMN_WIDTH = 180;
const TABLE_DATA_ACTION_WIDTH = 150;

function scriptSavePermission(tab: SqlEditorTab) {
  return tab.script ? SQL_SCRIPT_UPDATE : SQL_SCRIPT_CREATE;
}

function scriptSaveText(tab: SqlEditorTab) {
  return tab.script ? t("database.script.update") : t("database.script.save");
}

function dataColumns(tab: TableDataTab): DataTableColumns<Record<string, unknown>> {
  return withResizableColumns([
    ...tab.columns.map((column) => ({
      title: column.name,
      key: column.name,
      width: columnWidth(tab.columnWidths, column.name),
      minWidth: 80,
      resizable: true,
      sorter: true,
      sortOrder: tab.sort.columnKey === column.name ? tab.sort.order : false,
      ellipsis: { tooltip: true },
      render: (row: Record<string, unknown>) => formatCell(row[column.name])
    })),
    ...(canOperate.value
      ? [
          {
            title: t("common.actions"),
            key: "actions",
            fixed: "right" as const,
            width: TABLE_DATA_ACTION_WIDTH,
            resizable: false,
            render: (row: Record<string, unknown>) =>
              h("div", { class: "table-action-group" }, [
                h(
                  NButton,
                  { size: "tiny", quaternary: true, circle: true, title: t("common.edit"), onClick: () => openEditRow(row, tab) },
                  { icon: () => h(NIcon, { component: Edit20Regular }) }
                ),
                h(
                  NButton,
                  { size: "tiny", quaternary: true, circle: true, type: "error", title: t("common.delete"), onClick: () => confirmDeleteRow(row, tab) },
                  { icon: () => h(NIcon, { component: Delete20Regular }) }
                )
              ])
          }
        ]
      : [])
  ]);
}

function queryColumns(tab: SqlEditorTab): DataTableColumns<Record<string, unknown>> {
  const columns = tab.queryResult?.columns || [];
  if (!columns.length && tab.queryResult?.statement_type === "write") {
    return withResizableColumns([
      {
        title: t("database.sql.affectedRows"),
        key: "affected_rows",
        width: columnWidth(tab.resultColumnWidths, "affected_rows"),
        minWidth: 120,
        render: () => tab.queryResult?.affected_rows ?? 0
      }
    ]);
  }
  return withResizableColumns(
    columns.map((column) => ({
      title: column,
      key: column,
      width: columnWidth(tab.resultColumnWidths, column),
      minWidth: 80,
      resizable: true,
      sorter: "default" as const,
      ellipsis: { tooltip: true },
      render: (row: Record<string, unknown>) => formatCell(row[column])
    }))
  );
}

function queryRows(tab: SqlEditorTab) {
  return tab.queryResult?.rows || [];
}

function dataTableScrollX(tab: TableDataTab) {
  return Math.max(TABLE_MIN_SCROLL_X, sumColumnWidths({ ...columnWidthSnapshot(tab.columnWidths, tab.columns.map((column) => column.name)), actions: TABLE_DATA_ACTION_WIDTH }));
}

function queryTableScrollX(tab: SqlEditorTab) {
  const keys = tab.queryResult?.columns.length ? tab.queryResult.columns : tab.queryResult?.statement_type === "write" ? ["affected_rows"] : [];
  if (!keys.length) return TABLE_MIN_SCROLL_X;
  return Math.max(TABLE_MIN_SCROLL_X, sumColumnWidths(columnWidthSnapshot(tab.resultColumnWidths, keys)));
}

function columnWidth(widths: Record<string, number>, key: string) {
  return widths[key] ?? TABLE_DYNAMIC_COLUMN_WIDTH;
}

function columnWidthSnapshot(widths: Record<string, number>, keys: string[]) {
  return Object.fromEntries(keys.map((key) => [key, columnWidth(widths, key)]));
}

function nextColumnWidths(widths: Record<string, number>, keys: string[]) {
  const next = { ...widths };
  for (const key of keys) {
    next[key] ??= TABLE_DYNAMIC_COLUMN_WIDTH;
  }
  for (const key of Object.keys(next)) {
    if (!keys.includes(key)) delete next[key];
  }
  return next;
}

function handleDataColumnResize(limitedWidth: number, column: { key?: string | number }, tab: TableDataTab) {
  updateColumnWidth(tab.columnWidths, column.key, columnWidthKeys(tab.columnWidths), limitedWidth);
}

function handleQueryColumnResize(limitedWidth: number, column: { key?: string | number }, tab: SqlEditorTab) {
  updateColumnWidth(tab.resultColumnWidths, column.key, columnWidthKeys(tab.resultColumnWidths), limitedWidth);
}

function columnWidthKeys(widths: Record<string, number>) {
  return Object.fromEntries(Object.keys(widths).map((key) => [key, key]));
}

async function loadServerInfo() {
  try {
    serverInfo.value = await getDatabaseServerInfo(props.connection.conn_id);
  } catch {
    serverInfo.value = null;
  }
}

onMounted(async () => {
  sidebarWidth.value = clampSidebarWidth(sidebarWidth.value);
  window.addEventListener("resize", clampSidebarWidthToViewport);
  await refreshMetadata();
  await loadDownloadCount();
  void loadServerInfo();
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

function createTableDataTab(database: string, table: string): TableDataTab {
  const tab: TableDataTab = {
    type: "table-data",
    key: tableTabKey(database, table),
    title: table,
    database,
    table,
    filter: "",
    columns: [],
    rows: [],
    primaryKeys: [],
    totalExact: true,
    columnWidths: {},
    sort: { columnKey: null, order: false },
    loading: false,
    requestId: 0,
    pagination: {} as DataPagination
  };
  tab.pagination = createDataPagination(tab);
  return tab;
}

function createDataPagination(tab: TableDataTab): DataPagination {
  return {
    page: 1,
    pageSize: 50,
    itemCount: 0,
    pageSizes: [50, 100, 200, 500],
    showSizePicker: true,
    prefix: ({ itemCount }: { itemCount: number | undefined }) =>
      tab.totalExact ? t("common.total", { count: itemCount ?? 0 }) : t("database.table.totalEstimate", { count: itemCount ?? 0 })
  };
}

function createSqlTab(database: string, script: SqlScript | null, sqlText: string): SqlEditorTab {
  return {
    type: "sql-script",
    key: script ? sqlTabKey(script.id) : temporarySqlTabKey(++temporaryScriptCounter.value),
    title: script?.name || temporarySqlTitle(temporaryScriptCounter.value),
    database,
    script,
    sql: sqlText,
    queryResult: null,
    resultColumnWidths: {},
    executing: false,
    resultCollapsed: false
  };
}

function createDesignerTab(mode: "create" | "edit", database: string, table = ""): TableDesignerTab {
  return {
    type: "table-designer",
    key: mode === "create" ? designerCreateTabKey(database) : designerEditTabKey(database, table),
    title: mode === "create" ? t("database.table.createTab") : t("database.table.editTab", { name: table }),
    mode,
    database,
    name: table,
    originalName: table,
    columns: [],
    indexes: [],
    saving: false
  };
}

function tableTabKey(database: string, table: string) {
  return `data:${database}:${table}`;
}

function sqlTabKey(id: number) {
  return `script:${id}`;
}

function temporarySqlTabKey(counter: number) {
  return `temp:${counter}`;
}

function designerCreateTabKey(database: string) {
  return `designer:create:${database}`;
}

function designerEditTabKey(database: string, table: string) {
  return `designer:edit:${database}:${table}`;
}

function temporarySqlTitle(counter: number) {
  return counter === 1 ? t("database.script.temporary") : t("database.script.temporaryNamed", { index: counter });
}

function activateWorkbenchTab(key: string | number) {
  activeTabKey.value = String(key);
  const tab = activeWorkbenchTab.value;
  if (!tab) return;
  selectedDatabase.value = tab.database;
  if (tab.type === "table-data") {
    selectedKeys.value = [tableNodeKey(tab.database, tab.table)];
  } else if (tab.type === "sql-script" && tab.script) {
    selectedKeys.value = [scriptNodeKey(tab.database, tab.script.id)];
  }
  updateTablesForDb(tab.database);
}

function upsertWorkbenchTab<T extends WorkbenchTab>(tab: T) {
  const existing = workbenchTabs.value.find((item) => item.key === tab.key);
  if (existing) {
    activeTabKey.value = existing.key;
    activateWorkbenchTab(existing.key);
    return existing as T;
  }
  workbenchTabs.value.push(tab);
  activeTabKey.value = tab.key;
  activateWorkbenchTab(tab.key);
  return tab;
}

function findTableTab(key: string) {
  return workbenchTabs.value.find((tab): tab is TableDataTab => tab.key === key && tab.type === "table-data") || null;
}

function patchTableTab(key: string, patch: Partial<TableDataTab>) {
  const index = workbenchTabs.value.findIndex((tab) => tab.key === key && tab.type === "table-data");
  if (index < 0) return null;
  const current = workbenchTabs.value[index] as TableDataTab;
  const updated = { ...current, ...patch };
  workbenchTabs.value.splice(index, 1, updated);
  return updated;
}

function closeWorkbenchTab(key: string | number) {
  const tabKey = String(key);
  const index = workbenchTabs.value.findIndex((tab) => tab.key === tabKey);
  if (index < 0) return;
  workbenchTabs.value.splice(index, 1);
  if (activeTabKey.value !== tabKey) return;
  const next = workbenchTabs.value[Math.max(0, index - 1)] || workbenchTabs.value[index] || null;
  activeTabKey.value = next?.key || "";
  if (next) activateWorkbenchTab(next.key);
}

function handleNewTabSelect(key: string | number) {
  if (key === "table-create") {
    const database = preferredDatabase();
    if (!database) {
      message.warning(t("database.tabs.noDatabase"));
      return;
    }
    openCreateTableDesigner(database);
  } else if (key === "temp-sql") {
    startTemporaryScript();
  }
}

function preferredDatabase() {
  return selectedDatabase.value || props.connection.default_database || schemas.value[0]?.name || "";
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
      { label: t("database.script.detail"), key: "detail" }
    ];
    if (authStore.has(SQL_SCRIPT_UPDATE)) options.push({ label: t("database.script.rename"), key: "rename" });
    if (canOperate.value) options.push({ label: t("database.script.run"), key: "run" });
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
    if (initial) {
      const cat = findCategory(initial, "tablesCat");
      if (cat) {
        cat.children = await loadTableNodes(initial);
        updateTablesForDb(initial);
        expandedKeys.value = [schemaKey(initial), tablesCatKey(initial)];
      }
    } else {
      tables.value = [];
    }
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
  const match = cat.children.find((child) => child.table === activeTableTab.value?.table);
  selectedKeys.value = match ? [String(match.key)] : [schemaKey(database)];
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
    selectedKeys.value = [String(node.key)];
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
  const tab = upsertWorkbenchTab(createTableDataTab(database, table));
  void loadTableData(tab, { page: 1 });
}

function resetTableView() {
  selectedKeys.value = [];
}

function handleDataSorter(sorter: DataTableSortState | DataTableSortState[] | null, tab: TableDataTab) {
  const state = Array.isArray(sorter) ? sorter[0] : sorter;
  const sort: TableDataSort = { columnKey: null, order: false };
  if (!state || !state.order) {
    sort.columnKey = null;
    sort.order = false;
  } else {
    sort.columnKey = String(state.columnKey);
    sort.order = state.order;
  }
  void loadTableData(tab, { page: 1, sort });
}

function searchTableData(tab: TableDataTab) {
  void loadTableData(tab, { page: 1 });
}

async function loadTableData(tab: TableDataTab, options: TableDataLoadOptions = {}) {
  const current = findTableTab(tab.key);
  if (!current) return;
  const requestId = current.requestId + 1;
  const pagination = {
    ...current.pagination,
    page: options.page ?? current.pagination.page,
    pageSize: options.pageSize ?? current.pagination.pageSize
  };
  const sort = options.sort ?? current.sort;
  const loadingTab = patchTableTab(current.key, { loading: true, requestId, pagination, sort });
  if (!loadingTab) return;
  try {
    const result = await getTableData(
      props.connection.conn_id,
      loadingTab.database || "",
      loadingTab.table,
      loadingTab.pagination.page,
      loadingTab.pagination.pageSize,
      loadingTab.sort.columnKey || "",
      loadingTab.sort.order === "descend",
      loadingTab.filter,
      true
    );
    const latest = findTableTab(loadingTab.key);
    if (!latest || requestId !== latest.requestId) return;
    patchTableTab(latest.key, {
      columns: result.columns,
      rows: result.rows,
      primaryKeys: result.primary_keys,
      totalExact: result.total_exact,
      columnWidths: nextColumnWidths(latest.columnWidths, result.columns.map((column) => column.name)),
      loading: false,
      pagination: {
        ...latest.pagination,
        page: result.page,
        pageSize: result.page_size,
        itemCount: result.total
      }
    });
  } catch (error) {
    const latest = findTableTab(loadingTab.key);
    if (!latest || requestId !== latest.requestId) return;
    patchTableTab(latest.key, { loading: false });
    showError(message, error);
  }
}

async function executeSql(tab: SqlEditorTab) {
  tab.executing = true;
  try {
    const result = await queryDatabase(props.connection.conn_id, { sql: tab.sql, database: tab.database || "" });
    tab.queryResult = result;
    tab.resultColumnWidths = nextColumnWidths(tab.resultColumnWidths, result.columns.length ? result.columns : result.statement_type === "write" ? ["affected_rows"] : []);
    tab.resultCollapsed = false;
    message.success(t("database.sql.executed"));
  } catch (error) {
    showError(message, error);
  } finally {
    tab.executing = false;
  }
}

function openAddRow(tab: TableDataTab) {
  rowModal.mode = "add";
  rowModal.tabKey = tab.key;
  rowModal.original = null;
  rowModal.json = JSON.stringify(Object.fromEntries(tab.columns.map((column) => [column.name, null])), null, 2);
  rowModal.show = true;
}

function openEditRow(row: Record<string, unknown>, tab: TableDataTab) {
  rowModal.mode = "edit";
  rowModal.tabKey = tab.key;
  rowModal.original = row;
  rowModal.json = JSON.stringify(row, null, 2);
  rowModal.show = true;
}

async function saveRow() {
  const tab = workbenchTabs.value.find((item): item is TableDataTab => item.key === rowModal.tabKey && item.type === "table-data");
  if (!tab) return;
  savingRow.value = true;
  try {
    const values = JSON.parse(rowModal.json) as Record<string, unknown>;
    if (rowModal.mode === "add") {
      await createRow(props.connection.conn_id, { database: tab.database, table: tab.table, values });
    } else {
      await updateRow(props.connection.conn_id, {
        database: tab.database,
        table: tab.table,
        keys: rowKeys(rowModal.original || {}, tab),
        values
      });
    }
    rowModal.show = false;
    await loadTableData(tab);
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
    onPositiveClick: async () => {
      try {
        await onConfirm();
      } catch (error) {
        showError(message, error);
      }
    }
  });
}

function confirmDeleteRow(row: Record<string, unknown>, tab: TableDataTab) {
  confirmAction(t("database.row.deleteConfirm"), async () => {
    await deleteRow(props.connection.conn_id, { database: tab.database, table: tab.table, keys: rowKeys(row, tab) });
    await loadTableData(tab);
  });
}

function rowKeys(row: Record<string, unknown>, tab: TableDataTab) {
  const keys = tab.primaryKeys.length ? tab.primaryKeys : tab.columns.map((column) => column.name);
  return Object.fromEntries(keys.map((key) => [key, row[key]]));
}

async function exportTable(format: string | number, tab: TableDataTab) {
  try {
    const result = await submitExport(props.connection.conn_id, {
      format: format as DataFormat,
      database: tab.database,
      tables: [tab.table]
    });
    handleJobSubmitted(result.job_id);
  } catch (error) {
    showError(message, error);
  }
}

function openResultExport(tab: SqlEditorTab) {
  const statements = splitReadStatements(tab.sql);
  exportModal.tabKey = tab.key;
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
  const tab = workbenchTabs.value.find((item): item is SqlEditorTab => item.key === exportModal.tabKey && item.type === "sql-script");
  if (!tab) return;
  const picked = exportModal.selected
    .slice()
    .sort((a, b) => a - b)
    .map((index) => exportModal.statements[index])
    .filter(Boolean);
  if (!picked.length) return;
  try {
    const result = await submitExport(props.connection.conn_id, {
      format: exportModal.format,
      database: tab.database,
      queries: picked.map((statement, index) => ({ name: `result_${index + 1}`, sql: statement }))
    });
    exportModal.show = false;
    handleJobSubmitted(result.job_id);
  } catch (error) {
    showError(message, error);
  }
}

async function copyTableData(format: string | number, tab: TableDataTab) {
  try {
    const copyFormat = String(format) as CopyDataFormat;
    const text = copyFormat === "sql" ? tableDataToSql(tab) : tableDataToDelimited(tab, copyFormat === "csv" ? "," : "\t");
    await copyText(text);
    message.success(t("common.copied"));
  } catch (error) {
    showError(message, error);
  }
}

function tableDataToDelimited(tab: TableDataTab, delimiter: "," | "\t") {
  const headers = tab.columns.map((column) => column.name);
  const escapeCell = delimiter === "," ? csvCell : tsvCell;
  const lines = [headers.map(escapeCell).join(delimiter)];
  for (const row of tab.rows) {
    lines.push(headers.map((column) => escapeCell(row[column])).join(delimiter));
  }
  return lines.join("\r\n");
}

function tableDataToSql(tab: TableDataTab) {
  const columns = tab.columns.map((column) => column.name);
  const tableName = tab.database ? `${quoteSqlIdentifier(tab.database)}.${quoteSqlIdentifier(tab.table)}` : quoteSqlIdentifier(tab.table);
  const columnSql = columns.map(quoteSqlIdentifier).join(", ");
  const lines = [`-- ${tab.table}`, `-- ${columns.join(", ")}`];
  for (const row of tab.rows) {
    const values = columns.map((column) => sqlLiteral(row[column])).join(", ");
    lines.push(`INSERT INTO ${tableName} (${columnSql}) VALUES (${values});`);
  }
  return lines.join("\r\n");
}

function csvCell(value: unknown) {
  const text = copyCellText(value);
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function tsvCell(value: unknown) {
  return copyCellText(value).replaceAll("\t", " ").replace(/\r?\n/g, " ");
}

function copyCellText(value: unknown) {
  if (value === null || value === undefined) return "";
  if (value instanceof Date) return value.toISOString();
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function quoteSqlIdentifier(value: string) {
  return `\`${value.replaceAll("`", "``")}\``;
}

function sqlLiteral(value: unknown) {
  if (value === null || value === undefined) return "NULL";
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : "NULL";
  if (typeof value === "boolean") return value ? "1" : "0";
  return `'${copyCellText(value).replaceAll("'", "''")}'`;
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
  const database = preferredDatabase();
  if (!database) {
    message.warning(t("database.tabs.noDatabase"));
    return;
  }
  openCreateTableDesigner(database);
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

function openImport(tab: TableDataTab) {
  importTarget.database = tab.database;
  importTarget.table = tab.table;
  showImport.value = true;
}

function openImportForTable(database: string, table: string) {
  importTarget.database = database;
  importTarget.table = table;
  showImport.value = true;
}

function handleScriptOp(key: string, script: SqlScript) {
  if (key === "load") void loadScriptIntoEditor(script);
  else if (key === "rename") openRenameScript(script);
  else if (key === "detail") void showScriptDetail(script);
  else if (key === "run") void executeScript(script);
  else if (key === "delete") confirmDeleteScript(script);
}

function openCreateTableDesigner(database: string) {
  selectedDatabase.value = database;
  const existing = workbenchTabs.value.find((tab): tab is TableDesignerTab => tab.key === designerCreateTabKey(database) && tab.type === "table-designer");
  if (existing) {
    upsertWorkbenchTab(existing);
    return;
  }
  const tab = createDesignerTab("create", database);
  tab.columns = [
    columnDraft({ name: "id", type: "INT", nullable: false, primary_key: true, autoincrement: true, default: "", comment: "" }, false),
    columnDraft({ name: "name", type: "VARCHAR(255)", nullable: true, primary_key: false, autoincrement: false, default: "", comment: "" }, false)
  ];
  tab.indexes = [];
  upsertWorkbenchTab(tab);
}

async function openEditTableDesigner(database: string, table: string) {
  selectedDatabase.value = database;
  const existing = workbenchTabs.value.find((tab): tab is TableDesignerTab => tab.key === designerEditTabKey(database, table) && tab.type === "table-designer");
  if (existing) {
    upsertWorkbenchTab(existing);
    return;
  }
  try {
    const detail = await getTableStructure(props.connection.conn_id, database, table);
    const tab = createDesignerTab("edit", database, table);
    tab.columns = detail.columns.map((column) => columnDraft(columnToDefinition(column), true));
    tab.indexes = detail.indexes.map((index) => indexDraft(indexToDefinition(index), true));
    upsertWorkbenchTab(tab);
  } catch (error) {
    showError(message, error);
  }
}

function addDesignerColumn(tab: TableDesignerTab) {
  tab.columns.push(columnDraft({ name: "", type: "VARCHAR(255)", nullable: true, primary_key: false, autoincrement: false, default: "", comment: "" }, false));
}

function addDesignerIndex(tab: TableDesignerTab) {
  tab.indexes.push(indexDraft({ name: "", columns: [], unique: false }, false));
}

function toggleDesignerColumnDrop(tab: TableDesignerTab, column: TableColumnDraft) {
  if (column.existing) column.drop = !column.drop;
  else tab.columns = tab.columns.filter((item) => item.key !== column.key);
}

function toggleDesignerIndexDrop(tab: TableDesignerTab, index: TableIndexDraft) {
  if (index.existing) index.drop = !index.drop;
  else tab.indexes = tab.indexes.filter((item) => item.key !== index.key);
}

async function saveTableDesigner(tab: TableDesignerTab) {
  const name = tab.name.trim();
  if (!name || !activeDesignerColumns(tab).length) return;
  tab.saving = true;
  try {
    if (tab.mode === "create") {
      await createTable(props.connection.conn_id, {
        database: tab.database,
        name,
        columns: activeDesignerColumns(tab).map(draftToColumnDefinition),
        indexes: activeDesignerIndexes(tab).map(draftToIndexDefinition)
      });
      tab.mode = "edit";
      tab.originalName = name;
      tab.name = name;
      tab.key = designerEditTabKey(tab.database, name);
      tab.title = t("database.table.editTab", { name });
      activeTabKey.value = tab.key;
    } else {
      let targetTable = tab.originalName;
      if (name !== tab.originalName) {
        await renameTable(props.connection.conn_id, tab.originalName, { database: tab.database, new_name: name });
        const tableTab = workbenchTabs.value.find((item): item is TableDataTab => item.key === tableTabKey(tab.database, tab.originalName) && item.type === "table-data");
        if (tableTab) {
          tableTab.key = tableTabKey(tab.database, name);
          tableTab.title = name;
          tableTab.table = name;
        }
        targetTable = name;
      }
      const payload = buildAlterTablePayload(tab);
      if ((payload.actions?.length || 0) > 0 || (payload.index_actions?.length || 0) > 0) {
        await alterTable(props.connection.conn_id, targetTable, payload);
      }
      tab.originalName = targetTable;
      tab.name = targetTable;
      tab.key = designerEditTabKey(tab.database, targetTable);
      tab.title = t("database.table.editTab", { name: targetTable });
      activeTabKey.value = tab.key;
    }
    await reloadSchema(tab.database);
    await openSchemaTables(tab.database);
    const tableTab = workbenchTabs.value.find((item): item is TableDataTab => item.key === tableTabKey(tab.database, name) && item.type === "table-data");
    if (tableTab) await loadTableData(tableTab);
    message.success(t("common.saved"));
  } catch (error) {
    showError(message, error);
  } finally {
    tab.saving = false;
  }
}

function buildAlterTablePayload(tab: TableDesignerTab): AlterTablePayload {
  const actions: AlterTablePayload["actions"] = [];
  const indexActions: AlterTablePayload["index_actions"] = [];
  for (const column of tab.columns) {
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
  for (const index of tab.indexes) {
    if (index.existing && index.drop) {
      indexActions?.push({ action: "drop_index", name: index.original.name });
    } else if (!index.existing && !index.drop) {
      indexActions?.push({ action: "add_index", index: draftToIndexDefinition(index) });
    } else if (index.existing && !index.drop && indexChanged(index)) {
      indexActions?.push({ action: "drop_index", name: index.original.name });
      indexActions?.push({ action: "add_index", index: draftToIndexDefinition(index) });
    }
  }
  return { database: tab.database, actions, index_actions: indexActions };
}

function activeDesignerColumns(tab: TableDesignerTab) {
  return tab.columns.filter((column) => !column.drop && column.name.trim());
}

function activeDesignerIndexes(tab: TableDesignerTab) {
  return tab.indexes.filter((index) => !index.drop && index.name.trim() && splitIndexColumns(index.columns).length);
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
      await refreshMetadata();
    } else {
      const database = preferredDatabase();
      if (!database) return;
      await createTable(props.connection.conn_id, {
        database,
        name,
        columns: [
          { name: "id", type: "INT", nullable: false, primary_key: true, autoincrement: true },
          { name: "name", type: "VARCHAR(255)", nullable: true, primary_key: false, autoincrement: false }
        ]
      });
      objectModal.show = false;
      await openSchemaTables(database);
      selectTable(database, name);
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
    closeWorkbenchTab(tableTabKey(database, table));
    closeWorkbenchTab(designerEditTabKey(database, table));
    await reloadSchema(database);
  });
}

function truncateTableByName(database: string, table: string) {
  confirmAction(
    t("database.table.truncateConfirm", { name: table }),
    async () => {
      await truncateTable(props.connection.conn_id, database, table);
      const tab = workbenchTabs.value.find((item): item is TableDataTab => item.key === tableTabKey(database, table) && item.type === "table-data");
      if (tab) await loadTableData(tab);
    },
    t("common.confirm")
  );
}

function dropSchemaByName(database: string) {
  confirmAction(t("database.schema.dropConfirm", { name: database }), async () => {
    await dropSchema(props.connection.conn_id, database);
    if (selectedDatabase.value === database) {
      selectedDatabase.value = "";
    }
    workbenchTabs.value = workbenchTabs.value.filter((tab) => tab.database !== database);
    activeTabKey.value = workbenchTabs.value[0]?.key || "";
    await refreshMetadata();
  });
}

async function loadScriptIntoEditor(script: SqlScript) {
  try {
    const detail = await getSqlScript(script.id);
    selectedDatabase.value = detail.database || selectedDatabase.value;
    const existing = workbenchTabs.value.find((tab): tab is SqlEditorTab => tab.key === sqlTabKey(detail.id) && tab.type === "sql-script");
    if (existing) {
      existing.title = detail.name;
      existing.database = detail.database || existing.database;
      existing.script = detail;
      existing.sql = detail.content;
      upsertWorkbenchTab(existing);
    } else {
      upsertWorkbenchTab(createSqlTab(detail.database || selectedDatabase.value, detail, detail.content));
    }
  } catch (error) {
    showError(message, error);
  }
}

function startTemporaryScript() {
  scriptDetailModal.show = false;
  selectedKeys.value = [];
  upsertWorkbenchTab(createSqlTab(preferredDatabase(), null, "SELECT 1;"));
}

async function showScriptDetail(script: SqlScript) {
  try {
    scriptDetailModal.script = await getSqlScript(script.id);
    scriptDetailModal.show = true;
  } catch (error) {
    showError(message, error);
  }
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
    closeWorkbenchTab(sqlTabKey(script.id));
    await reloadScripts();
  });
}

function openRenameScript(script: SqlScript) {
  scriptRenameModal.id = script.id;
  scriptRenameModal.name = script.name;
  scriptRenameModal.saving = false;
  scriptRenameModal.show = true;
}

async function renameScript() {
  const scriptId = scriptRenameModal.id;
  const name = scriptRenameModal.name.trim();
  if (!scriptId || !name) return;
  scriptRenameModal.saving = true;
  try {
    const detail = await getSqlScript(scriptId);
    const saved = await updateSqlScript(scriptId, {
      name,
      content: detail.content,
      connection_id: detail.connection_id,
      database: detail.database,
      description: detail.description,
      is_shared: detail.is_shared
    });
    const tab = workbenchTabs.value.find((item): item is SqlEditorTab => item.key === sqlTabKey(scriptId) && item.type === "sql-script");
    if (tab) {
      tab.title = saved.name;
      tab.database = saved.database;
      tab.script = saved;
    }
    if (scriptDetailModal.script?.id === scriptId) {
      scriptDetailModal.script = saved;
    }
    scriptRenameModal.show = false;
    await reloadScripts();
  } catch (error) {
    showError(message, error);
  } finally {
    scriptRenameModal.saving = false;
  }
}

function openSaveScript(tab: SqlEditorTab) {
  scriptModal.mode = tab.script ? "update" : "create";
  scriptModal.tabKey = tab.key;
  scriptModal.id = tab.script?.id ?? null;
  scriptModal.name = tab.script?.name || "";
  scriptModal.description = tab.script?.description || "";
  scriptModal.is_shared = tab.script?.is_shared ?? false;
  scriptModal.content = tab.sql;
  scriptModal.show = true;
}

function openCreateScript(database: string) {
  selectedDatabase.value = database;
  scriptModal.mode = "create";
  scriptModal.tabKey = "";
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
    const tab = workbenchTabs.value.find((item): item is SqlEditorTab => item.key === scriptModal.tabKey && item.type === "sql-script");
    const payload = {
      name: scriptModal.name || t("database.script.untitled"),
      content: scriptModal.content,
      connection_id: props.connection.id,
      database: tab?.database || selectedDatabase.value,
      description: scriptModal.description,
      is_shared: scriptModal.is_shared
    };
    const saved =
      scriptModal.mode === "update" && scriptModal.id
        ? await updateSqlScript(scriptModal.id, payload)
        : await createSqlScript(payload);
    selectedDatabase.value = saved.database || selectedDatabase.value;
    const targetTab = tab || createSqlTab(saved.database, saved, saved.content);
    targetTab.key = sqlTabKey(saved.id);
    targetTab.title = saved.name;
    targetTab.database = saved.database;
    targetTab.script = saved;
    targetTab.sql = saved.content;
    upsertWorkbenchTab(targetTab);
    scriptModal.show = false;
    await reloadScripts();
  } catch (error) {
    showError(message, error);
  } finally {
    savingScript.value = false;
  }
}

function handleDataPage(page: number, tab: TableDataTab) {
  void loadTableData(tab, { page });
}

function handleDataPageSize(pageSize: number, tab: TableDataTab) {
  void loadTableData(tab, { page: 1, pageSize });
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
    pendingDownloadCount.value = (await getDataJobUnseenCount()).count;
  } catch {
    pendingDownloadCount.value = 0;
  }
}
</script>
