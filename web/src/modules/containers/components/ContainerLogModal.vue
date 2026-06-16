<template>
  <n-modal :show="show" preset="card" class="modal-card container-log-modal" :title="title" @update:show="$emit('update:show', $event)">
    <div class="container-log-body">
      <div class="container-log-toolbar">
        <span class="container-log-tail-label">{{ t("container.logTailLabel") }}</span>
        <n-input-number v-model:value="tailValue" :min="1" :max="5000" :show-button="false" />
        <n-button :loading="loading" @click="() => loadLogs()">{{ t("common.refresh") }}</n-button>
        <n-button :disabled="!logs" @click="copyLogs">{{ t("common.copy") }}</n-button>
        <n-button :loading="clearing" @click="clearLogs">{{ t("container.clearLogs") }}</n-button>
        <div class="container-log-switches">
          <div class="container-log-switch">
            <span>{{ t("container.wrapLines") }}</span>
            <n-switch v-model:value="wrapLines" size="small" />
          </div>
          <div class="container-log-switch">
            <span>{{ t("container.autoRefresh") }}</span>
            <n-switch v-model:value="autoRefresh" size="small" />
          </div>
        </div>
      </div>
      <div ref="logViewRef" class="container-log-content" :class="{ 'container-log-content--wrap': wrapLines }">
        <div class="container-log-lines">
          <template v-if="logLines.length">
            <div v-for="(line, index) in logLines" :key="index" class="container-log-line" :class="`container-log-line--${line.level}`">{{ line.text || " " }}</div>
          </template>
          <div v-else class="container-log-line container-log-line--muted">{{ t("container.logEmpty") }}</div>
        </div>
      </div>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import { NButton, NInputNumber, NModal, NSwitch, useDialog, useMessage } from "naive-ui";

import { t } from "../../../i18n";
import { copyText } from "../../../utils/clipboard";
import { showError } from "../../../utils/message";
import { clearContainerLogs, getContainerLogs, type ContainerItem } from "../api";

type LogLevel = "error" | "warn" | "success" | "info" | "debug" | "default";

const AUTO_REFRESH_INTERVAL = 3000;

const props = defineProps<{ show: boolean; container: ContainerItem | null }>();
const emit = defineEmits<{ "update:show": [value: boolean] }>();

const message = useMessage();
const dialog = useDialog();
const loading = ref(false);
const clearing = ref(false);
const logs = ref("");
const tailValue = ref(200);
const autoRefresh = ref(false);
const wrapLines = ref(false);
const logViewRef = ref<HTMLElement | null>(null);
const title = computed(() => t("container.logTitle", { name: props.container?.name || "" }));
const logLines = computed(() =>
  logs.value
    .replace(/\r/g, "")
    .split("\n")
    .map((text) => ({ text, level: detectLogLevel(text) }))
);
let timer: number | undefined;

function detectLogLevel(line: string): LogLevel {
  const lower = line.toLowerCase();
  const structured = lower.match(/"(?:level|severity|lvl)"\s*:\s*"?([a-z]+)"?/)?.[1] ?? lower.match(/\blevel=([a-z]+)/)?.[1];
  if (structured) {
    if (/(error|err|fatal|panic|critical|crit)/.test(structured)) return "error";
    if (/(warn)/.test(structured)) return "warn";
    if (/(debug|trace|verbose)/.test(structured)) return "debug";
    if (/(info|notice|log)/.test(structured)) return "info";
  }
  if (/\b(error|errors|fatal|panic|exception|failed|failure|denied|refused)\b/.test(lower)) return "error";
  if (/\b(warn|warning|warnings|deprecated)\b/.test(lower)) return "warn";
  if (/\b(success|succeeded|successfully|ready|started|listening|registered|enabled|ok)\b/.test(lower)) return "success";
  if (/\b(debug|trace|verbose)\b/.test(lower)) return "debug";
  if (/\b(info|notice)\b/.test(lower)) return "info";
  return "default";
}

watch(
  () => props.show,
  (show) => {
    if (show) {
      void loadLogs();
      if (autoRefresh.value) startAutoRefresh();
    } else {
      stopAutoRefresh();
    }
  }
);

watch(autoRefresh, (enabled) => {
  if (enabled && props.show) {
    startAutoRefresh();
    void loadLogs({ silent: true });
  } else {
    stopAutoRefresh();
  }
});

onBeforeUnmount(stopAutoRefresh);

async function loadLogs(options: { silent?: boolean } = {}) {
  if (!props.container) return;
  if (!options.silent) loading.value = true;
  try {
    logs.value = (await getContainerLogs(props.container.id, tailValue.value || 200)).logs;
    await scrollToBottom();
  } catch (error) {
    showError(message, error);
  } finally {
    if (!options.silent) loading.value = false;
  }
}

async function scrollToBottom() {
  await nextTick();
  const view = logViewRef.value;
  if (view) view.scrollTop = view.scrollHeight;
}

function startAutoRefresh() {
  stopAutoRefresh();
  timer = window.setInterval(() => void loadLogs({ silent: true }), AUTO_REFRESH_INTERVAL);
}

function stopAutoRefresh() {
  if (timer) {
    window.clearInterval(timer);
    timer = undefined;
  }
}

async function copyLogs() {
  await copyText(logs.value);
  message.success(t("common.copied"));
}

async function clearLogs() {
  const container = props.container;
  if (!container) return;
  clearing.value = true;
  try {
    const result = await clearContainerLogs(container.id, false);
    if (result.cleared) {
      message.success(t("container.logsCleared"));
      await loadLogs({ silent: true });
      return;
    }
    if (result.requires_restart) {
      dialog.warning({
        title: t("container.clearLogs"),
        content: t("container.clearLogsRestartConfirm", { name: container.name }),
        positiveText: t("common.confirm"),
        negativeText: t("common.cancel"),
        onPositiveClick: () => void clearLogsWithRestart(container.id)
      });
    }
  } catch (error) {
    showError(message, error);
  } finally {
    clearing.value = false;
  }
}

async function clearLogsWithRestart(containerId: string) {
  clearing.value = true;
  try {
    await clearContainerLogs(containerId, true);
    message.success(t("container.logsCleared"));
    await loadLogs({ silent: true });
  } catch (error) {
    showError(message, error);
  } finally {
    clearing.value = false;
  }
}
</script>

<style scoped>
.container-log-body {
  display: flex;
  flex-direction: column;
}

.container-log-toolbar {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.container-log-toolbar .n-input-number {
  width: 96px;
}

.container-log-tail-label {
  flex: 0 0 auto;
  color: var(--text-color-2);
  white-space: nowrap;
}

.container-log-switches {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-left: auto;
}

.container-log-switch {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-color-2);
  white-space: nowrap;
}

.container-log-content {
  flex: 0 0 auto;
  height: 56vh;
  max-height: 440px;
  min-height: 260px;
  margin: 0;
  padding: 10px 12px;
  overflow: auto;
  border: 1px solid #2b3240;
  border-radius: 6px;
  background: #11151c;
  color: #d4d4d4;
  font-family: Consolas, Monaco, "Courier New", monospace;
  font-size: 12px;
  line-height: 1.6;
  scrollbar-width: thin;
  scrollbar-color: #4f5d75 #0c0f14;
}

.container-log-content::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}

.container-log-content::-webkit-scrollbar-track {
  background: #0c0f14;
  border-radius: 6px;
}

.container-log-content::-webkit-scrollbar-thumb {
  background: #44506a;
  border: 2px solid #0c0f14;
  border-radius: 6px;
}

.container-log-content::-webkit-scrollbar-thumb:hover {
  background: #5a6b8c;
}

.container-log-content::-webkit-scrollbar-corner {
  background: #0c0f14;
}

.container-log-lines {
  width: max-content;
  min-width: 100%;
}

.container-log-line {
  white-space: pre;
  tab-size: 4;
}

.container-log-content--wrap .container-log-lines {
  width: auto;
  min-width: 0;
}

.container-log-content--wrap .container-log-line {
  white-space: pre-wrap;
  word-break: break-all;
}

.container-log-line--error {
  color: #ff6b6b;
}

.container-log-line--warn {
  color: #ffd166;
}

.container-log-line--success {
  color: #5fd07a;
}

.container-log-line--info {
  color: #6fc1ff;
}

.container-log-line--debug {
  color: #8b94a3;
}

.container-log-line--default {
  color: #d4d4d4;
}

.container-log-line--muted {
  color: #8b94a3;
}
</style>
