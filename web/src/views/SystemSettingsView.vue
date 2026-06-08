<template>
  <section class="work-card settings-card">
    <div class="settings-grid">
      <section class="settings-section">
        <h2 class="settings-section-title">{{ t("settings.basic") }}</h2>
        <n-form ref="formRef" class="inline-form" :model="form" :rules="rules" label-placement="left" label-width="auto">
          <n-form-item :label="t('field.platformName')" path="app_name">
            <n-input v-model:value="form.app_name" placeholder="" />
          </n-form-item>
          <n-form-item :label="t('field.defaultLocale')" path="default_locale">
            <n-select v-model:value="form.default_locale" :options="localeSelectOptions" placeholder="" />
          </n-form-item>
          <n-form-item :label="t('field.registrationEnabled')" path="registration_enabled">
            <n-switch v-model:value="form.registration_enabled" />
          </n-form-item>
          <n-form-item :label="t('field.apiEnabled')" path="api_enabled">
            <n-switch v-model:value="form.api_enabled" />
          </n-form-item>
          <n-form-item :label="t('field.apiTokenRevealEnabled')" path="api_token_reveal_enabled">
            <n-switch v-model:value="form.api_token_reveal_enabled" :disabled="!form.api_enabled" />
          </n-form-item>
          <n-form-item :label="t('field.registrationRequired')" path="registration_required_fields">
            <div class="settings-checks">
              <n-checkbox v-model:checked="form.registration_required_fields.phone">{{ t("field.phone") }}</n-checkbox>
              <n-checkbox v-model:checked="form.registration_required_fields.email">{{ t("field.email") }}</n-checkbox>
              <n-checkbox v-model:checked="form.registration_required_fields.company">{{ t("field.company") }}</n-checkbox>
              <n-checkbox v-model:checked="form.registration_required_fields.department">{{ t("field.departmentOrPosition") }}</n-checkbox>
            </div>
          </n-form-item>
          <n-form-item :label="t('field.logRetention')" path="log_retention_days">
            <n-select v-model:value="form.log_retention_days" :options="retentionOptions" placeholder="" />
          </n-form-item>
        </n-form>
        <div class="form-actions">
          <permission-button permission="action:setting:update" type="primary" :loading="saving" @click="saveSettings">
            {{ t("common.save") }}
          </permission-button>
        </div>
      </section>
      <section class="settings-section">
        <h2 class="settings-section-title">{{ t("settings.backup") }}</h2>
        <div class="settings-backup-panel">
          <permission-button permission="action:setting:operate" type="primary" :loading="backingUp" @click="downloadBackup">
            <template #icon><n-icon :component="Archive20Regular" /></template>
            {{ t("settings.backupData") }}
          </permission-button>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Archive20Regular } from "@vicons/fluent";
import { NCheckbox, NForm, NFormItem, NIcon, NInput, NSelect, NSwitch, useMessage } from "naive-ui";
import type { FormInst, FormRules } from "naive-ui";
import { computed, onMounted, reactive, ref } from "vue";

import { backupData, getSystemSettings, updateSystemSettings } from "../api/settings";
import type { SystemSettings } from "../api/types";
import PermissionButton from "../components/PermissionButton.vue";
import { localeOptions, t } from "../i18n";
import { appStore } from "../stores/app";
import { settingsStore } from "../stores/settings";
import { saveBlob } from "../utils/download";
import { showError } from "../utils/message";
import { maxLengthRule, requiredRule, validateForm } from "../utils/validation";

const message = useMessage();
const formRef = ref<FormInst | null>(null);
const saving = ref(false);
const backingUp = ref(false);
const form = reactive<SystemSettings>({
  app_name: "",
  registration_enabled: true,
  registration_required_fields: {
    phone: true,
    email: true,
    company: false,
    department: false
  },
  log_retention_days: 90,
  default_locale: "zh-CN",
  api_enabled: true,
  api_token_reveal_enabled: true
});

const rules = computed<FormRules>(() => ({
  app_name: [requiredRule(t("field.platformName")), maxLengthRule(t("field.platformName"), 80)]
}));
const localeSelectOptions = computed(() => localeOptions.map((item) => ({ label: t(item.labelKey), value: item.value })));
const retentionOptions = computed(() => [
  { label: t("settings.retention7"), value: 7 },
  { label: t("settings.retention30"), value: 30 },
  { label: t("settings.retention90"), value: 90 },
  { label: t("settings.retention180"), value: 180 },
  { label: t("settings.retention365"), value: 365 }
]);

onMounted(async () => {
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
    const updated = await updateSystemSettings(form);
    assignSettings(updated);
    settingsStore.setPublic(updated);
    await appStore.setLocale(updated.default_locale);
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
  form.registration_required_fields.phone = settings.registration_required_fields.phone;
  form.registration_required_fields.email = settings.registration_required_fields.email;
  form.registration_required_fields.company = settings.registration_required_fields.company;
  form.registration_required_fields.department = settings.registration_required_fields.department;
  form.log_retention_days = settings.log_retention_days;
  form.default_locale = settings.default_locale;
  form.api_enabled = settings.api_enabled;
  form.api_token_reveal_enabled = settings.api_token_reveal_enabled;
}

</script>
