<template>
  <div class="script-terminal">
    <div class="script-terminal-toolbar">
      <n-button size="small" :type="connected ? 'default' : 'primary'" :disabled="!project" @click="toggle">
        {{ connected ? t("script.terminalDisconnect") : t("script.terminalConnect") }}
      </n-button>
      <n-checkbox v-model:checked="customCommand" :disabled="connected" size="small">{{ t("script.terminalCustom") }}</n-checkbox>
      <n-input
        v-if="customCommand"
        v-model:value="command"
        :disabled="connected"
        size="small"
        placeholder="/bin/bash"
        class="script-terminal-command-input"
      />
    </div>
    <div v-show="connected" ref="terminalRef" class="script-terminal-screen"></div>
    <div v-if="!connected" class="script-terminal-idle">{{ t("script.terminalIdle") }}</div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { NButton, NCheckbox, NInput, useMessage } from "naive-ui";
import { FitAddon } from "@xterm/addon-fit";
import { Terminal } from "@xterm/xterm";
import "@xterm/xterm/css/xterm.css";

import { t, translateMessage } from "../../../i18n";
import { authStore } from "../../../stores/auth";
import type { ScriptProject } from "../api";

const props = withDefaults(
  defineProps<{ project: ScriptProject | null; active: boolean; autoConnect?: boolean }>(),
  { autoConnect: false }
);

const message = useMessage();
const customCommand = ref(false);
const command = ref("");
const connected = ref(false);
const terminalRef = ref<HTMLElement | null>(null);

let term: Terminal | null = null;
let fit: FitAddon | null = null;
let ws: WebSocket | null = null;
let resizeObserver: ResizeObserver | null = null;
let autoConnected = false;

watch(
  () => props.active,
  (active) => {
    if (!active) return;
    if (connected.value) {
      nextTick(() => fit?.fit());
    } else if (!autoConnected && props.project) {
      autoConnected = true;
      void connect();
    }
  }
);

watch(
  () => props.project?.id,
  () => {
    autoConnected = false;
    disconnect();
  }
);

// Refit on window resize; the workbench also dispatches a resize event when the panel expands.
function handleWindowResize() {
  if (props.active && connected.value) {
    fit?.fit();
    sendResize();
  }
}

// The default first terminal connects as soon as the workbench mounts, without
// waiting for the tab to be focused; extra terminals still connect on activation.
onMounted(() => {
  window.addEventListener("resize", handleWindowResize);
  if (props.autoConnect && props.project && !autoConnected) {
    autoConnected = true;
    void connect();
  }
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleWindowResize);
  disconnect();
});

function toggle() {
  if (connected.value) {
    disconnect();
  } else {
    autoConnected = true;
    void connect();
  }
}

async function connect() {
  const project = props.project;
  if (!project || connected.value) return;
  connected.value = true;
  await nextTick();
  if (!terminalRef.value) {
    connected.value = false;
    return;
  }
  term = new Terminal({
    cursorBlink: true,
    fontSize: 13,
    fontFamily: 'Consolas, Monaco, "Courier New", monospace',
    scrollback: 2000,
    theme: { background: "#000000", foreground: "#d4d4d4" }
  });
  fit = new FitAddon();
  term.loadAddon(fit);
  term.open(terminalRef.value);
  fit.fit();
  const params = new URLSearchParams({
    token: authStore.token,
    cmd: customCommand.value ? command.value : "",
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
    if (!props.active) return;
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
.script-terminal {
  display: flex;
  flex-direction: column;
  gap: 8px;
  height: 100%;
  padding-bottom: 10px;
  overflow: hidden;
}

.script-terminal-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.script-terminal-command-input {
  max-width: 240px;
}

.script-terminal-screen {
  flex: 1;
  min-height: 0;
  padding: 8px;
  border-radius: 6px;
  background: #000000;
  overflow: hidden;
}

.script-terminal-idle {
  color: var(--text-color-3);
  font-size: 12px;
  padding: 8px 0;
}
</style>
