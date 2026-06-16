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
import "monaco-editor/esm/vs/basic-languages/cpp/cpp.contribution";
import { language as cppLanguage } from "monaco-editor/esm/vs/basic-languages/cpp/cpp.js";
import "monaco-editor/esm/vs/basic-languages/css/css.contribution";
import { language as cssLanguage } from "monaco-editor/esm/vs/basic-languages/css/css.js";
import "monaco-editor/esm/vs/basic-languages/go/go.contribution";
import { language as goLanguage } from "monaco-editor/esm/vs/basic-languages/go/go.js";
import "monaco-editor/esm/vs/basic-languages/html/html.contribution";
import { language as htmlLanguage } from "monaco-editor/esm/vs/basic-languages/html/html.js";
import "monaco-editor/esm/vs/basic-languages/ini/ini.contribution";
import { language as iniLanguage } from "monaco-editor/esm/vs/basic-languages/ini/ini.js";
import "monaco-editor/esm/vs/basic-languages/javascript/javascript.contribution";
import { language as javascriptLanguage } from "monaco-editor/esm/vs/basic-languages/javascript/javascript.js";
import "monaco-editor/esm/vs/basic-languages/python/python.contribution";
import { language as pythonLanguage } from "monaco-editor/esm/vs/basic-languages/python/python.js";
import "monaco-editor/esm/vs/basic-languages/shell/shell.contribution";
import { language as shellLanguage } from "monaco-editor/esm/vs/basic-languages/shell/shell.js";
import "monaco-editor/esm/vs/basic-languages/sql/sql.contribution";
import { language as sqlLanguage } from "monaco-editor/esm/vs/basic-languages/sql/sql.js";
import "monaco-editor/esm/vs/basic-languages/typescript/typescript.contribution";
import { language as typescriptLanguage } from "monaco-editor/esm/vs/basic-languages/typescript/typescript.js";
import "monaco-editor/esm/vs/basic-languages/xml/xml.contribution";
import { language as xmlLanguage } from "monaco-editor/esm/vs/basic-languages/xml/xml.js";
import "monaco-editor/esm/vs/basic-languages/yaml/yaml.contribution";
import { language as yamlLanguage } from "monaco-editor/esm/vs/basic-languages/yaml/yaml.js";
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
let completionDisposables: monaco.IDisposable[] = [];

type BasicLanguageDefinition = {
  keywords?: string[];
  typeKeywords?: string[];
  operators?: string[];
  builtins?: string[];
  builtinFunctions?: string[];
  builtinVariables?: string[];
  tags?: string[];
  attributes?: string[];
};

const COMPLETION_LANGUAGES: Record<string, BasicLanguageDefinition> = {
  python: pythonLanguage,
  go: goLanguage,
  cpp: cppLanguage,
  shell: shellLanguage,
  sql: sqlLanguage,
  yaml: yamlLanguage,
  xml: xmlLanguage,
  ini: iniLanguage,
  javascript: javascriptLanguage,
  typescript: typescriptLanguage,
  css: cssLanguage,
  scss: cssLanguage,
  less: cssLanguage,
  html: htmlLanguage
};

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
  registerCompletionProviders();
  editor = monaco.editor.create(containerRef.value, {
    value: props.modelValue,
    language: props.language,
    theme: editorTheme(),
    readOnly: props.readOnly,
    minimap: { enabled: false },
    automaticLayout: true,
    scrollBeyondLastLine: false,
    suggestOnTriggerCharacters: true,
    quickSuggestions: { other: true, comments: false, strings: false },
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
  completionDisposables.forEach((item) => item.dispose());
  completionDisposables = [];
  editor?.dispose();
  editor = null;
});

function registerCompletionProviders() {
  if (completionDisposables.length > 0) return;
  completionDisposables = Object.entries(COMPLETION_LANGUAGES).map(([language, definition]) =>
    monaco.languages.registerCompletionItemProvider(language, {
      triggerCharacters: [" ", ".", ":", "<", "-", "$", "/"],
      provideCompletionItems: (model, position) => {
        const word = model.getWordUntilPosition(position);
        const range: monaco.IRange = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn
        };
        return { suggestions: completionItems(definition, range) };
      }
    })
  );
}

function completionItems(definition: BasicLanguageDefinition, range: monaco.IRange) {
  const seen = new Set<string>();
  const groups: Array<{ items?: string[]; kind: monaco.languages.CompletionItemKind; sortPrefix: string }> = [
    { items: definition.builtinVariables, kind: monaco.languages.CompletionItemKind.Variable, sortPrefix: "0" },
    { items: definition.builtinFunctions, kind: monaco.languages.CompletionItemKind.Function, sortPrefix: "1" },
    { items: definition.builtins, kind: monaco.languages.CompletionItemKind.Function, sortPrefix: "1" },
    { items: definition.keywords, kind: monaco.languages.CompletionItemKind.Keyword, sortPrefix: "2" },
    { items: definition.typeKeywords, kind: monaco.languages.CompletionItemKind.Keyword, sortPrefix: "2" },
    { items: definition.tags, kind: monaco.languages.CompletionItemKind.Class, sortPrefix: "3" },
    { items: definition.attributes, kind: monaco.languages.CompletionItemKind.Property, sortPrefix: "4" },
    { items: definition.operators, kind: monaco.languages.CompletionItemKind.Operator, sortPrefix: "5" }
  ];
  return groups.flatMap(({ items, kind, sortPrefix }) =>
    (items || [])
      .filter((label) => {
        const text = String(label || "").trim();
        if (!text || seen.has(text)) return false;
        seen.add(text);
        return true;
      })
      .map((label) => ({
        label,
        kind,
        insertText: label,
        range,
        sortText: `${sortPrefix}_${label}`
      }))
  );
}
</script>

<style scoped>
.code-editor-box {
  width: 100%;
  height: 100%;
  min-height: 200px;
}
</style>
