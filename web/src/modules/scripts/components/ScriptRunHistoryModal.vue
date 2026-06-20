<template>
  <n-modal
    :show="show"
    preset="card"
    class="modal-card script-history-modal"
    :title="title"
    @update:show="(value) => emit('update:show', value)"
  >
    <template #header-extra>
      <n-button quaternary circle size="small" :title="t('common.refresh')" :loading="loading" @click="() => void loadRuns()">
        <template #icon><n-icon :component="ArrowClockwise20Regular" /></template>
      </n-button>
    </template>
    <div class="script-history">
      <n-data-table
        size="small"
        :columns="columns"
        :data="runs"
        :loading="loading"
        :row-key="(row) => row.run_id"
        :scroll-x="tableScrollX"
        :max-height="240"
        @unstable-column-resize="handleColumnResize"
      />
      <div v-if="selectedRunId" class="script-history-log">
        <div class="script-history-log-bar">
          <n-tag size="small" :type="statusType(selectedStatus)">{{ statusLabel(selectedStatus) }}</n-tag>
          <span class="script-history-run-id" :title="selectedRunId">{{ selectedRunId }}</span>
        </div>
        <pre class="script-history-log-output">{{ selectedLog || t("script.emptyLog") }}</pre>
      </div>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { computed, h, onBeforeUnmount, reactive, ref, watch } from "vue";
import { NButton, NDataTable, NIcon, NModal, NTag, useMessage } from "naive-ui";
import type { DataTableColumns } from "naive-ui";
import { ArrowClockwise20Regular, Dismiss20Regular, Document20Regular } from "@vicons/fluent";

import { formatDateTime, t } from "../../../i18n";
import { showError } from "../../../utils/message";
import { sumColumnWidths, updateColumnWidth, withResizableColumns } from "../../../utils/table";
import {
  cancelScriptRun,
  getScriptRunLog,
  listScriptRuns,
  type ScriptProject,
  type ScriptRun,
  type ScriptRunStatus
} from "../api";

const props = defineProps<{ show: boolean; project: ScriptProject | null }>();
const emit = defineEmits<{ "update:show": [value: boolean] }>();

const message = useMessage();
const runs = ref<ScriptRun[]>([]);
const loading = ref(false);
const selectedRunId = ref("");
const selectedStatus = ref<ScriptRunStatus | "">("");
const selectedLog = ref("");
let pollTimer: number | null = null;

const title = computed(() => t("script.historyTitle", { name: props.project?.name || "" }));
const columnWidths = reactive<Record<string, number>>({
  trigger: 110,
  status: 120,
  exitCode: 110,
  createdAt: 220,
  actions: 80
});
const columnWidthKeys: Record<string, string> = {
  trigger: "trigger",
  status: "status",
  exit_code: "exitCode",
  created_at: "createdAt"
};
const tableScrollX = computed(() => sumColumnWidths(columnWidths));

const columns = computed<DataTableColumns<ScriptRun>>(() =>
  withResizableColumns([
  { title: t("script.field.trigger"), key: "trigger", width: columnWidths.trigger, render: (row) => t(`script.trigger.${row.trigger}`) },
  {
    title: t("field.status"),
    key: "status",
    width: columnWidths.status,
    render: (row) => h(NTag, { size: "small", type: statusType(row.status) }, () => statusLabel(row.status))
  },
  { title: t("script.field.exitCode"), key: "exit_code", width: columnWidths.exitCode, render: (row) => (row.exit_code === null ? "-" : String(row.exit_code)) },
  {
    title: t("field.createdAt"),
    key: "created_at",
    width: columnWidths.createdAt,
    sorter: (a, b) => a.created_at.localeCompare(b.created_at),
    defaultSortOrder: "descend",
    render: (row) => formatDateTime(row.created_at)
  },
  {
    title: t("common.actions"),
    key: "actions",
    width: columnWidths.actions,
    fixed: "right",
    render: (row) =>
      h("div", { class: "table-action-group" }, [
        h(
          NButton,
          { size: "tiny", quaternary: true, circle: true, title: t("script.runViewLog"), onClick: () => selectRun(row) },
          { icon: () => h(NIcon, { component: Document20Regular }) }
        ),
        row.status === "pending" || row.status === "running"
          ? h(
              NButton,
              { size: "tiny", quaternary: true, circle: true, type: "warning", title: t("script.runCancel"), onClick: () => void cancel(row.run_id) },
              { icon: () => h(NIcon, { component: Dismiss20Regular }) }
            )
          : null
      ].filter(Boolean))
  }
])
);

watch(
  () => props.show,
  (show) => {
    if (show) {
      resetLog();
      void loadRuns();
    } else {
      stopPolling();
    }
  }
);

onBeforeUnmount(stopPolling);

async function loadRuns() {
  if (!props.project) return;
  loading.value = true;
  try {
    runs.value = (await listScriptRuns(props.project.id, { page_size: 50 })).items;
  } catch (error) {
    showError(message, error);
  } finally {
    loading.value = false;
  }
}

function selectRun(run: ScriptRun) {
  selectedRunId.value = run.run_id;
  startPolling();
}

function startPolling() {
  stopPolling();
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
  if (!selectedRunId.value) return;
  try {
    const result = await getScriptRunLog(selectedRunId.value);
    selectedLog.value = result.logs;
    selectedStatus.value = result.status;
    if (result.status !== "pending" && result.status !== "running") {
      stopPolling();
      void loadRuns();
    }
  } catch {
    stopPolling();
  }
}

async function cancel(runId: string) {
  try {
    await cancelScriptRun(runId);
    message.success(t("script.runCanceled"));
    if (selectedRunId.value === runId) await refreshLog();
    await loadRuns();
  } catch (error) {
    showError(message, error);
  }
}

function handleColumnResize(_: number, limitedWidth: number, column: { key?: string | number }) {
  updateColumnWidth(columnWidths, column.key, columnWidthKeys, limitedWidth);
}

function resetLog() {
  selectedRunId.value = "";
  selectedStatus.value = "";
  selectedLog.value = "";
}

function statusType(status: string) {
  if (status === "success") return "success";
  if (status === "failed" || status === "timeout") return "error";
  if (status === "running") return "info";
  if (status === "canceled") return "warning";
  return "default";
}

function statusLabel(status: string) {
  return status ? t(`script.runStatus.${status}`) : "";
}
</script>

<style scoped>
.script-history {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.script-history-log-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.script-history-run-id {
  color: var(--text-color-3);
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.script-history-log-output {
  margin: 0;
  padding: 8px;
  background: #11151c;
  color: #d4d4d4;
  font-family: Consolas, Monaco, "Courier New", monospace;
  font-size: 12px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 220px;
  overflow: auto;
}
</style>
