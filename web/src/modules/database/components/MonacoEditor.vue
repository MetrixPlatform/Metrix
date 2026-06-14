<template>
  <div ref="containerRef" class="monaco-editor-box" />
</template>

<script setup lang="ts">
import * as monaco from "monaco-editor";
import EditorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";
import "monaco-editor/esm/vs/basic-languages/sql/sql.contribution";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

import { appStore } from "../../../stores/app";

const props = defineProps<{
  modelValue: string;
  suggestions?: string[];
}>();
const emit = defineEmits<{ (event: "update:modelValue", value: string): void }>();

const containerRef = ref<HTMLElement | null>(null);
let editor: monaco.editor.IStandaloneCodeEditor | null = null;
let completionDisposable: monaco.IDisposable | null = null;

function editorTheme() {
  return appStore.dark ? "vs-dark" : "vs";
}

(self as unknown as { MonacoEnvironment: { getWorker: () => Worker } }).MonacoEnvironment = {
  getWorker() {
    return new EditorWorker();
  }
};

onMounted(() => {
  if (!containerRef.value) return;
  completionDisposable = monaco.languages.registerCompletionItemProvider("sql", {
    provideCompletionItems: () => ({
      suggestions: (props.suggestions || []).map((label) => ({
        label,
        kind: monaco.languages.CompletionItemKind.Field,
        insertText: label,
        range: undefined as unknown as monaco.IRange
      }))
    })
  });
  editor = monaco.editor.create(containerRef.value, {
    value: props.modelValue,
    language: "sql",
    theme: editorTheme(),
    minimap: { enabled: false },
    automaticLayout: true,
    scrollBeyondLastLine: false,
    fontSize: 13,
    tabSize: 2
  });
  editor.onDidChangeModelContent(() => emit("update:modelValue", editor?.getValue() || ""));
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
  completionDisposable?.dispose();
  editor?.dispose();
});
</script>
