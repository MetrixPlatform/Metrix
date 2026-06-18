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
            <n-button size="tiny" quaternary circle :title="t('common.refresh')" @click="reloadTree">
              <template #icon><n-icon :component="ArrowSync20Regular" /></template>
            </n-button>
          </div>
        </div>
        <n-tree
          block-line
          :data="treeData"
          :on-load="loadTreeChildren"
          :selected-keys="selectedKeys"
          :expanded-keys="expandedKeys"
          :render-prefix="renderTreePrefix"
          class="script-tree"
          @update:selected-keys="handleSelect"
          @update:expanded-keys="(keys) => (expandedKeys = keys as string[])"
        />
        <input ref="uploadInputRef" type="file" class="script-upload-input" @change="handleUpload" />
      </div>

      <div class="script-main">
        <div class="script-editor-bar">
          <span class="script-editor-path">{{ currentPath || t("script.noFileSelected") }}</span>
          <div class="script-editor-actions">
            <div v-if="currentPath" class="script-auto-save">
              <span>{{ t("script.autoSave") }}</span>
              <n-switch v-model:value="autoSaveEnabled" size="small" @update:value="setAutoSave" />
            </div>
            <n-button
              v-if="currentPath"
              size="small"
              quaternary
              circle
              type="error"
              :title="t('common.delete')"
              @click="deleteCurrent"
            >
              <template #icon><n-icon :component="Delete20Regular" /></template>
            </n-button>
            <permission-button
              v-if="currentPath"
              :permission="SCRIPT_OPERATE"
              size="small"
              type="primary"
              :loading="savingFile"
              @click="saveFile"
            >
              {{ t("common.save") }}
            </permission-button>
          </div>
        </div>
        <div class="script-editor-host">
          <code-editor v-if="currentPath" v-model="currentContent" :language="currentLanguage" />
          <div v-else class="script-editor-empty">{{ t("script.editorEmpty") }}</div>
        </div>

        <div class="script-panel">
          <n-tabs v-model:value="activeTab" type="line" size="small" @update:value="handleTabChange">
            <template #suffix>
              <n-button quaternary circle size="tiny" :title="t('script.terminalAdd')" @click="addTerminal">
                <template #icon><n-icon :component="Add20Regular" /></template>
              </n-button>
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
              <script-terminal-panel :project="project" :active="activeTab === term.id" />
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
        <p class="script-modal-hint">{{ t("script.entryLocation", { dir: currentDir }) }}</p>
      </n-form>
      <template #action>
        <div class="form-actions modal-fixed-actions">
          <n-button @click="showNewEntry = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" @click="confirmNewEntry">{{ t("common.create") }}</n-button>
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
import { computed, h, onBeforeUnmount, onMounted, reactive, ref, watch, type VNodeChild } from "vue";
import {
  Add20Regular,
  ArrowLeft20Regular,
  ArrowSync20Regular,
  ArrowUpload20Regular,
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
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NInputNumber,
  NModal,
  NRadioButton,
  NRadioGroup,
  NSwitch,
  NTabPane,
  NTabs,
  NTag,
  NTree,
  useDialog,
  useMessage
} from "naive-ui";
import type { DataTableColumns, TreeOption } from "naive-ui";

import PermissionButton from "../../../components/PermissionButton.vue";
import { appKey } from "../../../config/app";
import { formatDateTime, t } from "../../../i18n";
import { messageText, showError } from "../../../utils/message";
import {
  cancelScriptRun,
  createScriptSchedule,
  deleteScriptEntry,
  deleteScriptSchedule,
  getScriptEnvironment,
  getScriptRunLog,
  listScriptFiles,
  listScriptRuns,
  listScriptSchedules,
  mkdirScript,
  readScriptFile,
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

const message = useMessage();
const dialog = useDialog();

const treeData = ref<TreeOption[]>([]);
const selectedKeys = ref<string[]>([]);
const expandedKeys = ref<string[]>([]);
const currentPath = ref("");
const currentContent = ref("");
const currentLanguage = ref("plaintext");
const savingFile = ref(false);
const autoSaveEnabled = ref(localStorage.getItem(AUTO_SAVE_KEY) === "1");
const uploadInputRef = ref<HTMLInputElement | null>(null);

interface TerminalTab {
  id: string;
  index: number;
  closable: boolean;
}
// The default first terminal (terminal-1) and the log/history/schedule/environment tabs are
// not closable; only extra terminals added via the "+" button get a close button.
const terminals = ref<TerminalTab[]>([{ id: "terminal-1", index: 1, closable: false }]);
let terminalSeq = 1;

const activeTab = ref<string>("log");
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
const currentDir = computed(() => {
  if (!currentPath.value) return "/";
  const node = findNode(treeData.value, currentPath.value);
  if (node && !node.isLeaf) return currentPath.value;
  const index = currentPath.value.lastIndexOf("/");
  return index > 0 ? currentPath.value.slice(0, index) : "/";
});

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

watch(currentContent, (value) => {
  if (skipNextContentWatch) {
    skipNextContentWatch = false;
    return;
  }
  if (autoSaveEnabled.value && currentPath.value) {
    scheduleAutoSave(currentPath.value, value);
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
  try {
    clearAutoSaveTimer();
    const result = await readScriptFile(props.project.id, String(key));
    currentPath.value = result.path;
    skipNextContentWatch = true;
    currentContent.value = result.content;
    currentLanguage.value = languageForPath(result.path);
    if (result.truncated) message.warning(t("script.fileTruncated"));
  } catch (error) {
    showError(message, error);
  }
}

async function saveFile() {
  if (!currentPath.value) return;
  clearAutoSaveTimer();
  await saveFileContent(currentPath.value, currentContent.value, false);
}

async function saveFileContent(path: string, content: string, silent: boolean) {
  savingFile.value = true;
  try {
    await writeScriptFile(props.project.id, path, content);
    if (!silent) message.success(t("script.fileSaved"));
  } catch (error) {
    showError(message, error);
  } finally {
    savingFile.value = false;
  }
}

function setAutoSave(value: boolean) {
  localStorage.setItem(AUTO_SAVE_KEY, value ? "1" : "0");
  if (value && currentPath.value) {
    scheduleAutoSave(currentPath.value, currentContent.value);
  } else {
    clearAutoSaveTimer();
  }
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

function deleteCurrent() {
  const path = currentPath.value;
  if (!path) return;
  dialog.warning({
    title: t("common.delete"),
    content: t("script.deleteEntryConfirm", { name: path }),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: async () => {
      try {
        await deleteScriptEntry(props.project.id, path);
        clearAutoSaveTimer();
        currentPath.value = "";
        currentContent.value = "";
        await reloadTree();
        message.success(t("script.fileDeleted"));
      } catch (error) {
        showError(message, error);
      }
    }
  });
}

function openNewEntry(isDir: boolean) {
  newEntryIsDir.value = isDir;
  newEntryName.value = "";
  showNewEntry.value = true;
}

async function confirmNewEntry() {
  const name = newEntryName.value.trim();
  if (!name) return;
  const base = currentDir.value === "/" ? "" : currentDir.value;
  const path = `${base}/${name}`;
  try {
    if (newEntryIsDir.value) {
      await mkdirScript(props.project.id, path);
    } else {
      await writeScriptFile(props.project.id, path, "");
    }
    showNewEntry.value = false;
    await reloadTree();
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
  try {
    await uploadScriptFile(props.project.id, currentDir.value, file);
    await reloadTree();
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

.script-panel {
  height: 38%;
  min-height: 220px;
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  padding: 0 12px;
  overflow: auto;
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
