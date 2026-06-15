<template>
  <section class="work-card settings-card">
    <n-form ref="formRef" class="settings-form inline-form" :model="form" :rules="rules" label-placement="left" label-width="auto">
      <n-tabs v-model:value="activeTab" class="settings-tabs" type="line" animated>
        <n-tab-pane name="basic" :tab="t('settings.basic')" display-directive="show">
          <section class="settings-section settings-section-compact">
            <div class="settings-section-head">
              <h2 class="settings-section-title">{{ t("settings.basic") }}</h2>
              <p>{{ t("settings.basicDesc") }}</p>
            </div>
            <div class="settings-fields settings-basic-fields">
              <n-form-item :label="t('field.platformName')" path="app_name">
                <n-input v-model:value="form.app_name" placeholder="" />
              </n-form-item>
              <n-form-item :label="t('field.defaultLocale')" path="default_locale">
                <n-select v-model:value="form.default_locale" :options="localeSelectOptions" placeholder="" />
              </n-form-item>
            </div>
          </section>
        </n-tab-pane>

        <n-tab-pane name="navigation" :tab="t('settings.navigation')" display-directive="show" class="navigation-settings-pane">
          <section class="settings-section navigation-settings-section">
            <div class="settings-section-head">
              <h2 class="settings-section-title">{{ t("settings.navigation") }}</h2>
              <p>{{ t("settings.navigationDesc") }}</p>
            </div>
            <n-scrollbar class="navigation-order-scroll" trigger="none">
              <div class="navigation-order-list">
                <div v-for="item in navigationLayout" :key="item.navigationKey" class="navigation-order-card">
                  <div class="navigation-order-row">
                    <div class="navigation-order-label">
                      <n-button
                        v-if="item.children?.length"
                        size="tiny"
                        quaternary
                        circle
                        :title="isNavigationGroupCollapsed(item.navigationKey) ? t('settings.expandGroup') : t('settings.collapseGroup')"
                        @click="toggleNavigationGroup(item.navigationKey)"
                      >
                        <template #icon>
                          <n-icon :component="isNavigationGroupCollapsed(item.navigationKey) ? ChevronRight20Regular : ChevronDown20Regular" />
                        </template>
                      </n-button>
                      <span v-else class="navigation-order-spacer" />
                      <n-icon :component="item.icon" />
                      <span :title="item.label">{{ item.label }}</span>
                      <n-tag v-if="item.children?.length" size="small" :bordered="false">{{ t("settings.navigationGroup") }}</n-tag>
                    </div>
                    <div class="navigation-order-actions">
                      <n-button size="tiny" quaternary :disabled="!canMoveNavigation(item.navigationKey, 'up')" @click="moveNavigation(item.navigationKey, 'up')">
                        {{ t("settings.moveUp") }}
                      </n-button>
                      <n-button size="tiny" quaternary :disabled="!canMoveNavigation(item.navigationKey, 'down')" @click="moveNavigation(item.navigationKey, 'down')">
                        {{ t("settings.moveDown") }}
                      </n-button>
                    </div>
                  </div>
                  <div v-if="item.children?.length && !isNavigationGroupCollapsed(item.navigationKey)" class="navigation-order-children">
                    <div v-for="child in item.children" :key="child.navigationKey" class="navigation-order-row navigation-order-child">
                      <div class="navigation-order-label">
                        <span class="navigation-order-spacer" />
                        <n-icon :component="child.icon" />
                        <span :title="child.label">{{ child.label }}</span>
                      </div>
                      <div class="navigation-order-actions">
                        <n-button size="tiny" quaternary :disabled="!canMoveNavigation(child.navigationKey, 'up')" @click="moveNavigation(child.navigationKey, 'up')">
                          {{ t("settings.moveUp") }}
                        </n-button>
                        <n-button size="tiny" quaternary :disabled="!canMoveNavigation(child.navigationKey, 'down')" @click="moveNavigation(child.navigationKey, 'down')">
                          {{ t("settings.moveDown") }}
                        </n-button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </n-scrollbar>
            <div class="settings-inline-actions">
              <n-button @click="resetNavigationOrder">{{ t("settings.restoreDefaultNavigation") }}</n-button>
            </div>
          </section>
        </n-tab-pane>

        <n-tab-pane name="registration" :tab="t('settings.registration')" display-directive="show">
          <section class="settings-section settings-section-compact">
            <div class="settings-section-head">
              <h2 class="settings-section-title">{{ t("settings.registration") }}</h2>
              <p>{{ t("settings.registrationDesc") }}</p>
            </div>
            <div class="settings-switch-list">
              <div class="settings-switch-row">
                <span>{{ t("field.registrationEnabled") }}</span>
                <n-switch v-model:value="form.registration_enabled" />
              </div>
              <div class="settings-switch-row">
                <span>{{ t("field.registrationApprovalRequired") }}</span>
                <n-switch v-model:value="form.registration_approval_required" />
              </div>
            </div>
            <n-form-item class="settings-check-form-item" :label="t('field.registrationRequired')" path="registration_required_fields">
              <div class="settings-checks">
                <n-checkbox v-model:checked="form.registration_required_fields.phone">{{ t("field.phone") }}</n-checkbox>
                <n-checkbox v-model:checked="form.registration_required_fields.email">{{ t("field.email") }}</n-checkbox>
                <n-checkbox v-model:checked="form.registration_required_fields.company">{{ t("field.company") }}</n-checkbox>
                <n-checkbox v-model:checked="form.registration_required_fields.department">{{ t("field.departmentOrPosition") }}</n-checkbox>
              </div>
            </n-form-item>
          </section>
        </n-tab-pane>

        <n-tab-pane name="api" :tab="t('settings.api')" display-directive="show">
          <section class="settings-section settings-section-compact">
            <div class="settings-section-head">
              <h2 class="settings-section-title">{{ t("settings.api") }}</h2>
              <p>{{ t("settings.apiDesc") }}</p>
            </div>
            <div class="settings-switch-list">
              <div class="settings-switch-row">
                <span>{{ t("field.apiEnabled") }}</span>
                <n-switch v-model:value="form.api_enabled" />
              </div>
              <div class="settings-switch-row">
                <span>{{ t("field.apiTokenRevealEnabled") }}</span>
                <n-switch v-model:value="form.api_token_reveal_enabled" :disabled="!form.api_enabled" />
              </div>
            </div>
          </section>
        </n-tab-pane>

        <n-tab-pane name="docker" :tab="t('settings.docker')" display-directive="show">
          <section class="settings-section settings-section-compact">
            <div class="settings-section-head">
              <h2 class="settings-section-title">{{ t("settings.docker") }}</h2>
              <p>{{ t("settings.dockerDesc") }}</p>
            </div>
            <n-form-item :label="t('field.dockerConnectionMode')" path="docker_connection_mode">
              <n-select v-model:value="form.docker_connection_mode" :options="dockerConnectionModeOptions" placeholder="" />
            </n-form-item>
            <n-form-item :label="t('field.dockerHost')" path="docker_host">
              <n-input
                v-model:value="form.docker_host"
                :disabled="form.docker_connection_mode === 'auto'"
                :placeholder="t('settings.dockerHostPlaceholder')"
              />
            </n-form-item>
            <p class="settings-field-hint">{{ t("settings.dockerHostHelp") }}</p>
          </section>
        </n-tab-pane>

        <n-tab-pane name="audit" :tab="t('settings.audit')" display-directive="show">
          <section class="settings-section settings-section-compact">
            <div class="settings-section-head">
              <h2 class="settings-section-title">{{ t("settings.audit") }}</h2>
              <p>{{ t("settings.auditDesc") }}</p>
            </div>
            <n-form-item :label="t('field.logRetention')" path="log_retention_days">
              <n-select v-model:value="form.log_retention_days" :options="retentionOptions" placeholder="" />
            </n-form-item>
          </section>
        </n-tab-pane>

        <n-tab-pane name="dataJobs" :tab="t('settings.dataJobs')" display-directive="show">
          <section class="settings-section settings-section-compact">
            <div class="settings-section-head">
              <h2 class="settings-section-title">{{ t("settings.dataJobs") }}</h2>
              <p>{{ t("settings.dataJobsDesc") }}</p>
            </div>
            <n-form-item :label="t('field.dataJobMaxWorkers')" path="data_job_max_workers">
              <n-input-number v-model:value="form.data_job_max_workers" :min="1" :max="16" :show-button="false" />
            </n-form-item>
            <n-form-item :label="t('field.dataJobRetention')" path="data_job_retention_hours">
              <div class="settings-duration-control">
                <n-input-number
                  v-model:value="dataJobRetention.value"
                  :min="1"
                  :max="dataJobRetention.unit === 'days' ? 365 : 8760"
                  :show-button="false"
                />
                <n-select v-model:value="dataJobRetention.unit" :options="dataJobRetentionUnitOptions" />
              </div>
            </n-form-item>
          </section>
        </n-tab-pane>

        <n-tab-pane name="backup" :tab="t('settings.backup')" display-directive="show">
          <section class="settings-section settings-section-compact">
            <div class="settings-section-head">
              <h2 class="settings-section-title">{{ t("settings.backup") }}</h2>
              <p>{{ t("settings.backupDesc") }}</p>
            </div>
            <div class="settings-backup-panel">
              <permission-button permission="action:setting:operate" type="primary" :loading="backingUp" @click="downloadBackup">
                <template #icon><n-icon :component="Archive20Regular" /></template>
                {{ t("settings.backupData") }}
              </permission-button>
            </div>
          </section>
        </n-tab-pane>
      </n-tabs>

      <div v-if="activeTab !== 'backup'" class="settings-footer">
        <div class="form-actions">
          <permission-button permission="action:setting:update" type="primary" :loading="saving" @click="saveSettings">
            {{ t("common.save") }}
          </permission-button>
        </div>
      </div>
    </n-form>
  </section>
</template>

<script setup lang="ts">
import { Archive20Regular, ChevronDown20Regular, ChevronRight20Regular } from "@vicons/fluent";
import {
  NButton,
  NCheckbox,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NInputNumber,
  NScrollbar,
  NSelect,
  NSwitch,
  NTabPane,
  NTag,
  NTabs,
  useMessage
} from "naive-ui";
import type { FormInst, FormRules } from "naive-ui";
import { computed, onMounted, reactive, ref } from "vue";

import { backupData, getSystemSettings, updateSystemSettings } from "../api/settings";
import type { SystemSettings } from "../api/types";
import PermissionButton from "../components/PermissionButton.vue";
import { ensureLocaleNames, localeOptions, t } from "../i18n";
import { flattenNavigationKeys, getNavigationLayout } from "../router/page-registry";
import { settingsStore } from "../stores/settings";
import { saveBlob } from "../utils/download";
import { showError } from "../utils/message";
import { maxLengthRule, requiredRule, validateForm } from "../utils/validation";

type SettingsTab = "basic" | "navigation" | "registration" | "api" | "docker" | "audit" | "dataJobs" | "backup";
type NavigationMove = "up" | "down";
type DataJobRetentionUnit = "hours" | "days";
type DockerConnectionMode = "auto" | "manual";

const message = useMessage();
const formRef = ref<FormInst | null>(null);
const activeTab = ref<SettingsTab>("basic");
const saving = ref(false);
const backingUp = ref(false);
const expandedNavigationGroups = ref<Set<string>>(new Set());
const dataJobRetention = reactive<{ value: number | null; unit: DataJobRetentionUnit }>({
  value: 7,
  unit: "days"
});
const form = reactive<SystemSettings>({
  app_name: "",
  registration_enabled: true,
  registration_approval_required: true,
  registration_required_fields: {
    phone: true,
    email: true,
    company: false,
    department: false
  },
  log_retention_days: 90,
  default_locale: "zh-CN",
  api_enabled: true,
  api_token_reveal_enabled: true,
  data_job_max_workers: 2,
  data_job_retention_hours: 168,
  data_job_retention_days: 7,
  navigation_order: [],
  docker_connection_mode: "auto",
  docker_host: ""
});

const rules = computed<FormRules>(() => ({
  app_name: [requiredRule(t("field.platformName")), maxLengthRule(t("field.platformName"), 80)]
}));
const localeSelectOptions = computed(() => localeOptions.value);
const navigationLayout = computed(() => getNavigationLayout(form.navigation_order));
const retentionOptions = computed(() => [
  { label: t("settings.retention7"), value: 7 },
  { label: t("settings.retention30"), value: 30 },
  { label: t("settings.retention90"), value: 90 },
  { label: t("settings.retention180"), value: 180 },
  { label: t("settings.retention365"), value: 365 }
]);
const dataJobRetentionUnitOptions = computed(() => [
  { label: t("settings.retentionUnitHours"), value: "hours" },
  { label: t("settings.retentionUnitDays"), value: "days" }
]);
const dockerConnectionModeOptions = computed(() => [
  { label: t("settings.dockerModeAuto"), value: "auto" },
  { label: t("settings.dockerModeManual"), value: "manual" }
]);

onMounted(async () => {
  void ensureLocaleNames();
  await loadSettings();
});

async function loadSettings() {
  try {
    assignSettings(await getSystemSettings());
  } catch (error) {
    showError(message, error);
  }
}

async function saveSettings() {
  if (!(await validateForm(formRef.value))) return;
  saving.value = true;
  try {
    form.data_job_retention_hours = dataJobRetentionHours();
    form.data_job_retention_days = Math.max(1, Math.ceil(form.data_job_retention_hours / 24));
    const updated = await updateSystemSettings({
      app_name: form.app_name,
      registration_enabled: form.registration_enabled,
      registration_approval_required: form.registration_approval_required,
      registration_required_fields: form.registration_required_fields,
      log_retention_days: form.log_retention_days,
      default_locale: form.default_locale,
      api_enabled: form.api_enabled,
      api_token_reveal_enabled: form.api_token_reveal_enabled,
      data_job_max_workers: form.data_job_max_workers,
      data_job_retention_hours: form.data_job_retention_hours,
      navigation_order: form.navigation_order,
      docker_connection_mode: form.docker_connection_mode,
      docker_host: form.docker_host
    });
    assignSettings(updated);
    settingsStore.setPublic(updated);
    message.success(t("settings.saved"));
  } catch (error) {
    showError(message, error);
  } finally {
    saving.value = false;
  }
}

async function downloadBackup() {
  backingUp.value = true;
  try {
    saveBlob(await backupData(), `metrix-backup-${new Date().toISOString().slice(0, 10)}.zip`);
  } catch (error) {
    showError(message, error);
  } finally {
    backingUp.value = false;
  }
}

function assignSettings(settings: SystemSettings) {
  form.app_name = settings.app_name;
  form.registration_enabled = settings.registration_enabled;
  form.registration_approval_required = settings.registration_approval_required;
  form.registration_required_fields.phone = settings.registration_required_fields.phone;
  form.registration_required_fields.email = settings.registration_required_fields.email;
  form.registration_required_fields.company = settings.registration_required_fields.company;
  form.registration_required_fields.department = settings.registration_required_fields.department;
  form.log_retention_days = settings.log_retention_days;
  form.default_locale = settings.default_locale;
  form.api_enabled = settings.api_enabled;
  form.api_token_reveal_enabled = settings.api_token_reveal_enabled;
  form.data_job_max_workers = settings.data_job_max_workers;
  form.data_job_retention_hours = settings.data_job_retention_hours ?? settings.data_job_retention_days * 24;
  form.data_job_retention_days = settings.data_job_retention_days;
  assignDataJobRetention(form.data_job_retention_hours);
  form.navigation_order = [...settings.navigation_order];
  form.docker_connection_mode = normalizeDockerConnectionMode(settings.docker_connection_mode);
  form.docker_host = settings.docker_host || "";
}

function assignDataJobRetention(hours: number) {
  if (hours >= 24 && hours % 24 === 0) {
    dataJobRetention.value = hours / 24;
    dataJobRetention.unit = "days";
    return;
  }
  dataJobRetention.value = hours;
  dataJobRetention.unit = "hours";
}

function dataJobRetentionHours() {
  const value = Math.max(1, Math.round(dataJobRetention.value || 1));
  return dataJobRetention.unit === "days" ? value * 24 : value;
}

function normalizeDockerConnectionMode(value: unknown): DockerConnectionMode {
  return value === "manual" ? "manual" : "auto";
}

function canMoveNavigation(key: string, direction: NavigationMove) {
  const siblings = navigationSiblings(key);
  const index = siblings.indexOf(key);
  if (index < 0) return false;
  return direction === "up" ? index > 0 : index < siblings.length - 1;
}

function moveNavigation(key: string, direction: NavigationMove) {
  const siblings = navigationSiblings(key);
  const index = siblings.indexOf(key);
  if (index < 0) return;
  const targetIndex = direction === "up" ? index - 1 : index + 1;
  const targetKey = siblings[targetIndex];
  if (!targetKey) return;
  const order = flattenNavigationKeys(navigationLayout.value);
  const left = order.indexOf(key);
  const right = order.indexOf(targetKey);
  if (left < 0 || right < 0) return;
  [order[left], order[right]] = [order[right], order[left]];
  form.navigation_order = order;
}

function resetNavigationOrder() {
  form.navigation_order = [];
}

function isNavigationGroupCollapsed(key: string) {
  return !expandedNavigationGroups.value.has(key);
}

function toggleNavigationGroup(key: string) {
  const next = new Set(expandedNavigationGroups.value);
  if (next.has(key)) {
    next.delete(key);
  } else {
    next.add(key);
  }
  expandedNavigationGroups.value = next;
}

function navigationSiblings(key: string) {
  const topLevel = navigationLayout.value.map((item) => item.navigationKey);
  if (topLevel.includes(key)) return topLevel;
  for (const item of navigationLayout.value) {
    const childKeys = item.children?.map((child) => child.navigationKey) || [];
    if (childKeys.includes(key)) return childKeys;
  }
  return [];
}

</script>
