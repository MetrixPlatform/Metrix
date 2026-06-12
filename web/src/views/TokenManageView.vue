<template>
  <section class="work-card table-page-card">
    <div class="toolbar token-toolbar">
      <strong>{{ t("token.title") }}</strong>
      <div class="toolbar-group">
        <n-button :loading="loading" @click="loadTokens">
          <template #icon><n-icon :component="ArrowClockwise20Regular" /></template>
          {{ t("common.refresh") }}
        </n-button>
        <permission-button permission="action:api_token:create" type="primary" @click="openCreate">
          <template #icon><n-icon :component="Add20Regular" /></template>
          {{ t("token.create") }}
        </permission-button>
      </div>
    </div>
    <n-data-table
      class="page-data-table"
      flex-height
      :columns="columns"
      :data="tokens"
      :loading="loading"
      :pagination="false"
      :row-key="(row) => row.id"
      :scroll-x="tableScrollX"
      @unstable-column-resize="handleColumnResize"
    />

    <n-modal v-model:show="showCreateModal" preset="card" class="modal-card" :title="t('token.create')">
      <n-form ref="formRef" class="form-stack inline-form" :model="form" :rules="rules" label-placement="left" label-width="auto">
        <n-form-item :label="t('field.tokenName')" path="name">
          <n-input v-model:value="form.name" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('field.expiresAt')" path="expires_at">
          <div class="token-expiry-control">
            <n-radio-group v-model:value="form.expires_mode">
              <n-radio-button value="never">{{ t("token.neverExpires") }}</n-radio-button>
              <n-radio-button value="custom">{{ t("token.customExpires") }}</n-radio-button>
            </n-radio-group>
            <n-date-picker
              v-if="form.expires_mode === 'custom'"
              v-model:value="form.expires_at"
              class="full-width"
              type="datetime"
              placeholder=""
              clearable
            />
          </div>
        </n-form-item>
        <div class="form-actions">
          <n-button @click="showCreateModal = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" :loading="creating" @click="saveToken">{{ t("common.create") }}</n-button>
        </div>
      </n-form>
    </n-modal>

    <n-modal v-model:show="showPlainTokenModal" preset="card" class="token-result-modal" :title="t('token.created')">
      <div class="token-once-tip">{{ createdTip }}</div>
      <n-input :value="plainToken" readonly type="textarea" :autosize="{ minRows: 3, maxRows: 5 }" />
      <div class="form-actions">
        <n-button @click="copyPlainToken">
          <template #icon><n-icon :component="Copy20Regular" /></template>
          {{ t("common.copy") }}
        </n-button>
        <n-button type="primary" @click="showPlainTokenModal = false">{{ t("common.ok") }}</n-button>
      </div>
    </n-modal>

    <n-modal v-model:show="showSecretModal" preset="card" class="token-result-modal" :title="t('token.fullToken')">
      <div class="token-once-tip">{{ revealedTokenName }}</div>
      <n-input :value="revealedToken" readonly type="textarea" :autosize="{ minRows: 3, maxRows: 5 }" />
      <div class="form-actions">
        <n-button @click="copyRevealedToken">
          <template #icon><n-icon :component="Copy20Regular" /></template>
          {{ t("common.copy") }}
        </n-button>
        <n-button type="primary" @click="showSecretModal = false">{{ t("common.close") }}</n-button>
      </div>
    </n-modal>
  </section>
</template>

<script setup lang="ts">
import { Add20Regular, ArrowClockwise20Regular, Copy20Regular, Delete20Regular, Eye20Regular } from "@vicons/fluent";
import { computed, h, onMounted, reactive, ref } from "vue";
import { NButton, NDataTable, NDatePicker, NForm, NFormItem, NIcon, NInput, NModal, NRadioButton, NRadioGroup, useDialog, useMessage } from "naive-ui";
import type { DataTableColumns, FormInst, FormRules } from "naive-ui";

import { createApiToken, deleteApiToken, getApiTokenSecret, listApiTokens } from "../api/tokens";
import type { ApiTokenItem } from "../api/types";
import PermissionButton from "../components/PermissionButton.vue";
import StatusTag from "../components/StatusTag.vue";
import { formatDateTime, t } from "../i18n";
import { authStore } from "../stores/auth";
import { settingsStore } from "../stores/settings";
import { copyText } from "../utils/clipboard";
import { messageText, showError } from "../utils/message";
import { sumColumnWidths, updateColumnWidth, withResizableColumns } from "../utils/table";
import { maxLengthRule, requiredRule, validateForm } from "../utils/validation";

type ExpiryMode = "never" | "custom";

const message = useMessage();
const dialog = useDialog();
const formRef = ref<FormInst | null>(null);
const loading = ref(false);
const creating = ref(false);
const secretLoadingId = ref<number | null>(null);
const tokens = ref<ApiTokenItem[]>([]);
const showCreateModal = ref(false);
const showPlainTokenModal = ref(false);
const showSecretModal = ref(false);
const plainToken = ref("");
const revealedToken = ref("");
const revealedTokenName = ref("");
const form = reactive({
  name: "",
  expires_mode: "never" as ExpiryMode,
  expires_at: null as number | null
});
const rules = computed<FormRules>(() => ({
  name: [requiredRule(t("field.tokenName")), maxLengthRule(t("field.tokenName"), 80)]
}));
const createdTip = computed(() => (settingsStore.apiTokenRevealEnabled() ? t("token.createdRevealTip") : t("token.createdTip")));
const tokenColumnWidths = reactive<Record<string, number>>({
  name: 180,
  prefix: 150,
  status: 90,
  expiresAt: 170,
  lastUsedAt: 170,
  createdAt: 170,
  actions: 120
});
const tokenColumnWidthKeys: Record<string, string> = {
  name: "name",
  token_prefix: "prefix",
  is_active: "status",
  expires_at: "expiresAt",
  last_used_at: "lastUsedAt",
  created_at: "createdAt"
};
const tableScrollX = computed(() => sumColumnWidths(tokenColumnWidths));

const columns = computed<DataTableColumns<ApiTokenItem>>(() =>
  withResizableColumns([
    { title: t("field.tokenName"), key: "name", width: tokenColumnWidths.name, ellipsis: { tooltip: true } },
    { title: t("field.tokenPrefix"), key: "token_prefix", width: tokenColumnWidths.prefix },
    {
      title: t("field.status"),
      key: "is_active",
      width: tokenColumnWidths.status,
      render: (row) => h(StatusTag, { status: row.is_active })
    },
    { title: t("field.expiresAt"), key: "expires_at", width: tokenColumnWidths.expiresAt, render: (row) => formatExpiresAt(row.expires_at) },
    { title: t("field.lastUsedAt"), key: "last_used_at", width: tokenColumnWidths.lastUsedAt, render: (row) => formatLastUsedAt(row.last_used_at) },
    { title: t("field.createdAt"), key: "created_at", width: tokenColumnWidths.createdAt, render: (row) => formatDateTime(row.created_at) },
    {
      title: t("common.actions"),
      key: "actions",
      width: tokenColumnWidths.actions,
      fixed: "right",
      align: "center",
      render: (row) => h("div", { class: "table-action-group" }, actionButtons(row))
    }
  ])
);

onMounted(async () => {
  await loadTokens();
});

async function loadTokens() {
  loading.value = true;
  try {
    tokens.value = await listApiTokens();
  } catch (error) {
    showError(message, error);
  } finally {
    loading.value = false;
  }
}

function handleColumnResize(_: number, limitedWidth: number, column: { key?: string | number }) {
  updateColumnWidth(tokenColumnWidths, column.key, tokenColumnWidthKeys, limitedWidth);
}

function openCreate() {
  Object.assign(form, { name: "", expires_mode: "never" as ExpiryMode, expires_at: null });
  showCreateModal.value = true;
}

async function saveToken() {
  if (!(await validateForm(formRef.value))) return;
  if (form.expires_mode === "custom" && !form.expires_at) {
    message.error(t("validation.required", { label: t("field.expiresAt") }));
    return;
  }
  creating.value = true;
  try {
    const result = await createApiToken({
      name: form.name,
      expires_at: form.expires_mode === "custom" && form.expires_at ? new Date(form.expires_at).toISOString() : null
    });
    plainToken.value = result.token;
    showCreateModal.value = false;
    showPlainTokenModal.value = true;
    await loadTokens();
    message.success(t("token.created"));
  } catch (error) {
    showError(message, error);
  } finally {
    creating.value = false;
  }
}

function actionButtons(row: ApiTokenItem) {
  const buttons = [];
  if (canRevealToken(row)) {
    buttons.push(
      h(
        NButton,
        {
          class: "row-action-button",
          size: "small",
          quaternary: true,
          circle: true,
          loading: secretLoadingId.value === row.id,
          title: t("common.show"),
          onClick: () => showTokenSecret(row)
        },
        { icon: () => h(NIcon, { component: Eye20Regular }) }
      ),
      h(
        NButton,
        {
          class: "row-action-button",
          size: "small",
          quaternary: true,
          circle: true,
          loading: secretLoadingId.value === row.id,
          title: t("token.copyFull"),
          onClick: () => copyTokenSecret(row)
        },
        { icon: () => h(NIcon, { component: Copy20Regular }) }
      )
    );
  }
  if (authStore.has("action:api_token:delete")) {
    buttons.push(
      h(
        NButton,
        {
          class: "row-action-button",
          size: "small",
          quaternary: true,
          circle: true,
          title: t("common.delete"),
          onClick: () => confirmDelete(row)
        },
        { icon: () => h(NIcon, { component: Delete20Regular }) }
      )
    );
  }
  return buttons;
}

function canRevealToken(row: ApiTokenItem) {
  return row.secret_available && settingsStore.apiTokenRevealEnabled() && authStore.has("action:api_token:read");
}

async function showTokenSecret(row: ApiTokenItem) {
  try {
    revealedToken.value = await fetchTokenSecret(row);
    revealedTokenName.value = row.name;
    showSecretModal.value = true;
  } catch (error) {
    showError(message, error);
  }
}

async function copyTokenSecret(row: ApiTokenItem) {
  try {
    await copyText(await fetchTokenSecret(row));
    message.success(t("common.copied"));
  } catch (error) {
    showError(message, error);
  }
}

async function fetchTokenSecret(row: ApiTokenItem) {
  secretLoadingId.value = row.id;
  try {
    const result = await getApiTokenSecret(row.id);
    return result.token;
  } finally {
    secretLoadingId.value = null;
  }
}

function confirmDelete(token: ApiTokenItem) {
  dialog.warning({
    title: t("token.deleteTitle"),
    content: t("token.deleteConfirm", { name: token.name }),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: async () => {
      try {
        const result = await deleteApiToken(token.id);
        await loadTokens();
        message.success(messageText(result, "token.deleted"));
      } catch (error) {
        showError(message, error);
      }
    }
  });
}

async function copyPlainToken() {
  try {
    await copyText(plainToken.value);
    message.success(t("common.copied"));
  } catch {
    message.error(t("message.operationFailed"));
  }
}

async function copyRevealedToken() {
  try {
    await copyText(revealedToken.value);
    message.success(t("common.copied"));
  } catch {
    message.error(t("message.operationFailed"));
  }
}

function formatExpiresAt(value: string | null) {
  return value ? formatDateTime(value) : t("token.neverExpires");
}

function formatLastUsedAt(value: string | null) {
  return value ? formatDateTime(value) : t("common.never");
}
</script>
