<template>
  <section class="work-card api-docs-page">
    <div class="toolbar api-docs-toolbar">
      <div class="api-docs-filter-row">
        <n-input v-model:value="keyword" class="filter-keyword" :placeholder="t('apiDocs.searchPlaceholder')" clearable />
        <n-button :loading="loading" @click="loadDocument">
          <template #icon><n-icon :component="ArrowClockwise20Regular" /></template>
          {{ t("common.refresh") }}
        </n-button>
      </div>
      <div class="toolbar-group api-docs-actions">
        <n-button :disabled="!documentText" @click="copyDocument">
          <template #icon><n-icon :component="Copy20Regular" /></template>
          {{ t("common.copy") }}
        </n-button>
        <n-button :disabled="!documentText" @click="downloadDocument">
          <template #icon><n-icon :component="ArrowDownload20Regular" /></template>
          {{ t("common.download") }}
        </n-button>
      </div>
    </div>

    <n-spin :show="loading" class="api-docs-spin">
      <n-empty v-if="!document && !loading" :description="t('apiDocs.empty')" />
      <div v-else-if="document" class="api-docs-layout">
        <aside class="api-docs-sidebar">
          <div class="api-docs-title">
            <strong>{{ document.info.title }}</strong>
            <span>{{ document.openapi }} · {{ document.info.version }}</span>
          </div>
          <button
            v-for="group in groups"
            :key="group.name"
            class="api-docs-tag"
            :class="{ active: activeTag === group.name }"
            type="button"
            @click="activeTag = group.name"
          >
            <span>{{ group.name }}</span>
            <strong>{{ group.operations.length }}</strong>
          </button>
        </aside>

        <main class="api-docs-content">
          <n-empty v-if="visibleGroups.length === 0" :description="t('apiDocs.noMatch')" />
          <section v-for="group in visibleGroups" :key="group.name" class="api-docs-group">
            <h2>{{ group.name }}</h2>
            <article v-for="operation in group.operations" :key="operation.key" class="api-operation">
              <div class="api-operation-head">
                <n-tag :type="methodTagType(operation.method)" size="small" round>{{ operation.method.toUpperCase() }}</n-tag>
                <code>{{ operation.path }}</code>
              </div>
              <h3>{{ operationTitle(operation) }}</h3>
              <p v-if="operation.operation.description" class="api-operation-description">{{ operation.operation.description }}</p>
              <dl class="api-operation-meta">
                <div>
                  <dt>{{ t("apiDocs.operationId") }}</dt>
                  <dd>{{ operation.operation.operationId || t("common.none") }}</dd>
                </div>
                <div>
                  <dt>{{ t("apiDocs.requestBody") }}</dt>
                  <dd>{{ requestBodyText(operation.operation) }}</dd>
                </div>
              </dl>
              <div v-if="operation.operation.parameters?.length" class="api-detail-block">
                <strong>{{ t("apiDocs.parameters") }}</strong>
                <n-data-table size="small" :columns="parameterColumns" :data="operation.operation.parameters" :pagination="false" />
              </div>
              <div v-if="operation.operation.responses" class="api-detail-block">
                <strong>{{ t("apiDocs.responses") }}</strong>
                <div class="api-response-list">
                  <span v-for="response in responseItems(operation.operation)" :key="response.code">
                    <code>{{ response.code }}</code>
                    {{ response.description || t("common.none") }}
                  </span>
                </div>
              </div>
            </article>
          </section>
        </main>
      </div>
    </n-spin>
  </section>
</template>

<script setup lang="ts">
import { ArrowClockwise20Regular, ArrowDownload20Regular, Copy20Regular } from "@vicons/fluent";
import { computed, h, onMounted, ref } from "vue";
import { NButton, NDataTable, NEmpty, NIcon, NInput, NSpin, NTag, useMessage } from "naive-ui";
import type { DataTableColumns } from "naive-ui";

import { getOpenApiDocument, type OpenApiDocument, type OpenApiOperation, type OpenApiParameter } from "../api/openapi";
import { t } from "../i18n";
import { saveBlob } from "../utils/download";
import { showError } from "../utils/message";

interface OperationEntry {
  key: string;
  path: string;
  method: string;
  operation: OpenApiOperation;
}

interface OperationGroup {
  name: string;
  operations: OperationEntry[];
}

const message = useMessage();
const loading = ref(false);
const document = ref<OpenApiDocument | null>(null);
const keyword = ref("");
const activeTag = ref("");
const documentText = computed(() => (document.value ? JSON.stringify(document.value, null, 2) : ""));
const groups = computed(() => groupOperations(document.value));
const visibleGroups = computed(() => {
  const normalizedKeyword = keyword.value.trim().toLowerCase();
  return groups.value
    .filter((group) => !activeTag.value || group.name === activeTag.value)
    .map((group) => ({
      ...group,
      operations: normalizedKeyword ? group.operations.filter((operation) => operationMatches(operation, normalizedKeyword)) : group.operations
    }))
    .filter((group) => group.operations.length > 0);
});

const parameterColumns = computed<DataTableColumns<OpenApiParameter>>(() => [
  { title: t("apiDocs.parameterName"), key: "name", width: 160 },
  { title: t("apiDocs.parameterIn"), key: "in", width: 100 },
  {
    title: t("apiDocs.required"),
    key: "required",
    width: 90,
    render: (row) => h(NTag, { size: "small", type: row.required ? "warning" : "default" }, { default: () => (row.required ? t("common.yes") : t("common.no")) })
  },
  { title: t("field.description"), key: "description", minWidth: 220, render: (row) => row.description || schemaText(row.schema) || t("common.none") }
]);

onMounted(async () => {
  await loadDocument();
});

async function loadDocument() {
  loading.value = true;
  try {
    document.value = await getOpenApiDocument();
    activeTag.value = groups.value[0]?.name || "";
  } catch (error) {
    showError(message, error);
  } finally {
    loading.value = false;
  }
}

async function copyDocument() {
  try {
    await navigator.clipboard.writeText(documentText.value);
    message.success(t("common.copied"));
  } catch {
    message.error(t("message.operationFailed"));
  }
}

function downloadDocument() {
  saveBlob(new Blob([documentText.value], { type: "application/json;charset=utf-8" }), "openapi.json");
}

function groupOperations(doc: OpenApiDocument | null): OperationGroup[] {
  if (!doc) return [];
  const groupsByName = new Map<string, OperationEntry[]>();
  for (const [path, methods] of Object.entries(doc.paths)) {
    for (const [method, operation] of Object.entries(methods)) {
      if (!["get", "post", "put", "delete", "patch"].includes(method)) continue;
      const tag = operation.tags?.[0] || t("apiDocs.defaultTag");
      groupsByName.set(tag, [...(groupsByName.get(tag) || []), { key: `${method}:${path}`, path, method, operation }]);
    }
  }
  return Array.from(groupsByName.entries()).map(([name, operations]) => ({ name, operations }));
}

function operationMatches(entry: OperationEntry, normalizedKeyword: string) {
  return [entry.path, entry.method, entry.operation.summary, entry.operation.description, entry.operation.operationId, ...(entry.operation.tags || [])]
    .filter(Boolean)
    .some((value) => String(value).toLowerCase().includes(normalizedKeyword));
}

function operationTitle(entry: OperationEntry) {
  return entry.operation.summary || entry.operation.operationId || entry.path;
}

function requestBodyText(operation: OpenApiOperation) {
  const contentTypes = Object.keys(operation.requestBody?.content || {});
  if (contentTypes.length === 0) {
    return t("common.none");
  }
  return `${operation.requestBody?.required ? t("apiDocs.required") : t("apiDocs.optional")} · ${contentTypes.join(t("common.listSeparator"))}`;
}

function responseItems(operation: OpenApiOperation) {
  return Object.entries(operation.responses || {}).map(([code, response]) => ({ code, description: response.description || "" }));
}

function methodTagType(method: string) {
  const types: Record<string, "success" | "info" | "warning" | "error" | "default"> = {
    get: "success",
    post: "info",
    put: "warning",
    patch: "warning",
    delete: "error"
  };
  return types[method] || "default";
}

function schemaText(schema: unknown) {
  if (!schema || typeof schema !== "object") {
    return "";
  }
  const schemaObject = schema as { type?: string; format?: string };
  return [schemaObject.type, schemaObject.format].filter(Boolean).join("/");
}
</script>
