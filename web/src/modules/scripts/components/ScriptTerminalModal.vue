<template>
  <n-modal
    :show="show"
    preset="card"
    class="modal-card script-terminal-modal"
    :title="title"
    @update:show="(value) => emit('update:show', value)"
  >
    <div class="script-terminal-body">
      <div class="script-terminal-form">
        <div class="script-terminal-field">
          <span class="script-terminal-label">{{ t("script.terminalCommand") }}</span>
          <div class="script-terminal-command">
            <n-checkbox v-model:checked="customCommand" :disabled="connected">{{ t("script.terminalCustom") }}</n-checkbox>
            <n-input v-if="customCommand" v-model:value="command" :disabled="connected" placeholder="/bin/sh" />
            <n-select v-else v-model:value="command" :disabled="connected" :options="shellOptions" />
          </div>
        </div>
        <div class="script-terminal-actions">
          <n-button :type="connected ? 'default' : 'primary'" @click="toggle">
            {{ connected ? t("script.terminalDisconnect") : t("script.terminalConnect") }}
          </n-button>
        </div>
      </div>
      <p class="script-terminal-hint">{{ t("script.terminalHint") }}</p>
      <div v-show="connected" ref="terminalRef" class="script-terminal-screen"></div>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import { NButton, NCheckbox, NInput, NModal, NSelect, useMessage } from "naive-ui";
import { FitAddon } from "@xterm/addon-fit";
import { Terminal } from "@xterm/xterm";
import "@xterm/xterm/css/xterm.css";

import { t, translateMessage } from "../../../i18n";
import { authStore } from "../../../stores/auth";
import type { ScriptProject } from "../api";

const props = defineProps<{ show: boolean; project: ScriptProject | null }>();
const emit = defineEmits<{ "update:show": [value: boolean] }>();

const message = useMessage();
const customCommand = ref(false);
const command = ref("/bin/sh");
const connected = ref(false);
const terminalRef = ref<HTMLElement | null>(null);
const shellOptions = [
  { label: "/bin/sh", value: "/bin/sh" },
  { label: "/bin/bash", value: "/bin/bash" },
  { label: "/bin/ash", value: "/bin/ash" }
];
const title = computed(() => t("script.terminalTitle", { name: props.project?.name || "" }));

let term: Terminal | null = null;
let fit: FitAddon | null = null;
let ws: WebSocket | null = null;
let resizeObserver: ResizeObserver | null = null;

watch(
  () => props.show,
  (show) => {
    if (!show) disconnect();
  }
);

onBeforeUnmount(disconnect);

function toggle() {
  if (connected.value) {
    disconnect();
  } else {
    void connect();
  }
}

async function connect() {
  const project = props.project;
  if (!project) return;
  connected.value = true;
  await nextTick();
  if (!terminalRef.value) return;
  term = new Terminal({
    cursorBlink: true,
    fontSize: 13,
    fontFamily: 'Consolas, Monaco, "Courier New", monospace',
    theme: { background: "#000000", foreground: "#d4d4d4" }
  });
  fit = new FitAddon();
  term.loadAddon(fit);
  term.open(terminalRef.value);
  fit.fit();
  const params = new URLSearchParams({
    token: authStore.token,
    cmd: command.value || "/bin/sh",
    cols: String(term.cols),
    rows: String(term.rows)
  });
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/api/scripts/${encodeURIComponent(project.id)}/terminal?${params.toString()}`);
  ws.binaryType = "arraybuffer";
  ws.onopen = () => {
    term?.focus();
    sendResize();
  };
  ws.onmessage = (event) => {
    if (typeof event.data === "string") {
      try {
        const payload = JSON.parse(event.data) as { type?: string; code?: string };
        if (payload.type === "error" && payload.code) {
          message.error(translateMessage(payload.code, {}, t("api.requestFailed")));
        }
      } catch {
        /* ignore non-JSON control messages */
      }
      return;
    }
    term?.write(new Uint8Array(event.data as ArrayBuffer));
  };
  ws.onclose = () => disconnect();
  ws.onerror = () => disconnect();
  term.onData((data) => {
    if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: "input", data }));
  });
  resizeObserver = new ResizeObserver(() => {
    fit?.fit();
    sendResize();
  });
  resizeObserver.observe(terminalRef.value);
}

function sendResize() {
  if (ws?.readyState === WebSocket.OPEN && term) {
    ws.send(JSON.stringify({ type: "resize", cols: term.cols, rows: term.rows }));
  }
}

function disconnect() {
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
  if (ws) {
    ws.onclose = null;
    ws.onerror = null;
    try {
      ws.close();
    } catch {
      /* ignore */
    }
    ws = null;
  }
  if (term) {
    term.dispose();
    term = null;
  }
  fit = null;
  connected.value = false;
}
</script>

<style scoped>
.script-terminal-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.script-terminal-form {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.script-terminal-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.script-terminal-label {
  color: var(--text-color-2);
  font-size: 13px;
}

.script-terminal-command {
  display: flex;
  align-items: center;
  gap: 10px;
}

.script-terminal-command .n-input,
.script-terminal-command .n-select {
  flex: 1;
}

.script-terminal-hint {
  margin: 0;
  color: var(--text-color-3);
  font-size: 12px;
}

.script-terminal-screen {
  height: clamp(160px, calc(76vh - 320px), 320px);
  padding: 8px;
  border-radius: 6px;
  background: #000000;
  overflow: hidden;
}
</style>
