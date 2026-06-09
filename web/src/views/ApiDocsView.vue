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
      <n-empty v-if="!openApiDocument && !loading" :description="t('apiDocs.empty')" />
      <div v-else-if="openApiDocument" class="api-docs-layout">
        <aside class="api-docs-sidebar">
          <div class="api-docs-title">
            <strong>{{ openApiDocument.info.title }}</strong>
            <span>{{ openApiDocument.openapi }} · {{ openApiDocument.info.version }}</span>
          </div>
          <button
            v-for="group in groups"
            :key="group.name"
            class="api-docs-tag"
            :class="{ active: activeTag === group.name }"
            type="button"
            @click="activeTag = group.name"
          >
            <span>{{ group.label }}</span>
            <strong>{{ group.operations.length }}</strong>
          </button>
        </aside>

        <main class="api-docs-content">
          <n-empty v-if="visibleGroups.length === 0" :description="t('apiDocs.noMatch')" />
          <section v-for="group in visibleGroups" :key="group.name" class="api-docs-group">
            <h2>{{ group.label }}</h2>
            <article v-for="operation in group.operations" :key="operation.key" class="api-operation">
              <div class="api-operation-head">
                <n-tag :type="methodTagType(operation.method)" size="small" round>{{ operation.method.toUpperCase() }}</n-tag>
                <code>{{ operation.path }}</code>
                <div class="api-operation-actions">
                  <n-button size="small" secondary @click="openDetail(operation)">{{ t("apiDocs.detail") }}</n-button>
                  <n-button size="small" secondary @click="openTest(operation)">
                    <template #icon><n-icon :component="Play20Regular" /></template>
                    {{ t("common.test") }}
                  </n-button>
                </div>
              </div>
              <h3>{{ operationTitle(operation) }}</h3>
              <p v-if="operationDescription(operation)" class="api-operation-description">{{ operationDescription(operation) }}</p>
              <dl class="api-operation-meta">
                <div>
                  <dt>{{ t("apiDocs.operationId") }}</dt>
                  <dd>{{ operation.operation.operationId || t("common.none") }}</dd>
                </div>
                <div>
                  <dt>{{ t("apiDocs.requestBody") }}</dt>
                  <dd>{{ requestBodyText(operation.operation) }}</dd>
                </div>
                <div>
                  <dt>{{ t("apiDocs.parameters") }}</dt>
                  <dd>{{ operation.operation.parameters?.length || 0 }}</dd>
                </div>
                <div>
                  <dt>{{ t("apiDocs.responses") }}</dt>
                  <dd>{{ Object.keys(operation.operation.responses || {}).length }}</dd>
                </div>
              </dl>
            </article>
          </section>
        </main>
      </div>
    </n-spin>

    <n-modal v-model:show="showDetailModal" preset="card" class="api-detail-modal" :title="t('apiDocs.detail')">
      <div v-if="selectedOperation" class="api-detail-content">
        <div class="api-test-endpoint">
          <n-tag :type="methodTagType(selectedOperation.method)" size="small" round>{{ selectedOperation.method.toUpperCase() }}</n-tag>
          <code>{{ selectedOperation.path }}</code>
        </div>
        <h3>{{ operationTitle(selectedOperation) }}</h3>
        <p v-if="operationDescription(selectedOperation)" class="api-operation-description">{{ operationDescription(selectedOperation) }}</p>

        <section class="api-detail-section">
          <h4>{{ t("apiDocs.operationId") }}</h4>
          <code>{{ selectedOperation.operation.operationId || t("common.none") }}</code>
        </section>

        <section class="api-detail-section">
          <h4>{{ t("apiDocs.parameters") }}</h4>
          <n-empty v-if="!selectedOperation.operation.parameters?.length" class="api-detail-empty" size="small" :description="t('apiDocs.noParameters')" />
          <n-data-table
            v-else
            size="small"
            :columns="parameterColumns"
            :data="selectedOperation.operation.parameters"
            :pagination="false"
            :scroll-x="parameterTableScrollX"
            @unstable-column-resize="handleParameterColumnResize"
          />
        </section>

        <section class="api-detail-section">
          <h4>{{ t("apiDocs.requestBody") }}</h4>
          <n-empty v-if="!hasRequestBody(selectedOperation)" class="api-detail-empty" size="small" :description="t('apiDocs.noRequestBody')" />
          <div v-else class="api-schema-card">
            <div class="api-schema-head">
              <span>{{ t("apiDocs.contentType") }}{{ t("common.labelSeparator") }}{{ requestContentType(selectedOperation) }}</span>
              <n-tag size="small" :type="selectedOperation.operation.requestBody?.required ? 'warning' : 'default'">
                {{ selectedOperation.operation.requestBody?.required ? t("apiDocs.required") : t("apiDocs.optional") }}
              </n-tag>
            </div>
            <n-data-table
              v-if="requestBodyFields(selectedOperation).length"
              size="small"
              :columns="schemaFieldColumns"
              :data="requestBodyFields(selectedOperation)"
              :pagination="false"
              :scroll-x="schemaFieldTableScrollX"
              @unstable-column-resize="handleSchemaFieldColumnResize"
            />
            <strong>{{ t("apiDocs.requestExample") }}</strong>
            <pre class="api-json-block">{{ requestBodyExampleText(selectedOperation) }}</pre>
          </div>
        </section>

        <section class="api-detail-section">
          <h4>{{ t("apiDocs.responses") }}</h4>
          <div class="api-response-detail-list">
            <article v-for="response in responseItems(selectedOperation)" :key="response.code" class="api-response-card">
              <div class="api-schema-head">
                <strong>{{ t("apiDocs.statusCode") }}{{ t("common.labelSeparator") }}<code>{{ response.code }}</code></strong>
                <span>{{ response.description }}</span>
              </div>
              <p class="api-operation-description">{{ response.explanation }}</p>
              <n-data-table
                v-if="response.fields.length"
                size="small"
                :columns="schemaFieldColumns"
                :data="response.fields"
                :pagination="false"
                :scroll-x="schemaFieldTableScrollX"
                @unstable-column-resize="handleSchemaFieldColumnResize"
              />
              <template v-if="response.example">
                <strong>{{ t("apiDocs.responseExample") }}</strong>
                <pre class="api-json-block">{{ response.example }}</pre>
              </template>
            </article>
          </div>
        </section>
      </div>
    </n-modal>

    <n-modal v-model:show="showTestModal" preset="card" class="api-test-modal" :title="t('apiDocs.test')">
      <div v-if="selectedOperation" class="api-test-content">
        <div class="api-test-endpoint">
          <n-tag :type="methodTagType(selectedOperation.method)" size="small" round>{{ selectedOperation.method.toUpperCase() }}</n-tag>
          <code>{{ selectedOperation.path }}</code>
        </div>
        <n-form class="form-stack inline-form" label-placement="left" label-width="auto">
          <n-form-item
            v-for="parameter in testParameters"
            :key="parameterKey(parameter)"
            :label="parameterLabel(parameter)"
          >
            <n-input
              :value="testParams[parameterKey(parameter)]"
              :placeholder="parameterDescription(parameter)"
              @update:value="(value) => setTestParam(parameter, value)"
            />
          </n-form-item>
          <n-form-item v-if="hasTestRequestBody" :label="t('field.requestBody')">
            <n-input
              v-model:value="testBody"
              type="textarea"
              :placeholder="t('apiDocs.bodyPlaceholder')"
              :autosize="{ minRows: 8, maxRows: 14 }"
            />
          </n-form-item>
        </n-form>
        <div class="form-actions">
          <n-button @click="showTestModal = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" :loading="testing" @click="sendTestRequest">
            <template #icon><n-icon :component="Send20Regular" /></template>
            {{ t("common.test") }}
          </n-button>
        </div>
        <div v-if="testRequest || testResponse" class="api-test-result-grid">
          <div v-if="testRequest" class="api-test-result">
            <div class="api-test-result-head">
              <strong>{{ t("apiDocs.testRequest") }}</strong>
            </div>
            <pre>{{ testRequest }}</pre>
          </div>
          <div v-if="testResponse" class="api-test-result">
            <div class="api-test-result-head">
              <strong>{{ t("apiDocs.testResponse") }}</strong>
              <span v-if="testStatus !== null">{{ t("apiDocs.httpStatus") }} <code>{{ testStatus }}</code></span>
            </div>
            <pre>{{ testResponse }}</pre>
          </div>
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

import {
  getOpenApiDocument,
  type OpenApiDocument,
  type OpenApiMediaType,
  type OpenApiOperation,
  type OpenApiParameter,
  type OpenApiResponse,
  type OpenApiSchema
} from "../api/openapi";
import { t } from "../i18n";
import { openApiText } from "../i18n/openapi";
import { saveBlob } from "../utils/download";
import { showError } from "../utils/message";
import { sumColumnWidths, updateColumnWidth, withResizableColumns } from "../utils/table";

interface OperationEntry {
  key: string;
  path: string;
  method: string;
  operation: OpenApiOperation;
}

interface OperationGroup {
  name: string;
  label: string;
  operations: OperationEntry[];
}

interface SchemaField {
  name: string;
  required: boolean;
  type: string;
  description: string;
}

interface ResponseDetail {
  code: string;
  description: string;
  explanation: string;
  fields: SchemaField[];
  example: string;
}

const TEST_METHODS_WITH_BODY = new Set(["post", "put", "patch", "delete"]);
const HTTP_METHODS = new Set(["get", "post", "put", "delete", "patch"]);
const JSON_TYPE = "application/json";

const message = useMessage();
const loading = ref(false);
const testing = ref(false);
const openApiDocument = ref<OpenApiDocument | null>(null);
const keyword = ref("");
const apiToken = ref("");
const activeTag = ref("");
const selectedOperation = ref<OperationEntry | null>(null);
const showDetailModal = ref(false);
const showTestModal = ref(false);
const testParams = reactive<Record<string, string>>({});
const testBody = ref("");
const testStatus = ref<number | null>(null);
const testRequest = ref("");
const testResponse = ref("");
const parameterColumnWidths = reactive<Record<string, number>>({
  name: 150,
  in: 90,
  required: 90,
  schema: 140,
  description: 280
});
const schemaFieldColumnWidths = reactive<Record<string, number>>({
  name: 180,
  required: 90,
  type: 150,
  description: 280
});
const parameterColumnWidthKeys: Record<string, string> = {
  name: "name",
  in: "in",
  required: "required",
  schema: "schema",
  description: "description"
};
const schemaFieldColumnWidthKeys: Record<string, string> = {
  name: "name",
  required: "required",
  type: "type",
  description: "description"
};
const documentText = computed(() => (openApiDocument.value ? JSON.stringify(openApiDocument.value, null, 2) : ""));
const parameterTableScrollX = computed(() => sumColumnWidths(parameterColumnWidths));
const schemaFieldTableScrollX = computed(() => sumColumnWidths(schemaFieldColumnWidths));
const groups = computed(() => groupOperations(openApiDocument.value));
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
const hasTestRequestBody = computed(() => Boolean(selectedOperation.value && hasRequestBody(selectedOperation.value)));

const parameterColumns = computed<DataTableColumns<OpenApiParameter>>(() =>
  withResizableColumns([
    { title: t("apiDocs.parameterName"), key: "name", width: parameterColumnWidths.name },
    { title: t("apiDocs.parameterIn"), key: "in", width: parameterColumnWidths.in },
    {
      title: t("apiDocs.required"),
      key: "required",
      width: parameterColumnWidths.required,
      render: (row) => h(NTag, { size: "small", type: row.required ? "warning" : "default" }, { default: () => (row.required ? t("common.yes") : t("common.no")) })
    },
    { title: t("apiDocs.parameterType"), key: "schema", width: parameterColumnWidths.schema, render: (row) => schemaLabel(row.schema) || t("common.none") },
    { title: t("field.description"), key: "description", width: parameterColumnWidths.description, render: (row) => parameterDescription(row) || t("common.none") }
  ])
);

const schemaFieldColumns = computed<DataTableColumns<SchemaField>>(() =>
  withResizableColumns([
    { title: t("apiDocs.fieldName"), key: "name", width: schemaFieldColumnWidths.name },
    {
      title: t("apiDocs.required"),
      key: "required",
      width: schemaFieldColumnWidths.required,
      render: (row) => h(NTag, { size: "small", type: row.required ? "warning" : "default" }, { default: () => (row.required ? t("common.yes") : t("common.no")) })
    },
    { title: t("apiDocs.parameterType"), key: "type", width: schemaFieldColumnWidths.type },
    { title: t("field.description"), key: "description", width: schemaFieldColumnWidths.description }
  ])
);

onMounted(async () => {
  await loadDocument();
});

async function loadDocument() {
  loading.value = true;
  try {
    openApiDocument.value = await getOpenApiDocument();
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

function openDetail(operation: OperationEntry) {
  selectedOperation.value = operation;
  showDetailModal.value = true;
}

function openTest(operation: OperationEntry) {
  selectedOperation.value = operation;
  clearTestParams();
  for (const parameter of testParameters.value) {
    testParams[parameterKey(parameter)] = parameterExample(parameter);
  }
  testBody.value = hasRequestBody(operation) ? requestBodyExampleText(operation) : "";
  testStatus.value = null;
  testRequest.value = "";
  testResponse.value = "";
  showTestModal.value = true;
}

function handleParameterColumnResize(_: number, limitedWidth: number, column: { key?: string | number }) {
  updateColumnWidth(parameterColumnWidths, column.key, parameterColumnWidthKeys, limitedWidth);
}

function handleSchemaFieldColumnResize(_: number, limitedWidth: number, column: { key?: string | number }) {
  updateColumnWidth(schemaFieldColumnWidths, column.key, schemaFieldColumnWidthKeys, limitedWidth);
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

  const headers = new Headers({ Authorization: `Bearer ${token}`, Accept: "application/json" });
  const requestHeaders: Record<string, string> = {
    Authorization: maskToken(token),
    Accept: "application/json"
  };
  if (body !== undefined) {
    headers.set("Content-Type", JSON_TYPE);
    requestHeaders["Content-Type"] = JSON_TYPE;
  }
  testRequest.value = JSON.stringify(
    {
      method: operation.method.toUpperCase(),
      url,
      headers: requestHeaders,
      body: body === undefined ? null : JSON.parse(body)
    },
    null,
    2
  );

  testing.value = true;
  try {
    const response = await fetch(url, { method: operation.method.toUpperCase(), headers, body });
    testStatus.value = response.status;
    testResponse.value = JSON.stringify(
      {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders(response.headers),
        body: await responseBody(response)
      },
      null,
      2
    );
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
    } else if (parameter.in === "query") {
      if (!value && parameter.required) {
        throw new Error(t("apiDocs.pathParamRequired", { name: parameter.name }));
      }
      if (value) {
        query.set(parameter.name, value);
      }
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
      if (!HTTP_METHODS.has(method)) continue;
      const tag = operation.tags?.[0] || "default";
      groupsByName.set(tag, [...(groupsByName.get(tag) || []), { key: `${method}:${path}`, path, method, operation }]);
    }
  }
  return Array.from(groupsByName.entries()).map(([name, operations]) => ({ name, label: tagLabel(name), operations }));
}

function operationMatches(entry: OperationEntry, normalizedKeyword: string) {
  return [
    entry.path,
    entry.method,
    entry.operation.summary,
    entry.operation.description,
    entry.operation.operationId,
    operationTitle(entry),
    operationDescription(entry),
    ...(entry.operation.tags || []).map(tagLabel)
  ]
    .filter(Boolean)
    .some((value) => String(value).toLowerCase().includes(normalizedKeyword));
}

function operationTitle(entry: OperationEntry) {
  const operationId = entry.operation.operationId;
  return operationId ? openApiText(`operation.${operationId}.summary`, entry.operation.summary || operationId) : entry.operation.summary || entry.path;
}

function operationDescription(entry: OperationEntry) {
  const operationId = entry.operation.operationId;
  return operationId ? openApiText(`operation.${operationId}.description`, entry.operation.description || "") : entry.operation.description || "";
}

function tagLabel(name: string) {
  return name === "default" ? t("apiDocs.defaultTag") : openApiText(`tag.${name}`, name);
}

function requestBodyText(operation: OpenApiOperation) {
  const contentTypes = Object.keys(operation.requestBody?.content || {});
  if (contentTypes.length === 0) {
    return t("common.none");
  }
  return `${operation.requestBody?.required ? t("apiDocs.required") : t("apiDocs.optional")} · ${contentTypes.join(t("common.listSeparator"))}`;
}

function responseItems(entry: OperationEntry): ResponseDetail[] {
  const responses = { ...(entry.operation.responses || {}) };
  for (const code of defaultResponseCodes(entry)) {
    responses[code] ||= { description: openApiText(`response.${code}`) };
  }
  return Object.entries(responses).map(([code, response]) => {
    const media = mediaEntry(response.content)?.[1];
    return {
      code,
      description: response.description || t("common.none"),
      explanation: openApiText(`response.${code}`, response.description || ""),
      fields: media?.schema ? schemaFields(media.schema) : [],
      example: media ? prettyJson(mediaExample(media, responseSchemaFallback(response))) : ""
    };
  });
}

function defaultResponseCodes(entry: OperationEntry) {
  const codes = ["401", "403", "500"];
  if (entry.method !== "get" || hasRequestBody(entry)) {
    codes.unshift("400");
  }
  if (entry.path.includes("{")) {
    codes.push("404");
  }
  return codes;
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

function parameterDescription(parameter: OpenApiParameter) {
  const operationId = selectedOperation.value?.operation.operationId || "";
  return openApiText(
    operationId ? `parameter.${operationId}.${parameter.name}` : "",
    openApiText(`parameter.common.${parameter.name}`, parameter.description || schemaDescription(parameter.schema, parameter.name))
  );
}

function parameterExample(parameter: OpenApiParameter) {
  const value = parameter.example ?? exampleFromSchema(parameter.schema, parameter.name);
  return value === undefined || value === null ? "" : String(value);
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
  return TEST_METHODS_WITH_BODY.has(operation.method) && Boolean(requestMedia(operation));
}

function requestContentType(operation: OperationEntry) {
  return requestMedia(operation)?.[0] || t("common.none");
}

function requestBodyFields(operation: OperationEntry) {
  const media = requestMedia(operation)?.[1];
  return media?.schema ? schemaFields(media.schema) : [];
}

function requestBodyExampleText(operation: OperationEntry) {
  const media = requestMedia(operation)?.[1];
  return media ? prettyJson(mediaExample(media, {})) : "";
}

function requestMedia(operation: OperationEntry): [string, OpenApiMediaType] | undefined {
  return mediaEntry(operation.operation.requestBody?.content);
}

function responseSchemaFallback(response: OpenApiResponse) {
  return mediaEntry(response.content)?.[1].schema;
}

function mediaEntry(content?: Record<string, OpenApiMediaType>): [string, OpenApiMediaType] | undefined {
  if (!content) {
    return undefined;
  }
  const entries = Object.entries(content);
  return entries.find(([type]) => type === JSON_TYPE) || entries.find(([type]) => type.includes("json")) || entries[0];
}

function mediaExample(media: OpenApiMediaType, fallbackSchema?: OpenApiSchema) {
  if (media.example !== undefined) {
    return media.example;
  }
  const firstExample = Object.values(media.examples || {})[0]?.value;
  if (firstExample !== undefined) {
    return firstExample;
  }
  return exampleFromSchema(media.schema || fallbackSchema);
}

function schemaFields(schema: OpenApiSchema | undefined, parent = "", depth = 0, parentRequired: string[] = []): SchemaField[] {
  const resolved = resolveSchema(schema);
  if (!resolved || depth > 2) return [];
  const properties = resolved.properties || {};
  const required = resolved.required || parentRequired;
  const fields: SchemaField[] = [];
  for (const [name, child] of Object.entries(properties)) {
    const path = parent ? `${parent}.${name}` : name;
    const childSchema = resolveSchema(child) || child;
    fields.push({
      name: path,
      required: required.includes(name),
      type: schemaLabel(childSchema),
      description: schemaDescription(childSchema, path)
    });
    if (childSchema.properties && depth < 1) {
      fields.push(...schemaFields(childSchema, path, depth + 1, childSchema.required || []));
    }
  }
  return fields;
}

function schemaDescription(schema: OpenApiSchema | undefined, fieldPath = "") {
  const description = schema?.description || "";
  if (!fieldPath) {
    return description;
  }
  const leafName = fieldPath.split(".").at(-1) || fieldPath;
  return openApiText(`schema.property.${fieldPath}`, openApiText(`schema.property.${leafName}`, description));
}

function schemaLabel(schema: OpenApiSchema | undefined): string {
  if (!schema) return "";
  if (schema.$ref) return refName(schema.$ref);
  const resolved = resolveSchema(schema);
  if (!resolved) return "";
  if (resolved.$ref) return refName(resolved.$ref);
  const composed = [...(resolved.anyOf || []), ...(resolved.oneOf || [])].map(schemaLabel).filter(Boolean);
  if (composed.length) return composed.join(" | ");
  if (resolved.allOf?.length) return resolved.allOf.map(schemaLabel).filter(Boolean).join(" & ");
  if (resolved.type === "array") return `${t("apiDocs.parameterType")}[] ${schemaLabel(resolved.items)}`.trim();
  return [resolved.type || (resolved.properties ? "object" : ""), resolved.format].filter(Boolean).join("/");
}

function resolveSchema(schema: OpenApiSchema | undefined, seen = new Set<string>()): OpenApiSchema | undefined {
  if (!schema) return undefined;
  if (schema.$ref) {
    const name = refName(schema.$ref);
    if (seen.has(name)) return schema;
    seen.add(name);
    return resolveSchema(openApiDocument.value?.components?.schemas?.[name], seen);
  }
  if (schema.allOf?.length) {
    return mergeSchemas(schema.allOf.map((item) => resolveSchema(item, seen)).filter(Boolean) as OpenApiSchema[]);
  }
  return schema;
}

function mergeSchemas(schemas: OpenApiSchema[]): OpenApiSchema {
  return schemas.reduce<OpenApiSchema>(
    (merged, schema) => ({
      ...merged,
      ...schema,
      required: [...(merged.required || []), ...(schema.required || [])],
      properties: { ...(merged.properties || {}), ...(schema.properties || {}) }
    }),
    {}
  );
}

function exampleFromSchema(schema: OpenApiSchema | undefined, name = "", seen = new Set<string>()): unknown {
  const resolved = resolveSchema(schema, seen);
  if (!resolved) return sampleByName(name, "string");
  if (resolved.default !== undefined) return resolved.default;
  if (resolved.example !== undefined) return resolved.example;
  if (resolved.examples?.length) return resolved.examples[0];
  if (resolved.const !== undefined) return resolved.const;
  if (resolved.enum?.length) return resolved.enum[0];
  const composed = [...(resolved.anyOf || []), ...(resolved.oneOf || [])].find((item) => item.type !== "null");
  if (composed) return exampleFromSchema(composed, name, seen);
  if (resolved.allOf?.length) return exampleFromSchema(mergeSchemas(resolved.allOf.map((item) => resolveSchema(item, seen)).filter(Boolean) as OpenApiSchema[]), name, seen);
  if (resolved.properties) {
    return Object.fromEntries(Object.entries(resolved.properties).map(([key, child]) => [key, exampleFromSchema(child, key, seen)]));
  }
  if (resolved.type === "array") {
    return [exampleFromSchema(resolved.items, singular(name), seen)];
  }
  return sampleByName(name, resolved.format || resolved.type || "string");
}

function sampleByName(name: string, type: string): unknown {
  if (type === "integer" || type === "number") {
    return name.endsWith("_id") || name === "id" ? 1 : 20;
  }
  if (type === "boolean") return true;
  if (type === "date-time") return new Date().toISOString();
  if (name === "username") return "api_user";
  if (name === "password" || name === "new_password") return "ApiPass123";
  if (name === "old_password") return "OldPass123";
  if (name === "phone") return "13800000000";
  if (name === "email") return "user@example.com";
  if (name === "target_type") return "authenticated";
  if (name === "sort_order") return "descend";
  if (name === "actor_scope" || name === "created_by") return "self";
  if (name === "page") return 1;
  if (name === "page_size") return 20;
  if (name === "ids") return 1;
  return name || "string";
}

function singular(name: string) {
  return name.endsWith("s") ? name.slice(0, -1) : name;
}

function refName(ref: string) {
  return ref.split("/").at(-1) || ref;
}

function prettyJson(value: unknown) {
  return JSON.stringify(value ?? {}, null, 2);
}

async function responseBody(response: Response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function responseHeaders(headers: Headers) {
  const entries: Record<string, string> = {};
  headers.forEach((value, key) => {
    if (["content-type", "content-length"].includes(key)) {
      entries[key] = value;
    }
  });
  return entries;
}

function maskToken(token: string) {
  if (token.length <= 16) {
    return "Bearer ***";
  }
  return `Bearer ${token.slice(0, 8)}...${token.slice(-4)}`;
}
</script>
