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

const SQL_KEYWORDS = [
  "SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "HAVING", "LIMIT", "OFFSET", "JOIN", "INNER JOIN",
  "LEFT JOIN", "RIGHT JOIN", "FULL JOIN", "ON", "AS", "AND", "OR", "NOT", "IN", "LIKE", "BETWEEN", "IS NULL",
  "IS NOT NULL", "DISTINCT", "COUNT", "SUM", "AVG", "MIN", "MAX", "INSERT INTO", "VALUES", "UPDATE", "SET",
  "DELETE FROM", "CREATE TABLE", "ALTER TABLE", "DROP TABLE", "TRUNCATE TABLE", "CREATE DATABASE", "DROP DATABASE",
  "CREATE INDEX", "PRIMARY KEY", "FOREIGN KEY", "REFERENCES", "DEFAULT", "AUTO_INCREMENT", "UNION", "UNION ALL",
  "CASE", "WHEN", "THEN", "ELSE", "END", "ASC", "DESC", "SHOW TABLES", "SHOW DATABASES", "DESCRIBE", "EXPLAIN"
];

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
    triggerCharacters: [" ", ".", "("],
    provideCompletionItems: (model, position) => {
      const word = model.getWordUntilPosition(position);
      const range: monaco.IRange = {
        startLineNumber: position.lineNumber,
        endLineNumber: position.lineNumber,
        startColumn: word.startColumn,
        endColumn: word.endColumn
      };
      const keywords = SQL_KEYWORDS.map((label) => ({
        label,
        kind: monaco.languages.CompletionItemKind.Keyword,
        insertText: label,
        range
      }));
      const fields = (props.suggestions || []).map((label) => ({
        label,
        kind: monaco.languages.CompletionItemKind.Field,
        insertText: label,
        range
      }));
      return { suggestions: [...keywords, ...fields] };
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
