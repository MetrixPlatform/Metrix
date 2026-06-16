<template>
  <div ref="containerRef" class="code-editor-box" />
</template>

<script setup lang="ts">
import * as monaco from "monaco-editor";
import EditorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";
import CssWorker from "monaco-editor/esm/vs/language/css/css.worker?worker";
import HtmlWorker from "monaco-editor/esm/vs/language/html/html.worker?worker";
import JsonWorker from "monaco-editor/esm/vs/language/json/json.worker?worker";
import TsWorker from "monaco-editor/esm/vs/language/typescript/ts.worker?worker";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

import { appStore } from "../../../stores/app";

const props = withDefaults(
  defineProps<{
    modelValue: string;
    language?: string;
    readOnly?: boolean;
  }>(),
  { language: "plaintext", readOnly: false }
);
const emit = defineEmits<{ (event: "update:modelValue", value: string): void }>();

const containerRef = ref<HTMLElement | null>(null);
let editor: monaco.editor.IStandaloneCodeEditor | null = null;

// Comprehensive worker wiring so JSON/TS/JS/CSS/HTML keep their built-in language
// services offline; everything else falls back to the basic editor worker. Set both
// at import time and on mount so this wins even if another Monaco wrapper loaded first.
function configureWorkers() {
  (self as unknown as { MonacoEnvironment: monaco.Environment }).MonacoEnvironment = {
    getWorker(_workerId: string, label: string) {
      if (label === "json") return new JsonWorker();
      if (label === "css" || label === "scss" || label === "less") return new CssWorker();
      if (label === "html" || label === "handlebars" || label === "razor") return new HtmlWorker();
      if (label === "typescript" || label === "javascript") return new TsWorker();
      return new EditorWorker();
    }
  };
}

configureWorkers();

function editorTheme() {
  return appStore.dark ? "vs-dark" : "vs";
}

onMounted(() => {
  if (!containerRef.value) return;
  configureWorkers();
  editor = monaco.editor.create(containerRef.value, {
    value: props.modelValue,
    language: props.language,
    theme: editorTheme(),
    readOnly: props.readOnly,
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
  () => props.language,
  (language) => {
    const model = editor?.getModel();
    if (model) {
      monaco.editor.setModelLanguage(model, language);
    }
  }
);

watch(
  () => props.readOnly,
  (readOnly) => editor?.updateOptions({ readOnly })
);

watch(
  () => appStore.dark,
  () => monaco.editor.setTheme(editorTheme())
);

onBeforeUnmount(() => {
  editor?.dispose();
  editor = null;
});
</script>

<style scoped>
.code-editor-box {
  width: 100%;
  height: 100%;
  min-height: 200px;
}
</style>
