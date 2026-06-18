<template>
  <section class="work-card script-workbench">
    <div class="script-workbench-header">
      <div class="script-workbench-title">
        <n-button quaternary circle :aria-label="t('common.back')" :title="t('common.back')" @click="emit('close')">
          <template #icon><n-icon :component="ArrowLeft20Regular" /></template>
        </n-button>
        <span class="script-workbench-name" :title="project.name">{{ project.name }}</span>
        <n-tag size="small" :bordered="false">{{ project.language }}</n-tag>
      </div>
      <div class="script-workbench-actions">
        <permission-button :permission="SCRIPT_OPERATE" type="primary" :loading="running" @click="runScript">
          <template #icon><n-icon :component="Play20Regular" /></template>
          {{ t("script.run") }}
        </permission-button>
      </div>
    </div>

    <div class="script-workbench-body">
      <div class="script-sidebar">
        <div class="script-sidebar-toolbar">
          <span class="script-sidebar-title">{{ t("script.files") }}</span>
          <div class="script-sidebar-tools">
            <n-button size="tiny" quaternary circle :title="t('script.collapseAll')" @click="collapseAll">
              <template #icon><n-icon :component="ChevronUp20Regular" /></template>
            </n-button>
            <n-button size="tiny" quaternary circle :title="t('script.newFile')" @click="openNewEntry(false)">
              <template #icon><n-icon :component="DocumentAdd20Regular" /></template>
            </n-button>
            <n-button size="tiny" quaternary circle :title="t('script.newFolder')" @click="openNewEntry(true)">
              <template #icon><n-icon :component="FolderAdd20Regular" /></template>
            </n-button>
            <n-button size="tiny" quaternary circle :title="t('script.upload')" @click="triggerUpload">
              <template #icon><n-icon :component="ArrowUpload20Regular" /></template>
            </n-button>
            <n-button size="tiny" quaternary circle :title="t('common.refresh')" @click="reloadTreePreservingExpansion">
              <template #icon><n-icon :component="ArrowSync20Regular" /></template>
            </n-button>
          </div>
        </div>
        <n-tree
          block-line
          draggable
          :data="treeData"
          :on-load="loadTreeChildren"
          :selected-keys="selectedKeys"
          :expanded-keys="expandedKeys"
          :render-prefix="renderTreePrefix"
          :node-props="treeNodeProps"
          class="script-tree"
          @update:selected-keys="handleSelect"
          @update:expanded-keys="(keys) => (expandedKeys = keys as string[])"
          @drop="handleTreeDrop"
        />
        <input ref="uploadInputRef" type="file" class="script-upload-input" @change="handleUpload" />
        <n-dropdown
          trigger="manual"
          placement="bottom-start"
          :show="treeMenu.show"
          :options="treeMenuOptions"
          :x="treeMenu.x"
          :y="treeMenu.y"
          @select="handleTreeMenuSelect"
          @clickoutside="treeMenu.show = false"
        />
      </div>

      <div class="script-main">
        <n-tabs
          v-if="openFiles.length"
          :value="activePath"
          type="card"
          size="small"
          class="script-editor-tabs"
          @update:value="(value) => setActive(String(value))"
          @close="(name) => closeTab(String(name))"
        >
          <n-tab
            v-for="file in openFiles"
            :key="file.path"
            :name="file.path"
            :closable="true"
            :tab="() => renderEditorTab(file)"
          />
        </n-tabs>

        <div v-if="activeFile" class="script-editor-bar">
          <span class="script-editor-path">{{ activeFile.path }}</span>
          <div class="script-editor-actions">
            <n-radio-group v-if="isActiveMarkdown" v-model:value="viewMode" size="small">
              <n-radio-button value="source" :label="t('script.markdownSource')" />
              <n-radio-button value="preview" :label="t('script.markdownPreview')" />
            </n-radio-group>
            <permission-button
              v-if="!autoSaveEnabled"
              :permission="SCRIPT_OPERATE"
              size="small"
              type="primary"
              :loading="savingFile"
              @click="saveFile"
            >
              {{ t("common.save") }}
            </permission-button>
            <div class="script-auto-save">
              <span>{{ t("script.autoSave") }}</span>
              <n-switch v-model:value="autoSaveEnabled" size="small" @update:value="setAutoSave" />
            </div>
          </div>
        </div>

        <div class="script-editor-host">
          <!-- renderedMarkdown comes from markdown-it with html:false, so raw HTML is escaped (safe for v-html) -->
          <div v-if="showMarkdownPreview" class="script-markdown-preview" v-html="renderedMarkdown"></div>
          <code-editor v-else-if="activeFile" v-model="editorContent" :language="activeFile.language" />
          <div v-else class="script-editor-empty">{{ t("script.editorEmpty") }}</div>
        </div>

        <n-dropdown
          trigger="manual"
          placement="bottom-start"
          :show="tabMenu.show"
          :options="tabMenuOptions"
          :x="tabMenu.x"
          :y="tabMenu.y"
          @select="handleTabMenuSelect"
          @clickoutside="tabMenu.show = false"
        />

        <div class="script-panel" :class="{ 'script-panel-collapsed': panelCollapsed }">
          <n-tabs
            v-model:value="activeTab"
            type="line"
            size="small"
            :pane-wrapper-style="panelCollapsed ? 'display: none' : undefined"
            @update:value="handleTabChange"
          >
            <template #suffix>
              <div class="script-panel-suffix">
                <n-button quaternary circle size="tiny" :title="t('script.terminalAdd')" @click="addTerminal">
                  <template #icon><n-icon :component="Add20Regular" /></template>
                </n-button>
                <n-button
                  quaternary
                  circle
                  size="tiny"
                  :title="panelCollapsed ? t('script.panelExpand') : t('script.panelCollapse')"
                  @click="togglePanel"
                >
                  <template #icon><n-icon :component="panelCollapsed ? ChevronUp20Regular : ChevronDown20Regular" /></template>
                </n-button>
              </div>
            </template>
            <n-tab-pane name="log" :tab="t('script.tab.log')">
              <div class="script-log-bar">
                <n-tag v-if="currentRunId" size="small" :type="runStatusType(runStatus)">{{ runStatusLabel(runStatus) }}</n-tag>
                <span v-else class="script-log-empty">{{ t("script.selectRunHint") }}</span>
                <n-button
                  v-if="currentRunId && isActiveRun"
                  size="tiny"
                  quaternary
                  @click="cancelCurrentRun"
                >
                  {{ t("script.runCancel") }}
                </n-button>
              </div>
              <pre class="script-log-output">{{ runLog || t("script.emptyLog") }}</pre>
            </n-tab-pane>

            <n-tab-pane name="history" :tab="t('script.tab.history')">
              <n-data-table
                size="small"
                :columns="runColumns"
                :data="runs"
                :loading="loadingRuns"
                :row-key="(row) => row.run_id"
                :max-height="240"
              />
            </n-tab-pane>

            <n-tab-pane name="schedules" :tab="t('script.tab.schedules')">
              <div class="script-panel-toolbar">
                <permission-button :permission="SCRIPT_OPERATE" size="small" type="primary" @click="openScheduleCreate">
                  {{ t("script.schedule.add") }}
                </permission-button>
              </div>
              <n-data-table
                size="small"
                :columns="scheduleColumns"
                :data="schedules"
                :loading="loadingSchedules"
                :row-key="(row) => row.id"
                :max-height="220"
              />
            </n-tab-pane>

            <n-tab-pane name="environment" :tab="t('script.tab.environment')">
              <div class="script-panel-toolbar">
                <n-button size="small" :loading="loadingEnv" @click="loadEnvironment">{{ t("script.env.refresh") }}</n-button>
              </div>
              <div v-if="environment" class="script-env">
                <p v-if="!environment.available" class="script-env-warn">{{ environment.message || t("script.env.unavailable") }}</p>
                <template v-else>
                  <div class="script-env-row"><span>{{ t("script.env.image") }}</span><code>{{ environment.image }}</code></div>
                  <div class="script-env-row"><span>{{ t("script.env.os") }}</span><span>{{ environment.os_type }} / {{ environment.architecture }}</span></div>
                  <div class="script-env-row"><span>{{ t("script.env.version") }}</span><span>{{ environment.language_version || "-" }}</span></div>
                  <div class="script-env-row">
                    <span>{{ t("script.env.source") }}</span>
                    <span>{{ environment.pip_index_configured || environment.npm_registry_configured || environment.go_proxy_configured ? t("script.env.sourceConfigured") : t("script.env.sourcePublic") }}</span>
                  </div>
                  <pre class="script-env-packages">{{ environment.packages || "-" }}</pre>
                </template>
              </div>
              <div v-else class="script-log-empty">{{ t("script.env.hint") }}</div>
            </n-tab-pane>

            <n-tab-pane
              v-for="term in terminals"
              :key="term.id"
              :name="term.id"
              :tab="() => renderTerminalTab(term)"
              display-directive="show"
            >
              <script-terminal-panel :project="project" :active="activeTab === term.id" :auto-connect="!term.closable" />
            </n-tab-pane>
          </n-tabs>
        </div>
      </div>
    </div>

    <n-modal v-model:show="showNewEntry" preset="card" class="modal-card" :title="newEntryIsDir ? t('script.newFolder') : t('script.newFile')">
      <n-form class="inline-form" label-placement="left" label-width="auto">
        <n-form-item :label="t('script.entryName')">
          <n-input v-model:value="newEntryName" :placeholder="t('script.entryNamePlaceholder')" @keyup.enter="confirmNewEntry" />
        </n-form-item>
        <p class="script-modal-hint">{{ t("script.entryLocation", { dir: selectedDir }) }}</p>
      </n-form>
      <template #action>
        <div class="form-actions modal-fixed-actions">
          <n-button @click="showNewEntry = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" @click="confirmNewEntry">{{ t("common.create") }}</n-button>
        </div>
      </template>
    </n-modal>

    <n-modal v-model:show="renameModal.show" preset="card" class="modal-card" :title="t('script.rename')">
      <n-form class="inline-form" label-placement="left" label-width="auto">
        <n-form-item :label="t('script.entryName')">
          <n-input v-model:value="renameModal.value" :placeholder="t('script.entryNamePlaceholder')" @keyup.enter="confirmRename" />
        </n-form-item>
      </n-form>
      <template #action>
        <div class="form-actions modal-fixed-actions">
          <n-button @click="renameModal.show = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" :loading="renameModal.saving" @click="confirmRename">{{ t("common.save") }}</n-button>
        </div>
      </template>
    </n-modal>

    <n-modal v-model:show="showSchedule" preset="card" class="modal-card" :title="editingSchedule ? t('script.schedule.edit') : t('script.schedule.add')">
      <n-form class="inline-form" label-placement="left" label-width="auto">
        <n-form-item :label="t('script.schedule.name')">
          <n-input v-model:value="scheduleForm.name" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('script.schedule.type')">
          <n-radio-group v-model:value="scheduleForm.trigger_type">
            <n-radio-button value="interval" :label="t('script.schedule.triggerInterval')" />
            <n-radio-button value="cron" :label="t('script.schedule.triggerCron')" />
          </n-radio-group>
        </n-form-item>
        <n-form-item v-if="scheduleForm.trigger_type === 'interval'" :label="t('script.schedule.interval')">
          <n-input-number v-model:value="scheduleForm.interval_seconds" :min="10" :max="2592000" :show-button="false" />
        </n-form-item>
        <n-form-item v-else :label="t('script.schedule.cron')">
          <n-input v-model:value="scheduleForm.cron_expr" :placeholder="t('script.schedule.cronPlaceholder')" />
        </n-form-item>
        <n-form-item :label="t('script.schedule.enabled')">
          <n-switch v-model:value="scheduleForm.enabled" />
        </n-form-item>
      </n-form>
      <template #action>
        <div class="form-actions modal-fixed-actions">
          <n-button @click="showSchedule = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" :loading="savingSchedule" @click="saveSchedule">{{ t("common.save") }}</n-button>
        </div>
      </template>
    </n-modal>

  </section>
</template>

<script setup lang="ts">
import { computed, h, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch, type VNodeChild } from "vue";
import {
  Add20Regular,
  ArrowLeft20Regular,
  ArrowSync20Regular,
  ArrowUpload20Regular,
  ChevronDown20Regular,
  ChevronUp20Regular,
  Delete20Regular,
  Dismiss16Regular,
  DocumentAdd20Regular,
  Edit20Regular,
  FolderAdd20Regular,
  Play20Regular
} from "@vicons/fluent";
import {
  NButton,
  NDataTable,
  NDropdown,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NInputNumber,
  NModal,
  NRadioButton,
  NRadioGroup,
  NSwitch,
  NTab,
  NTabPane,
  NTabs,
  NTag,
  NTree,
  useDialog,
  useMessage
} from "naive-ui";
import type { DataTableColumns, DropdownOption, TreeDropInfo, TreeOption } from "naive-ui";
import MarkdownIt from "markdown-it";

import PermissionButton from "../../../components/PermissionButton.vue";
import { appKey } from "../../../config/app";
import { formatDateTime, t } from "../../../i18n";
import { messageText, showError } from "../../../utils/message";
import {
  cancelScriptRun,
  copyScriptEntries,
  createScriptSchedule,
  deleteScriptEntry,
  deleteScriptSchedule,
  getScriptEnvironment,
  getScriptRunLog,
  listScriptFiles,
  listScriptRuns,
  listScriptSchedules,
  mkdirScript,
  moveScriptEntries,
  readScriptFile,
  renameScriptEntry,
  submitScriptRun,
  updateScriptSchedule,
  uploadScriptFile,
  writeScriptFile,
  type ScriptEnvironmentInfo,
  type ScriptProject,
  type ScriptRun,
  type ScriptSchedule,
  type ScriptScheduleTrigger
} from "../api";
import CodeEditor from "../components/CodeEditor.vue";
import ScriptTerminalPanel from "../components/ScriptTerminalPanel.vue";
import { SCRIPT_OPERATE } from "../permissions";
import { getFileIcon, getFolderIcon } from "../utils/fileIcons";

const props = defineProps<{ project: ScriptProject }>();
const emit = defineEmits<{ close: [] }>();

const AUTO_SAVE_KEY = appKey("scriptWorkbench.autoSave");
const PANEL_COLLAPSED_KEY = appKey("scriptWorkbench.panelCollapsed");

const message = useMessage();
const dialog = useDialog();

const markdown = new MarkdownIt({ html: false, linkify: true, breaks: false });

const treeData = ref<TreeOption[]>([]);
const selectedKeys = ref<string[]>([]);
const expandedKeys = ref<string[]>([]);
const savingFile = ref(false);
// Auto save is on by default; only an explicit "0" (the user turned it off) keeps it off.
const autoSaveEnabled = ref(localStorage.getItem(AUTO_SAVE_KEY) !== "0");
const panelCollapsed = ref(localStorage.getItem(PANEL_COLLAPSED_KEY) === "1");
const viewMode = ref<"source" | "preview">("source");
const uploadInputRef = ref<HTMLInputElement | null>(null);

interface OpenFile {
  path: string;
  name: string;
  content: string;
  savedContent: string;
  language: string;
  truncated: boolean;
}
const openFiles = ref<OpenFile[]>([]);
const activePath = ref("");

// Clipboard remembers the copied source path; paste is only enabled when it has content.
const clipboard = ref<string | null>(null);

const treeMenu = reactive({ show: false, x: 0, y: 0, target: null as TreeOption | null });
const tabMenu = reactive({ show: false, x: 0, y: 0, path: "" });
const renameModal = reactive({ show: false, path: "", value: "", saving: false });

interface TerminalTab {
  id: string;
  index: number;
  closable: boolean;
}
// The default first terminal (terminal-1) and the log/history/schedule/environment tabs are
// not closable; only extra terminals added via the "+" button get a close button.
const terminals = ref<TerminalTab[]>([{ id: "terminal-1", index: 1, closable: false }]);
let terminalSeq = 1;

const activeTab = ref<string>("terminal-1");
const running = ref(false);
const currentRunId = ref("");
const runLog = ref("");
const runStatus = ref<string>("");
const runs = ref<ScriptRun[]>([]);
const loadingRuns = ref(false);
const schedules = ref<ScriptSchedule[]>([]);
const loadingSchedules = ref(false);
const environment = ref<ScriptEnvironmentInfo | null>(null);
const loadingEnv = ref(false);

const showNewEntry = ref(false);
const newEntryIsDir = ref(false);
const newEntryName = ref("");

const showSchedule = ref(false);
const editingSchedule = ref<ScriptSchedule | null>(null);
const savingSchedule = ref(false);
const scheduleForm = reactive<{ name: string; trigger_type: ScriptScheduleTrigger; interval_seconds: number | null; cron_expr: string; enabled: boolean }>({
  name: "",
  trigger_type: "interval",
  interval_seconds: 3600,
  cron_expr: "",
  enabled: true
});

let pollTimer: number | null = null;
let autoSaveTimer: number | null = null;
let skipNextContentWatch = false;

const isActiveRun = computed(() => runStatus.value === "pending" || runStatus.value === "running");
const activeFile = computed(() => openFiles.value.find((file) => file.path === activePath.value) ?? null);
const editorContent = computed<string>({
  get: () => activeFile.value?.content ?? "",
  set: (value) => {
    if (activeFile.value) activeFile.value.content = value;
  }
});
const isActiveMarkdown = computed(() => activeFile.value?.language === "markdown");
const showMarkdownPreview = computed(() => isActiveMarkdown.value && viewMode.value === "preview");
// html: false makes markdown-it escape raw HTML, so v-html only renders markdown-generated tags.
const renderedMarkdown = computed(() => (activeFile.value ? markdown.render(activeFile.value.content) : ""));
// New files/folders/uploads land in the selected directory (or the selected file's directory).
const selectedDir = computed(() => {
  const key = selectedKeys.value[0];
  if (!key) return "/";
  const node = findNode(treeData.value, key);
  if (!node) return "/";
  if (!node.isLeaf) return key;
  return parentPath(key);
});
const treeMenuOptions = computed<DropdownOption[]>(() => [
  { label: t("common.copy"), key: "copy" },
  { label: t("script.paste"), key: "paste", disabled: !clipboard.value },
  { type: "divider", key: "divider" },
  { label: t("script.rename"), key: "rename" },
  { label: t("common.delete"), key: "delete" }
]);
const tabMenuOptions = computed<DropdownOption[]>(() => [
  { label: t("script.editorTab.close"), key: "close" },
  { label: t("script.editorTab.closeOthers"), key: "closeOthers", disabled: openFiles.value.length <= 1 },
  { label: t("script.editorTab.closeLeft"), key: "closeLeft", disabled: !hasTabsToSide(tabMenu.path, "left") },
  { label: t("script.editorTab.closeRight"), key: "closeRight", disabled: !hasTabsToSide(tabMenu.path, "right") },
  { type: "divider", key: "divider" },
  { label: t("script.editorTab.closeAll"), key: "closeAll" }
]);

const runColumns = computed<DataTableColumns<ScriptRun>>(() => [
  { title: t("script.field.trigger"), key: "trigger", width: 90, render: (row) => t(`script.trigger.${row.trigger}`) },
  {
    title: t("field.status"),
    key: "status",
    width: 100,
    render: (row) => h(NTag, { size: "small", type: runStatusType(row.status) }, () => runStatusLabel(row.status))
  },
  { title: t("script.field.exitCode"), key: "exit_code", width: 80, render: (row) => (row.exit_code === null ? "-" : String(row.exit_code)) },
  { title: t("field.createdAt"), key: "created_at", width: 160, render: (row) => formatDateTime(row.created_at) },
  {
    title: t("common.actions"),
    key: "actions",
    width: 120,
    render: (row) =>
      h("div", { class: "table-action-group" }, [
        h(NButton, { size: "tiny", quaternary: true, onClick: () => viewRun(row) }, () => t("script.runViewLog")),
        row.status === "pending" || row.status === "running"
          ? h(NButton, { size: "tiny", quaternary: true, type: "warning", onClick: () => cancelRun(row.run_id) }, () => t("script.runCancel"))
          : null
      ].filter(Boolean))
  }
]);

const scheduleColumns = computed<DataTableColumns<ScriptSchedule>>(() => [
  { title: t("script.schedule.name"), key: "name", width: 120, render: (row) => row.name || t("common.none") },
  {
    title: t("script.schedule.type"),
    key: "trigger_type",
    width: 150,
    render: (row) =>
      row.trigger_type === "interval"
        ? t("script.schedule.intervalValue", { seconds: row.interval_seconds ?? 0 })
        : row.cron_expr
  },
  {
    title: t("script.schedule.enabled"),
    key: "enabled",
    width: 80,
    render: (row) => h(NTag, { size: "small", type: row.enabled ? "success" : "default" }, () => (row.enabled ? t("common.enabled") : t("common.disabled")))
  },
  { title: t("script.schedule.nextRun"), key: "next_run_at", width: 160, render: (row) => (row.next_run_at ? formatDateTime(row.next_run_at) : "-") },
  {
    title: t("common.actions"),
    key: "actions",
    width: 110,
    render: (row) =>
      h("div", { class: "table-action-group" }, [
        h(NButton, { size: "tiny", quaternary: true, circle: true, title: t("common.edit"), onClick: () => openScheduleEdit(row) }, { icon: () => h(NIcon, { component: Edit20Regular }) }),
        h(NButton, { size: "tiny", quaternary: true, circle: true, type: "error", title: t("common.delete"), onClick: () => confirmScheduleDelete(row) }, { icon: () => h(NIcon, { component: Delete20Regular }) })
      ])
  }
]);

onMounted(() => {
  void reloadTree();
  void loadRuns();
});

onBeforeUnmount(() => {
  stopPolling();
  clearAutoSaveTimer();
});

watch(editorContent, (value) => {
  if (skipNextContentWatch) {
    skipNextContentWatch = false;
    return;
  }
  const file = activeFile.value;
  if (autoSaveEnabled.value && file) {
    scheduleAutoSave(file.path, value);
  }
});

function toNodes(entries: { name: string; path: string; is_dir: boolean }[]): TreeOption[] {
  return entries.map((entry) => ({ key: entry.path, label: entry.name, isLeaf: !entry.is_dir }));
}

function renderTreePrefix({ option }: { option: TreeOption }): VNodeChild {
  const name = String(option.label ?? "");
  const icon = option.isLeaf
    ? getFileIcon(name)
    : getFolderIcon(name, expandedKeys.value.includes(String(option.key)));
  return h(icon, { width: 16, height: 16, class: "script-file-icon" });
}

async function reloadTree() {
  try {
    const result = await listScriptFiles(props.project.id, "/");
    treeData.value = toNodes(result.entries);
    expandedKeys.value = [];
  } catch (error) {
    showError(message, error);
  }
}

async function loadTreeChildren(node: TreeOption) {
  try {
    const result = await listScriptFiles(props.project.id, String(node.key));
    node.children = toNodes(result.entries);
  } catch (error) {
    showError(message, error);
  }
}

async function handleSelect(keys: Array<string | number>) {
  selectedKeys.value = keys.map(String);
  const key = keys[0];
  if (key === undefined) return;
  const node = findNode(treeData.value, String(key));
  if (!node || !node.isLeaf) return;
  await openFile(String(key));
}

async function openFile(path: string) {
  const existing = openFiles.value.find((file) => file.path === path);
  if (existing) {
    setActive(path);
    return;
  }
  try {
    const result = await readScriptFile(props.project.id, path);
    openFiles.value.push({
      path: result.path,
      name: baseName(result.path),
      content: result.content,
      savedContent: result.content,
      language: languageForPath(result.path),
      truncated: result.truncated
    });
    if (result.truncated) message.warning(t("script.fileTruncated"));
    setActive(result.path);
  } catch (error) {
    showError(message, error);
  }
}

function setActive(path: string) {
  if (activePath.value === path) {
    if (selectedKeys.value[0] !== path) selectedKeys.value = [path];
    return;
  }
  clearAutoSaveTimer();
  skipNextContentWatch = true;
  activePath.value = path;
  selectedKeys.value = [path];
  // Each newly focused file starts in source view; markdown preview is opt-in per file.
  viewMode.value = "source";
}

function closeTab(path: string) {
  const index = openFiles.value.findIndex((file) => file.path === path);
  if (index < 0) return;
  openFiles.value.splice(index, 1);
  if (activePath.value === path) {
    const fallback = openFiles.value[index] || openFiles.value[index - 1] || null;
    if (fallback) setActive(fallback.path);
    else {
      activePath.value = "";
      clearAutoSaveTimer();
    }
  }
}

function closeOtherTabs(path: string) {
  openFiles.value = openFiles.value.filter((file) => file.path === path);
  setActive(path);
}

function closeTabsToSide(path: string, side: "left" | "right") {
  const index = openFiles.value.findIndex((file) => file.path === path);
  if (index < 0) return;
  openFiles.value = side === "left" ? openFiles.value.slice(index) : openFiles.value.slice(0, index + 1);
  if (!openFiles.value.some((file) => file.path === activePath.value)) setActive(path);
}

function hasTabsToSide(path: string, side: "left" | "right") {
  const index = openFiles.value.findIndex((file) => file.path === path);
  if (index < 0) return false;
  return side === "left" ? index > 0 : index < openFiles.value.length - 1;
}

function closeAllTabs() {
  openFiles.value = [];
  activePath.value = "";
  clearAutoSaveTimer();
}

async function saveFile() {
  const file = activeFile.value;
  if (!file) return;
  clearAutoSaveTimer();
  await saveFileContent(file.path, file.content, false);
}

async function saveFileContent(path: string, content: string, silent: boolean) {
  savingFile.value = true;
  try {
    await writeScriptFile(props.project.id, path, content);
    const file = openFiles.value.find((item) => item.path === path);
    if (file) file.savedContent = content;
    if (!silent) message.success(t("script.fileSaved"));
  } catch (error) {
    showError(message, error);
  } finally {
    savingFile.value = false;
  }
}

function setAutoSave(value: boolean) {
  localStorage.setItem(AUTO_SAVE_KEY, value ? "1" : "0");
  const file = activeFile.value;
  if (value && file) {
    scheduleAutoSave(file.path, file.content);
  } else {
    clearAutoSaveTimer();
  }
}

function renderEditorTab(file: OpenFile): VNodeChild {
  const dirty = file.content !== file.savedContent;
  return h(
    "span",
    {
      class: "script-editor-tab",
      title: file.path,
      onContextmenu: (event: MouseEvent) => openTabMenu(event, file.path)
    },
    [
      h(getFileIcon(file.name), { width: 15, height: 15, class: "script-file-icon" }),
      h("span", { class: "script-editor-tab-name" }, file.name),
      dirty ? h("span", { class: "script-editor-tab-dot", title: t("script.autoSave") }) : null
    ]
  );
}

function openTabMenu(event: MouseEvent, path: string) {
  event.preventDefault();
  event.stopPropagation();
  tabMenu.path = path;
  tabMenu.x = event.clientX;
  tabMenu.y = event.clientY;
  tabMenu.show = false;
  void nextTick(() => (tabMenu.show = true));
}

function handleTabMenuSelect(key: string) {
  tabMenu.show = false;
  const path = tabMenu.path;
  if (!path) return;
  if (key === "close") closeTab(path);
  else if (key === "closeOthers") closeOtherTabs(path);
  else if (key === "closeLeft") closeTabsToSide(path, "left");
  else if (key === "closeRight") closeTabsToSide(path, "right");
  else if (key === "closeAll") closeAllTabs();
}

function scheduleAutoSave(path: string, content: string) {
  clearAutoSaveTimer();
  autoSaveTimer = window.setTimeout(() => {
    autoSaveTimer = null;
    void saveFileContent(path, content, true);
  }, 800);
}

function clearAutoSaveTimer() {
  if (autoSaveTimer !== null) {
    clearTimeout(autoSaveTimer);
    autoSaveTimer = null;
  }
}

function togglePanel() {
  panelCollapsed.value = !panelCollapsed.value;
  localStorage.setItem(PANEL_COLLAPSED_KEY, panelCollapsed.value ? "1" : "0");
  // On expand, nudge a layout pass so the embedded terminal (xterm) re-fits to the restored size.
  if (!panelCollapsed.value) {
    void nextTick(() => window.dispatchEvent(new Event("resize")));
  }
}

function deletePath(path: string) {
  if (!path) return;
  dialog.warning({
    title: t("common.delete"),
    content: t("script.deleteEntryConfirm", { name: path }),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: async () => {
      try {
        await deleteScriptEntry(props.project.id, path);
        closeTabsUnder(path);
        await refreshDir(parentPath(path));
        message.success(t("script.fileDeleted"));
      } catch (error) {
        showError(message, error);
      }
    }
  });
}

// --- tree context menu (copy / paste / rename / delete) ---------------

function treeNodeProps({ option }: { option: TreeOption }) {
  return {
    onContextmenu(event: MouseEvent) {
      event.preventDefault();
      event.stopPropagation();
      treeMenu.target = option;
      selectedKeys.value = [String(option.key)];
      treeMenu.x = event.clientX;
      treeMenu.y = event.clientY;
      treeMenu.show = false;
      void nextTick(() => (treeMenu.show = true));
    }
  };
}

function handleTreeMenuSelect(key: string) {
  treeMenu.show = false;
  const node = treeMenu.target;
  if (!node) return;
  if (key === "copy") setClipboard(String(node.key));
  else if (key === "paste") void pasteTo(node);
  else if (key === "rename") openRename(node);
  else if (key === "delete") deletePath(String(node.key));
}

function setClipboard(path: string) {
  clipboard.value = path;
  message.success(t("script.copyPrepared"));
}

async function pasteTo(node: TreeOption) {
  if (!clipboard.value) return;
  const targetDir = nodeDir(node);
  try {
    await copyScriptEntries(props.project.id, {
      paths: [clipboard.value],
      target_dir: targetDir,
      conflict_policy: "rename"
    });
    await refreshDir(targetDir);
    expandDir(targetDir);
    message.success(t("script.pasted"));
  } catch (error) {
    showError(message, error);
  }
}

function openRename(node: TreeOption) {
  renameModal.path = String(node.key);
  renameModal.value = String(node.label ?? baseName(String(node.key)));
  renameModal.show = true;
}

async function confirmRename() {
  const name = renameModal.value.trim();
  const oldPath = renameModal.path;
  if (!name || !oldPath) return;
  renameModal.saving = true;
  try {
    const entry = await renameScriptEntry(props.project.id, oldPath, name);
    renameModal.show = false;
    syncPathsAfterMove(oldPath, entry.path);
    await refreshDir(parentPath(oldPath));
    message.success(t("script.renamed"));
  } catch (error) {
    showError(message, error);
  } finally {
    renameModal.saving = false;
  }
}

// --- drag & drop move --------------------------------------------------

async function handleTreeDrop({ node, dragNode, dropPosition }: TreeDropInfo) {
  const sourcePath = String(dragNode.key);
  const targetDir = dropPosition === "inside" && !node.isLeaf ? String(node.key) : nodeDir(node);
  if (parentPath(sourcePath) === targetDir) return;
  if (!dragNode.isLeaf && (targetDir === sourcePath || targetDir.startsWith(sourcePath.replace(/\/+$/, "") + "/"))) {
    message.warning(t("script.moveInvalidTarget"));
    return;
  }
  try {
    const moved = await moveScriptEntries(props.project.id, {
      paths: [sourcePath],
      target_dir: targetDir,
      conflict_policy: "error"
    });
    const newPath = moved[0]?.path ?? joinPath(targetDir, baseName(sourcePath));
    syncPathsAfterMove(sourcePath, newPath);
    const sourceDir = parentPath(sourcePath);
    await refreshDir(sourceDir);
    if (targetDir !== sourceDir) await refreshDir(targetDir);
    expandDir(targetDir);
    message.success(t("script.moved"));
  } catch (error) {
    showError(message, error);
  }
}

function syncPathsAfterMove(oldPath: string, newPath: string) {
  if (oldPath === newPath) return;
  const prefix = oldPath + "/";
  for (const file of openFiles.value) {
    if (file.path === oldPath) {
      file.path = newPath;
      file.name = baseName(newPath);
      file.language = languageForPath(newPath);
    } else if (file.path.startsWith(prefix)) {
      const next = newPath + file.path.slice(oldPath.length);
      file.path = next;
      file.name = baseName(next);
      file.language = languageForPath(next);
    }
  }
  if (activePath.value === oldPath) activePath.value = newPath;
  else if (activePath.value.startsWith(prefix)) activePath.value = newPath + activePath.value.slice(oldPath.length);
}

function closeTabsUnder(path: string) {
  const prefix = path + "/";
  openFiles.value
    .filter((file) => file.path === path || file.path.startsWith(prefix))
    .forEach((file) => closeTab(file.path));
}

// --- tree refresh helpers (preserve expansion) -------------------------

async function refreshDir(dirPath: string) {
  const dir = dirPath || "/";
  const node = dir === "/" ? null : findNode(treeData.value, dir);
  if (dir === "/" || !node || node.isLeaf) {
    await reloadTreePreservingExpansion();
    return;
  }
  try {
    const result = await listScriptFiles(props.project.id, dir);
    node.children = toNodes(result.entries);
  } catch (error) {
    showError(message, error);
  }
}

async function reloadTreePreservingExpansion() {
  const expanded = [...expandedKeys.value];
  try {
    const result = await listScriptFiles(props.project.id, "/");
    const data = toNodes(result.entries);
    await loadExpandedChildren(data, expanded);
    treeData.value = data;
    expandedKeys.value = expanded.filter((key) => findNode(data, key) !== null);
  } catch (error) {
    showError(message, error);
  }
}

async function loadExpandedChildren(nodes: TreeOption[], expanded: string[]) {
  for (const node of nodes) {
    if (node.isLeaf || !expanded.includes(String(node.key))) continue;
    try {
      const result = await listScriptFiles(props.project.id, String(node.key));
      node.children = toNodes(result.entries);
      await loadExpandedChildren(node.children, expanded);
    } catch {
      /* ignore subtree reload errors */
    }
  }
}

function expandDir(dir: string) {
  if (dir !== "/" && !expandedKeys.value.includes(dir)) {
    expandedKeys.value = [...expandedKeys.value, dir];
  }
}

function nodeDir(node: TreeOption): string {
  const key = String(node.key);
  return node.isLeaf ? parentPath(key) : key;
}

function parentPath(value: string): string {
  const index = value.lastIndexOf("/");
  return index > 0 ? value.slice(0, index) : "/";
}

function baseName(value: string): string {
  const parts = value.split("/").filter(Boolean);
  return parts[parts.length - 1] || "";
}

function joinPath(dir: string, name: string): string {
  return dir === "/" ? `/${name}` : `${dir}/${name}`;
}

function openNewEntry(isDir: boolean) {
  newEntryIsDir.value = isDir;
  newEntryName.value = "";
  showNewEntry.value = true;
}

async function confirmNewEntry() {
  const name = newEntryName.value.trim();
  if (!name) return;
  const dir = selectedDir.value;
  const path = joinPath(dir, name);
  try {
    if (newEntryIsDir.value) {
      await mkdirScript(props.project.id, path);
    } else {
      await writeScriptFile(props.project.id, path, "");
    }
    showNewEntry.value = false;
    await refreshDir(dir);
    expandDir(dir);
    message.success(t("script.created"));
  } catch (error) {
    showError(message, error);
  }
}

function triggerUpload() {
  uploadInputRef.value?.click();
}

async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;
  const dir = selectedDir.value;
  try {
    await uploadScriptFile(props.project.id, dir, file);
    await refreshDir(dir);
    expandDir(dir);
    message.success(t("script.uploaded"));
  } catch (error) {
    showError(message, error);
  }
}

async function runScript() {
  running.value = true;
  try {
    const result = await submitScriptRun(props.project.id);
    activeTab.value = "log";
    runLog.value = "";
    startPolling(result.run_id);
    void loadRuns();
    message.success(t("script.runStarted"));
  } catch (error) {
    showError(message, error);
  } finally {
    running.value = false;
  }
}

async function loadRuns() {
  loadingRuns.value = true;
  try {
    runs.value = (await listScriptRuns(props.project.id, { page_size: 50 })).items;
  } catch (error) {
    showError(message, error);
  } finally {
    loadingRuns.value = false;
  }
}

function viewRun(run: ScriptRun) {
  activeTab.value = "log";
  startPolling(run.run_id);
}

async function cancelRun(runId: string) {
  try {
    await cancelScriptRun(runId);
    message.success(t("script.runCanceled"));
    if (currentRunId.value === runId) await refreshLog();
    void loadRuns();
  } catch (error) {
    showError(message, error);
  }
}

function cancelCurrentRun() {
  if (currentRunId.value) void cancelRun(currentRunId.value);
}

function startPolling(runId: string) {
  stopPolling();
  currentRunId.value = runId;
  void refreshLog();
  pollTimer = window.setInterval(() => void refreshLog(), 2000);
}

function stopPolling() {
  if (pollTimer !== null) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

async function refreshLog() {
  if (!currentRunId.value) return;
  try {
    const result = await getScriptRunLog(currentRunId.value);
    runLog.value = result.logs;
    runStatus.value = result.status;
    if (result.status !== "pending" && result.status !== "running") {
      stopPolling();
      void loadRuns();
    }
  } catch {
    stopPolling();
  }
}

function handleTabChange(tab: string) {
  if (tab === "history") void loadRuns();
  else if (tab === "schedules") void loadSchedules();
}

async function loadSchedules() {
  loadingSchedules.value = true;
  try {
    schedules.value = await listScriptSchedules(props.project.id);
  } catch (error) {
    showError(message, error);
  } finally {
    loadingSchedules.value = false;
  }
}

function openScheduleCreate() {
  editingSchedule.value = null;
  Object.assign(scheduleForm, { name: "", trigger_type: "interval", interval_seconds: 3600, cron_expr: "", enabled: true });
  showSchedule.value = true;
}

function openScheduleEdit(schedule: ScriptSchedule) {
  editingSchedule.value = schedule;
  Object.assign(scheduleForm, {
    name: schedule.name,
    trigger_type: schedule.trigger_type,
    interval_seconds: schedule.interval_seconds ?? 3600,
    cron_expr: schedule.cron_expr,
    enabled: schedule.enabled
  });
  showSchedule.value = true;
}

async function saveSchedule() {
  savingSchedule.value = true;
  try {
    const payload = {
      name: scheduleForm.name,
      trigger_type: scheduleForm.trigger_type,
      interval_seconds: scheduleForm.trigger_type === "interval" ? scheduleForm.interval_seconds : null,
      cron_expr: scheduleForm.trigger_type === "cron" ? scheduleForm.cron_expr : "",
      enabled: scheduleForm.enabled
    };
    if (editingSchedule.value) {
      await updateScriptSchedule(editingSchedule.value.id, payload);
    } else {
      await createScriptSchedule(props.project.id, payload);
    }
    showSchedule.value = false;
    await loadSchedules();
    message.success(t("script.schedule.saved"));
  } catch (error) {
    showError(message, error);
  } finally {
    savingSchedule.value = false;
  }
}

function confirmScheduleDelete(schedule: ScriptSchedule) {
  dialog.warning({
    title: t("script.schedule.deleteTitle"),
    content: t("script.schedule.deleteConfirm", { name: schedule.name || String(schedule.id) }),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: async () => {
      try {
        const result = await deleteScriptSchedule(schedule.id);
        await loadSchedules();
        message.success(messageText(result, "script.schedule.deleted"));
      } catch (error) {
        showError(message, error);
      }
    }
  });
}

async function loadEnvironment() {
  loadingEnv.value = true;
  try {
    environment.value = await getScriptEnvironment(props.project.id);
  } catch (error) {
    showError(message, error);
  } finally {
    loadingEnv.value = false;
  }
}

function runStatusType(status: string) {
  if (status === "success") return "success";
  if (status === "failed" || status === "timeout") return "error";
  if (status === "running") return "info";
  if (status === "canceled") return "warning";
  return "default";
}

function runStatusLabel(status: string) {
  return status ? t(`script.runStatus.${status}`) : "";
}

function collapseAll() {
  expandedKeys.value = [];
}

function addTerminal() {
  terminalSeq += 1;
  const id = `terminal-${terminalSeq}`;
  terminals.value.push({ id, index: terminalSeq, closable: true });
  activeTab.value = id;
}

function closeTerminal(id: string) {
  const index = terminals.value.findIndex((term) => term.id === id);
  if (index < 0) return;
  terminals.value.splice(index, 1);
  if (activeTab.value === id) {
    const fallback = terminals.value[index - 1] || terminals.value[index] || null;
    activeTab.value = fallback ? fallback.id : "log";
  }
}

function renderTerminalTab(term: TerminalTab): VNodeChild {
  const label = term.closable ? `${t("script.tab.terminal")} ${term.index}` : t("script.tab.terminal");
  const children: VNodeChild[] = [h("span", null, label)];
  if (term.closable) {
    children.push(
      h(NIcon, {
        component: Dismiss16Regular,
        class: "script-terminal-tab-close",
        onClick: (event: MouseEvent) => {
          event.stopPropagation();
          closeTerminal(term.id);
        }
      })
    );
  }
  return h("span", { class: "script-terminal-tab" }, children);
}

function findNode(nodes: TreeOption[], key: string): TreeOption | null {
  for (const node of nodes) {
    if (node.key === key) return node;
    if (node.children) {
      const found = findNode(node.children, key);
      if (found) return found;
    }
  }
  return null;
}

function languageForPath(path: string): string {
  const ext = path.split(".").pop()?.toLowerCase() || "";
  const map: Record<string, string> = {
    js: "javascript",
    jsx: "javascript",
    mjs: "javascript",
    cjs: "javascript",
    ts: "typescript",
    tsx: "typescript",
    json: "json",
    html: "html",
    htm: "html",
    css: "css",
    scss: "scss",
    less: "less",
    py: "python",
    go: "go",
    c: "cpp",
    h: "cpp",
    cpp: "cpp",
    cc: "cpp",
    hpp: "cpp",
    sql: "sql",
    sh: "shell",
    bash: "shell",
    yaml: "yaml",
    yml: "yaml",
    xml: "xml",
    ini: "ini",
    toml: "ini",
    md: "markdown",
    markdown: "markdown",
    vue: "html"
  };
  return map[ext] || "plaintext";
}
</script>

<style scoped>
.script-workbench {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0;
}

.script-workbench-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-color);
}

.script-workbench-title {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.script-workbench-name {
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 320px;
}

.script-workbench-actions {
  display: flex;
  gap: 8px;
}

.script-workbench-body {
  display: flex;
  flex: 1;
  min-height: 0;
}

.script-sidebar {
  width: 260px;
  flex-shrink: 0;
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.script-sidebar-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-bottom: 1px solid var(--border-color);
}

.script-sidebar-title {
  font-size: 13px;
  color: var(--text-color-2);
}

.script-sidebar-tools {
  display: flex;
  gap: 2px;
}

.script-tree {
  flex: 1;
  overflow: auto;
  padding: 6px;
}

.script-tree :deep(.script-file-icon) {
  display: block;
  flex: none;
}

.script-upload-input {
  display: none;
}

.script-main {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  min-height: 0;
}

.script-editor-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 6px 12px;
  border-bottom: 1px solid var(--border-color);
}

.script-editor-path {
  font-size: 12px;
  color: var(--text-color-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.script-editor-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.script-auto-save {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-color-3);
  font-size: 12px;
  white-space: nowrap;
}

.script-editor-tabs {
  flex-shrink: 0;
  border-bottom: 1px solid var(--border-color);
}

.script-editor-tabs :deep(.n-tabs-nav) {
  padding: 4px 6px 0;
}

.script-editor-tabs :deep(.n-tabs-tab) {
  padding-top: 6px;
  padding-bottom: 6px;
}

.script-editor-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 200px;
}

.script-editor-tab :deep(.script-file-icon),
.script-editor-tab .script-file-icon {
  flex: none;
}

.script-editor-tab-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.script-editor-tab-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-color-3);
  flex: none;
}

.script-editor-host {
  flex: 1;
  min-height: 200px;
  position: relative;
}

.script-editor-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-color-3);
}

.script-markdown-preview {
  position: absolute;
  inset: 0;
  overflow: auto;
  padding: 16px 28px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-color);
  word-wrap: break-word;
}

.script-markdown-preview :deep(h1),
.script-markdown-preview :deep(h2) {
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.3em;
}

.script-markdown-preview :deep(h1),
.script-markdown-preview :deep(h2),
.script-markdown-preview :deep(h3),
.script-markdown-preview :deep(h4) {
  margin: 1em 0 0.5em;
  line-height: 1.3;
}

.script-markdown-preview :deep(p),
.script-markdown-preview :deep(ul),
.script-markdown-preview :deep(ol) {
  margin: 0.6em 0;
}

.script-markdown-preview :deep(a) {
  color: var(--primary-color);
}

.script-markdown-preview :deep(code) {
  font-family: Consolas, Monaco, "Courier New", monospace;
  font-size: 0.92em;
  padding: 0.15em 0.4em;
  border-radius: 4px;
  background: var(--panel-bg-hover);
}

.script-markdown-preview :deep(pre) {
  margin: 0.8em 0;
  padding: 12px 14px;
  border-radius: 6px;
  overflow: auto;
  background: var(--panel-bg-hover);
}

.script-markdown-preview :deep(pre code) {
  padding: 0;
  background: transparent;
}

.script-markdown-preview :deep(blockquote) {
  margin: 0.8em 0;
  padding: 0 1em;
  color: var(--muted-color);
  border-left: 3px solid var(--border-color);
}

.script-markdown-preview :deep(table) {
  border-collapse: collapse;
  margin: 0.8em 0;
}

.script-markdown-preview :deep(th),
.script-markdown-preview :deep(td) {
  border: 1px solid var(--border-color);
  padding: 6px 12px;
}

.script-markdown-preview :deep(img) {
  max-width: 100%;
}

.script-panel {
  height: 38%;
  min-height: 220px;
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  padding: 0 12px;
  overflow: auto;
}

.script-panel.script-panel-collapsed {
  flex: 0 0 auto;
  height: auto;
  min-height: 0;
  overflow: visible;
}

.script-panel-suffix {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.script-panel-toolbar {
  padding: 6px 0;
}

.script-log-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
}

.script-log-empty {
  color: var(--text-color-3);
  font-size: 12px;
}

.script-log-output {
  margin: 0;
  padding: 8px;
  background: #11151c;
  color: #d4d4d4;
  font-family: Consolas, Monaco, "Courier New", monospace;
  font-size: 12px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 180px;
  overflow: auto;
}

.script-env {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-bottom: 10px;
}

.script-env-row {
  display: flex;
  gap: 10px;
  font-size: 13px;
}

.script-env-row span:first-child {
  color: var(--text-color-3);
  min-width: 90px;
}

.script-env-warn {
  color: var(--warning-color, #f0a020);
}

.script-env-packages {
  margin: 4px 0 0;
  padding: 8px;
  background: var(--code-color, rgba(0, 0, 0, 0.04));
  border-radius: 4px;
  font-size: 12px;
  max-height: 140px;
  overflow: auto;
  white-space: pre-wrap;
}

.script-terminal-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.script-terminal-tab-close {
  font-size: 14px;
  border-radius: 4px;
  opacity: 0.55;
}

.script-terminal-tab-close:hover {
  opacity: 1;
  background: var(--hover-color, rgba(127, 127, 127, 0.16));
}
</style>
