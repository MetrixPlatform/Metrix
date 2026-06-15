<template>
  <div ref="shellRef" class="monaco-editor-shell">
    <div ref="containerRef" class="monaco-editor-box" />
    <div
      v-if="contextMenu.show"
      class="monaco-context-menu"
      :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }"
      @mousedown.prevent
    >
      <button v-for="item in contextMenuItems" :key="item.key" type="button" @click="runContextMenuAction(item.key)">
        {{ item.label }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import * as monaco from "monaco-editor";
import EditorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";
import "monaco-editor/esm/vs/basic-languages/sql/sql.contribution";
import { language as sqlLanguage } from "monaco-editor/esm/vs/basic-languages/sql/sql.js";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import { appStore } from "../../../stores/app";
import { copyText } from "../../../utils/clipboard";

const props = defineProps<{
  modelValue: string;
  suggestions?: string[];
}>();
const emit = defineEmits<{ (event: "update:modelValue", value: string): void }>();

// Reuse the keyword/function lists Monaco already ships with its SQL grammar
// (monaco-editor/.../sql.js) instead of hand-maintaining a keyword list.
const SQL_KEYWORDS = sqlLanguage.keywords;
const SQL_FUNCTIONS = sqlLanguage.builtinFunctions;

const containerRef = ref<HTMLElement | null>(null);
const shellRef = ref<HTMLElement | null>(null);
const contextMenu = ref({ show: false, x: 0, y: 0 });
let editor: monaco.editor.IStandaloneCodeEditor | null = null;
let completionDisposable: monaco.IDisposable | null = null;

const CONTEXT_MENU_LABELS = {
  "zh-CN": {
    changeAll: "更改所有匹配项",
    cut: "剪切",
    copy: "复制",
    paste: "粘贴",
    selectAll: "全选",
    commandPalette: "命令面板"
  },
  "en-US": {
    changeAll: "Change All Occurrences",
    cut: "Cut",
    copy: "Copy",
    paste: "Paste",
    selectAll: "Select All",
    commandPalette: "Command Palette"
  }
};
type ContextMenuKey = keyof (typeof CONTEXT_MENU_LABELS)["zh-CN"];
const CONTEXT_MENU_KEYS: ContextMenuKey[] = ["changeAll", "cut", "copy", "paste", "selectAll", "commandPalette"];

function editorTheme() {
  return appStore.dark ? "vs-dark" : "vs";
}

function contextMenuLabels() {
  return CONTEXT_MENU_LABELS[appStore.locale as "zh-CN" | "en-US"] || CONTEXT_MENU_LABELS["zh-CN"];
}

const contextMenuItems = computed(() => {
  const labels = contextMenuLabels();
  return CONTEXT_MENU_KEYS.map((key) => ({ key, label: labels[key] }));
});

(self as unknown as { MonacoEnvironment: { getWorker: () => Worker } }).MonacoEnvironment = {
  getWorker() {
    return new EditorWorker();
  }
};

onMounted(() => {
  if (!containerRef.value) return;
  completionDisposable = monaco.languages.registerCompletionItemProvider("sql", {
    triggerCharacters: [" ", ".", "("],
    provideCompletionItems: (model, position) => {
      const word = model.getWordUntilPosition(position);
      const range: monaco.IRange = {
        startLineNumber: position.lineNumber,
        endLineNumber: position.lineNumber,
        startColumn: word.startColumn,
        endColumn: word.endColumn
      };
      const fields = (props.suggestions || []).map((label) => ({
        label,
        kind: monaco.languages.CompletionItemKind.Field,
        insertText: label,
        range,
        sortText: `0_${label}`
      }));
      const functions = SQL_FUNCTIONS.map((label) => ({
        label,
        kind: monaco.languages.CompletionItemKind.Function,
        insertText: label,
        range,
        sortText: `1_${label}`
      }));
      const keywords = SQL_KEYWORDS.map((label) => ({
        label,
        kind: monaco.languages.CompletionItemKind.Keyword,
        insertText: label,
        range,
        sortText: `2_${label}`
      }));
      return { suggestions: [...fields, ...functions, ...keywords] };
    }
  });
  editor = monaco.editor.create(containerRef.value, {
    value: props.modelValue,
    language: "sql",
    theme: editorTheme(),
    minimap: { enabled: false },
    automaticLayout: true,
    scrollBeyondLastLine: false,
    suggestOnTriggerCharacters: true,
    quickSuggestions: { other: true, comments: false, strings: false },
    contextmenu: false,
    fontSize: 13,
    tabSize: 2
  });
  editor.onDidChangeModelContent(() => emit("update:modelValue", editor?.getValue() || ""));
  editor.onContextMenu((event) => openContextMenu(event.event.browserEvent));
  document.addEventListener("click", hideContextMenu);
  document.addEventListener("keydown", hideContextMenu);
});

watch(
  () => props.modelValue,
  (value) => {
    if (editor && editor.getValue() !== value) {
      editor.setValue(value);
    }
  }
);

watch(
  () => appStore.dark,
  () => monaco.editor.setTheme(editorTheme())
);

onBeforeUnmount(() => {
  document.removeEventListener("click", hideContextMenu);
  document.removeEventListener("keydown", hideContextMenu);
  completionDisposable?.dispose();
  editor?.dispose();
});

function openContextMenu(event: MouseEvent) {
  event.preventDefault();
  if (!shellRef.value) return;
  const rect = shellRef.value.getBoundingClientRect();
  contextMenu.value = {
    show: true,
    x: Math.max(0, event.clientX - rect.left),
    y: Math.max(0, event.clientY - rect.top)
  };
}

function hideContextMenu() {
  contextMenu.value.show = false;
}

async function runContextMenuAction(key: ContextMenuKey) {
  hideContextMenu();
  editor?.focus();
  if (!editor) return;
  if (key === "cut") {
    await copySelection();
    deleteSelection();
  } else if (key === "copy") {
    await copySelection();
  } else if (key === "paste") {
    await pasteFromClipboard();
  } else if (key === "selectAll") {
    void editor.getAction("editor.action.selectAll")?.run();
  } else if (key === "changeAll") {
    void editor.getAction("editor.action.changeAll")?.run();
  } else if (key === "commandPalette") {
    void editor.getAction("editor.action.quickCommand")?.run();
  }
}

async function copySelection() {
  if (!editor) return;
  const selection = editor.getSelection();
  const text = selection ? editor.getModel()?.getValueInRange(selection) || "" : "";
  if (text) await copyText(text);
}

function deleteSelection() {
  const selection = editor?.getSelection();
  if (selection && !selection.isEmpty()) {
    editor?.executeEdits("context-menu", [{ range: selection, text: "" }]);
  }
}

async function pasteFromClipboard() {
  const text = await navigator.clipboard?.readText?.();
  if (text) {
    editor?.trigger("context-menu", "type", { text });
  }
}
</script>
