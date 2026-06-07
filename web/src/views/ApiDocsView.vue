<template>
  <section class="work-card api-docs-page">
    <div class="toolbar api-docs-toolbar">
      <div class="api-docs-filter-row">
        <n-input v-model:value="keyword" class="filter-keyword" :placeholder="t('apiDocs.searchPlaceholder')" clearable />
        <n-input
          v-model:value="apiToken"
          class="filter-keyword"
          type="password"
          show-password-on="click"
          :placeholder="t('apiDocs.testTokenPlaceholder')"
        />
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
                <n-button class="api-operation-test-button" size="small" secondary @click="openTest(operation)">
                  <template #icon><n-icon :component="Play20Regular" /></template>
                  {{ t("common.test") }}
                </n-button>
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

    <n-modal v-model:show="showTestModal" preset="card" class="api-test-modal" :title="t('apiDocs.test')">
      <div v-if="selectedOperation" class="api-test-content">
        <div class="api-test-endpoint">
          <n-tag :type="methodTagType(selectedOperation.method)" size="small" round>{{ selectedOperation.method.toUpperCase() }}</n-tag>
          <code>{{ selectedOperation.path }}</code>
        </div>
        <n-form class="form-stack inline-form" label-placement="left" label-width="110">
          <n-form-item
            v-for="parameter in testParameters"
            :key="parameterKey(parameter)"
            :label="parameterLabel(parameter)"
          >
            <n-input
              :value="testParams[parameterKey(parameter)]"
              :placeholder="parameter.description || schemaText(parameter.schema) || parameter.name"
              @update:value="(value) => setTestParam(parameter, value)"
            />
          </n-form-item>
          <n-form-item v-if="hasTestRequestBody" :label="t('field.requestBody')">
            <n-input v-model:value="testBody" type="textarea" :placeholder="t('apiDocs.bodyPlaceholder')" :autosize="{ minRows: 6, maxRows: 10 }" />
          </n-form-item>
        </n-form>
        <div class="form-actions">
          <n-button @click="showTestModal = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" :loading="testing" @click="sendTestRequest">
            <template #icon><n-icon :component="Send20Regular" /></template>
            {{ t("common.test") }}
          </n-button>
        </div>
        <div v-if="testStatus !== null" class="api-test-result">
          <div class="api-test-result-head">
            <strong>{{ t("apiDocs.testResponse") }}</strong>
            <span>{{ t("apiDocs.httpStatus") }} <code>{{ testStatus }}</code></span>
          </div>
          <pre>{{ testResponse || t("common.none") }}</pre>
        </div>
      </div>
    </n-modal>
  </section>
</template>

<script setup lang="ts">
import { ArrowClockwise20Regular, ArrowDownload20Regular, Copy20Regular, Play20Regular, Send20Regular } from "@vicons/fluent";
import { computed, h, onMounted, reactive, ref } from "vue";
import { NButton, NDataTable, NEmpty, NForm, NFormItem, NIcon, NInput, NModal, NSpin, NTag, useMessage } from "naive-ui";
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

const TEST_METHODS_WITH_BODY = new Set(["post", "put", "patch", "delete"]);

const message = useMessage();
const loading = ref(false);
const testing = ref(false);
const document = ref<OpenApiDocument | null>(null);
const keyword = ref("");
const apiToken = ref("");
const activeTag = ref("");
const selectedOperation = ref<OperationEntry | null>(null);
const showTestModal = ref(false);
const testParams = reactive<Record<string, string>>({});
const testBody = ref("");
const testStatus = ref<number | null>(null);
const testResponse = ref("");
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
const testParameters = computed(() =>
  (selectedOperation.value?.operation.parameters || []).filter((parameter) => parameter.in === "path" || parameter.in === "query")
);
const hasTestRequestBody = computed(() => {
  const operation = selectedOperation.value;
  return Boolean(operation && TEST_METHODS_WITH_BODY.has(operation.method) && Object.keys(operation.operation.requestBody?.content || {}).length > 0);
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

function openTest(operation: OperationEntry) {
  selectedOperation.value = operation;
  clearTestParams();
  for (const parameter of testParameters.value) {
    testParams[parameterKey(parameter)] = "";
  }
  testBody.value = hasRequestBody(operation) ? "{}" : "";
  testStatus.value = null;
  testResponse.value = "";
  showTestModal.value = true;
}

async function sendTestRequest() {
  const operation = selectedOperation.value;
  const token = apiToken.value.trim();
  if (!operation) return;
  if (!token) {
    message.error(t("apiDocs.tokenRequired"));
    return;
  }
  let url = "";
  let body: string | undefined;
  try {
    url = buildRequestUrl(operation);
    body = buildRequestBody();
  } catch (error) {
    message.error(error instanceof Error ? error.message : t("message.operationFailed"));
    return;
  }

  testing.value = true;
  try {
    const headers = new Headers({ Authorization: `Bearer ${token}`, Accept: "application/json" });
    if (body !== undefined) {
      headers.set("Content-Type", "application/json");
    }
    const response = await fetch(url, { method: operation.method.toUpperCase(), headers, body });
    testStatus.value = response.status;
    testResponse.value = await responseText(response);
    message.success(t("apiDocs.testSuccess"));
  } catch (error) {
    showError(message, error);
  } finally {
    testing.value = false;
  }
}

function buildRequestUrl(operation: OperationEntry) {
  let path = operation.path;
  const query = new URLSearchParams();
  for (const parameter of testParameters.value) {
    const key = parameterKey(parameter);
    const value = (testParams[key] || "").trim();
    if (parameter.in === "path") {
      if (!value) {
        throw new Error(t("apiDocs.pathParamRequired", { name: parameter.name }));
      }
      path = path.replace(`{${parameter.name}}`, encodeURIComponent(value));
    } else if (parameter.in === "query" && value) {
      query.set(parameter.name, value);
    }
  }
  return query.size ? `${path}?${query}` : path;
}

function buildRequestBody() {
  if (!hasTestRequestBody.value) {
    return undefined;
  }
  const body = testBody.value.trim();
  if (!body) {
    return undefined;
  }
  try {
    JSON.parse(body);
  } catch {
    throw new Error(t("apiDocs.invalidJson"));
  }
  return body;
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

function parameterKey(parameter: OpenApiParameter) {
  return `${parameter.in}:${parameter.name}`;
}

function parameterLabel(parameter: OpenApiParameter) {
  return `${parameter.name}${parameter.required ? " *" : ""}`;
}

function setTestParam(parameter: OpenApiParameter, value: string) {
  testParams[parameterKey(parameter)] = value;
}

function clearTestParams() {
  for (const key of Object.keys(testParams)) {
    delete testParams[key];
  }
}

function hasRequestBody(operation: OperationEntry) {
  return TEST_METHODS_WITH_BODY.has(operation.method) && Object.keys(operation.operation.requestBody?.content || {}).length > 0;
}

async function responseText(response: Response) {
  const text = await response.text();
  if (!text) {
    return "";
  }
  try {
    return JSON.stringify(JSON.parse(text), null, 2);
  } catch {
    return text;
  }
}

function schemaText(schema: unknown) {
  if (!schema || typeof schema !== "object") {
    return "";
  }
  const schemaObject = schema as { type?: string; format?: string };
  return [schemaObject.type, schemaObject.format].filter(Boolean).join("/");
}
</script>
