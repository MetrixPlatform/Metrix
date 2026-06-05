<template>
  <div class="auth-page">
    <div class="auth-top-actions">
      <LanguageSwitcher />
    </div>
    <div class="auth-card install-card">
      <div class="auth-brand">
        <BrandMark />
        <div>
          <h1 class="auth-title">{{ t("install.title", { name: APP_NAME }) }}</h1>
          <p class="auth-subtitle">{{ t("install.subtitle") }}</p>
        </div>
      </div>
      <n-form ref="formRef" class="install-form inline-form" :model="form" :rules="rules" label-placement="left" label-width="116">
        <div class="install-grid">
          <section class="install-section">
            <div class="install-section-head">
              <h2 class="install-section-title">{{ t("install.databaseConfig") }}</h2>
              <n-button secondary :loading="testing" @click="testConnection">{{ t("install.testConnection") }}</n-button>
            </div>
            <n-form-item :label="t('field.databaseType')" path="database_type">
              <n-radio-group v-model:value="form.database_type">
                <n-radio-button v-for="option in databaseOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </n-radio-button>
              </n-radio-group>
            </n-form-item>
            <n-form-item v-if="form.database_type === 'sqlite'" :label="t('field.sqlitePath')" path="sqlite_path">
              <n-input v-model:value="form.sqlite_path" :placeholder="t('install.emptySqlitePath', { path: DEFAULT_SQLITE_PATH })" />
            </n-form-item>
            <template v-else>
              <div class="install-field-row compact">
                <n-form-item :label="t('field.mysqlHost')" path="mysql.host">
                  <n-input v-model:value="form.mysql.host" />
                </n-form-item>
                <n-form-item :label="t('field.mysqlPort')" path="mysql.port">
                  <n-input-number v-model:value="form.mysql.port" class="full-width" :min="1" :max="65535" />
                </n-form-item>
              </div>
              <div class="install-field-row">
                <n-form-item :label="t('field.mysqlDatabase')" path="mysql.database">
                  <n-input v-model:value="form.mysql.database" />
                </n-form-item>
                <n-form-item :label="t('field.mysqlUsername')" path="mysql.username">
                  <n-input v-model:value="form.mysql.username" />
                </n-form-item>
              </div>
              <n-form-item :label="t('field.mysqlPassword')" path="mysql.password">
                <n-input v-model:value="form.mysql.password" type="password" show-password-on="click" />
              </n-form-item>
            </template>
          </section>
          <section class="install-section">
            <h2 class="install-section-title">{{ t("install.adminInfo") }}</h2>
            <div class="install-field-row">
              <n-form-item :label="t('field.adminUsername')" path="admin_username">
                <n-input v-model:value="form.admin_username" />
              </n-form-item>
              <n-form-item :label="t('field.adminPassword')" path="admin_password">
                <n-input v-model:value="form.admin_password" type="password" show-password-on="click" />
              </n-form-item>
            </div>
            <div class="install-field-row">
              <n-form-item :label="t('field.adminFullName')" path="admin_full_name">
                <n-input v-model:value="form.admin_full_name" />
              </n-form-item>
              <n-form-item :label="t('field.adminPhone')" path="admin_phone">
                <n-input v-model:value="form.admin_phone" />
              </n-form-item>
            </div>
            <div class="install-field-row">
              <n-form-item :label="t('field.adminEmail')" path="admin_email">
                <n-input v-model:value="form.admin_email" />
              </n-form-item>
              <n-form-item :label="t('field.adminCompany')" path="admin_company">
                <n-input v-model:value="form.admin_company" />
              </n-form-item>
            </div>
            <n-form-item :label="t('field.adminDepartment')" path="admin_department">
              <n-input v-model:value="form.admin_department" />
            </n-form-item>
            <div class="install-submit">
              <n-button type="primary" block :loading="loading" @click="submit">{{ t("install.submit") }}</n-button>
            </div>
          </section>
        </div>
      </n-form>
    </div>
    <footer class="auth-footer">
      <CopyrightNotice />
    </footer>
  </div>
</template>

<script setup lang="ts">
import { NButton, NForm, NFormItem, NInput, NInputNumber, NRadioButton, NRadioGroup, useMessage } from "naive-ui";
import type { FormInst, FormRules } from "naive-ui";
import { computed, reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { installSystem, testInstallDatabase } from "../api/install";
import BrandMark from "../components/BrandMark.vue";
import CopyrightNotice from "../components/CopyrightNotice.vue";
import LanguageSwitcher from "../components/LanguageSwitcher.vue";
import { APP_NAME, DEFAULT_DATABASE_NAME, DEFAULT_SQLITE_PATH } from "../config/app";
import { t } from "../i18n";
import { messageText, showError } from "../utils/message";
import { emailRule, maxLengthRule, minLengthRule, numberRequiredRule, phoneRule, requiredRule, validateForm } from "../utils/validation";

const router = useRouter();
const message = useMessage();
const formRef = ref<FormInst | null>(null);
const loading = ref(false);
const testing = ref(false);
const databaseOptions = [
  { label: "SQLite", value: "sqlite" },
  { label: "MySQL", value: "mysql" }
];

const form = reactive({
  database_type: "sqlite" as "sqlite" | "mysql",
  sqlite_path: "",
  mysql: {
    host: "127.0.0.1",
    port: 3306,
    database: DEFAULT_DATABASE_NAME,
    username: "root",
    password: ""
  },
  admin_username: "",
  admin_password: "",
  admin_full_name: "",
  admin_phone: "",
  admin_email: "",
  admin_company: "",
  admin_department: ""
});

const rules = computed<FormRules>(() => ({
  sqlite_path: maxLengthRule(t("field.sqlitePath"), 500),
  "mysql.host": [requiredRule(t("field.mysqlHost")), maxLengthRule(t("field.mysqlHost"), 120)],
  "mysql.port": numberRequiredRule(t("field.mysqlPort")),
  "mysql.database": [requiredRule(t("field.mysqlDatabase")), maxLengthRule(t("field.mysqlDatabase"), 64)],
  "mysql.username": [requiredRule(t("field.mysqlUsername")), maxLengthRule(t("field.mysqlUsername"), 120)],
  "mysql.password": maxLengthRule(t("field.mysqlPassword"), 256),
  admin_username: [requiredRule(t("field.adminUsername")), minLengthRule(t("field.adminUsername"), 3), maxLengthRule(t("field.adminUsername"), 64)],
  admin_password: [requiredRule(t("field.adminPassword")), minLengthRule(t("field.adminPassword"), 6), maxLengthRule(t("field.adminPassword"), 128)],
  admin_full_name: [requiredRule(t("field.adminFullName")), maxLengthRule(t("field.adminFullName"), 80)],
  admin_phone: [requiredRule(t("field.adminPhone")), phoneRule()],
  admin_email: [requiredRule(t("field.adminEmail")), emailRule(), maxLengthRule(t("field.adminEmail"), 254)],
  admin_company: maxLengthRule(t("field.adminCompany"), 120),
  admin_department: maxLengthRule(t("field.adminDepartment"), 120)
}));

async function testConnection() {
  testing.value = true;
  try {
    const result = await testInstallDatabase(databasePayload());
    message.success(messageText(result, "install.connectionOk"));
  } catch (error) {
    showError(message, error);
  } finally {
    testing.value = false;
  }
}

async function submit() {
  if (!(await validateForm(formRef.value))) return;
  loading.value = true;
  try {
    const result = await installSystem(form);
    message.success(messageText(result, "install.finished"));
    await router.push("/login");
  } catch (error) {
    showError(message, error);
  } finally {
    loading.value = false;
  }
}

function databasePayload() {
  return {
    database_type: form.database_type,
    sqlite_path: form.sqlite_path,
    mysql: form.database_type === "mysql" ? form.mysql : undefined
  };
}
</script>
