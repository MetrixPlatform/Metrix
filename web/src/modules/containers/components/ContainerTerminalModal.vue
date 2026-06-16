<template>
  <n-modal :show="show" preset="card" class="modal-card container-terminal-modal" :title="title" @update:show="(value) => emit('update:show', value)">
    <div class="container-terminal-body">
      <div class="container-terminal-form">
        <div class="container-terminal-field">
          <span class="container-terminal-label">{{ t("container.terminalUser") }}</span>
          <n-input v-model:value="execUser" :disabled="connected" placeholder="root" />
        </div>
        <div class="container-terminal-field">
          <span class="container-terminal-label container-terminal-required">{{ t("container.terminalCommand") }}</span>
          <div class="container-terminal-command">
            <n-checkbox v-model:checked="customCommand" :disabled="connected">{{ t("container.terminalCustom") }}</n-checkbox>
            <n-input v-if="customCommand" v-model:value="command" :disabled="connected" placeholder="/bin/sh" />
            <n-select v-else v-model:value="command" :disabled="connected" :options="shellOptions" />
          </div>
        </div>
        <div class="container-terminal-actions">
          <n-button :type="connected ? 'default' : 'primary'" @click="toggle">
            {{ connected ? t("container.terminalDisconnect") : t("container.terminalConnect") }}
          </n-button>
        </div>
      </div>
      <div v-show="connected" ref="terminalRef" class="container-terminal-screen"></div>
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
import type { ContainerItem } from "../api";

const props = defineProps<{ show: boolean; container: ContainerItem | null }>();
const emit = defineEmits<{ "update:show": [value: boolean] }>();

const message = useMessage();
const execUser = ref("");
const customCommand = ref(false);
const command = ref("/bin/sh");
const connected = ref(false);
const terminalRef = ref<HTMLElement | null>(null);
const shellOptions = [
  { label: "/bin/sh", value: "/bin/sh" },
  { label: "/bin/bash", value: "/bin/bash" },
  { label: "/bin/ash", value: "/bin/ash" }
];
const title = computed(() => t("container.terminalTitle", { name: props.container?.name || "" }));

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
  const container = props.container;
  if (!container) return;
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
    user: execUser.value,
    cmd: command.value || "/bin/sh",
    cols: String(term.cols),
    rows: String(term.rows)
  });
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/api/container-instances/${encodeURIComponent(container.id)}/exec?${params.toString()}`);
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
.container-terminal-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.container-terminal-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.container-terminal-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.container-terminal-label {
  color: var(--text-color-2);
  font-size: 13px;
}

.container-terminal-required::before {
  content: "* ";
  color: var(--error-color, #d03050);
}

.container-terminal-command {
  display: flex;
  align-items: center;
  gap: 10px;
}

.container-terminal-command .n-input,
.container-terminal-command .n-select {
  flex: 1;
}

.container-terminal-screen {
  height: 380px;
  padding: 8px;
  border-radius: 6px;
  background: #000000;
  overflow: hidden;
}
</style>
