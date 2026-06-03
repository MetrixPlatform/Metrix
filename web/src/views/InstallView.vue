<template>
  <div class="auth-page">
    <div class="auth-card install-card">
      <div class="auth-brand">
        <BrandMark />
        <div>
          <h1 class="auth-title">初始化 Metrix</h1>
          <p class="auth-subtitle">选择网站数据库并创建初始管理员</p>
        </div>
      </div>
      <n-form ref="formRef" class="install-form" :model="form" :rules="rules" label-placement="top">
        <div class="install-grid">
          <section class="install-section">
            <div class="install-section-head">
              <h2 class="install-section-title">数据库配置</h2>
              <n-button secondary :loading="testing" @click="testConnection">测试连接</n-button>
            </div>
            <n-form-item label="数据库类型" path="database_type">
              <n-radio-group v-model:value="form.database_type">
                <n-radio-button v-for="option in databaseOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </n-radio-button>
              </n-radio-group>
            </n-form-item>
            <n-form-item v-if="form.database_type === 'sqlite'" label="SQLite 数据库文件" path="sqlite_path">
              <n-input v-model:value="form.sqlite_path" placeholder="留空使用 runtime/metrix.db" />
            </n-form-item>
            <template v-else>
              <div class="install-field-row compact">
                <n-form-item label="MySQL 地址" path="mysql.host">
                  <n-input v-model:value="form.mysql.host" />
                </n-form-item>
                <n-form-item label="端口" path="mysql.port">
                  <n-input-number v-model:value="form.mysql.port" class="full-width" :min="1" :max="65535" />
                </n-form-item>
              </div>
              <div class="install-field-row">
                <n-form-item label="数据库名" path="mysql.database">
                  <n-input v-model:value="form.mysql.database" />
                </n-form-item>
                <n-form-item label="用户名" path="mysql.username">
                  <n-input v-model:value="form.mysql.username" />
                </n-form-item>
              </div>
              <n-form-item label="密码" path="mysql.password">
                <n-input v-model:value="form.mysql.password" type="password" show-password-on="click" />
              </n-form-item>
            </template>
          </section>
          <section class="install-section">
            <h2 class="install-section-title">管理员信息</h2>
            <div class="install-field-row">
              <n-form-item label="管理员账号" path="admin_username">
                <n-input v-model:value="form.admin_username" />
              </n-form-item>
              <n-form-item label="管理员密码" path="admin_password">
                <n-input v-model:value="form.admin_password" type="password" show-password-on="click" />
              </n-form-item>
            </div>
            <div class="install-field-row">
              <n-form-item label="姓名" path="admin_full_name">
                <n-input v-model:value="form.admin_full_name" />
              </n-form-item>
              <n-form-item label="公司" path="admin_company">
                <n-input v-model:value="form.admin_company" />
              </n-form-item>
            </div>
            <n-form-item label="部门" path="admin_department">
              <n-input v-model:value="form.admin_department" />
            </n-form-item>
            <div class="install-submit">
              <n-button type="primary" block :loading="loading" @click="submit">初始化</n-button>
            </div>
          </section>
        </div>
      </n-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NButton, NForm, NFormItem, NInput, NInputNumber, NRadioButton, NRadioGroup, useMessage } from "naive-ui";
import type { FormInst, FormRules } from "naive-ui";
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { installSystem, testInstallDatabase } from "../api/install";
import BrandMark from "../components/BrandMark.vue";
import { maxLengthRule, minLengthRule, numberRequiredRule, requiredRule, validateForm } from "../utils/validation";

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
    database: "metrix",
    username: "root",
    password: ""
  },
  admin_username: "",
  admin_password: "",
  admin_full_name: "",
  admin_company: "",
  admin_department: ""
});

const rules: FormRules = {
  sqlite_path: maxLengthRule("SQLite 数据库文件", 500),
  "mysql.host": [requiredRule("MySQL 地址"), maxLengthRule("MySQL 地址", 120)],
  "mysql.port": numberRequiredRule("端口"),
  "mysql.database": [requiredRule("数据库名"), maxLengthRule("数据库名", 64)],
  "mysql.username": [requiredRule("用户名"), maxLengthRule("用户名", 120)],
  "mysql.password": maxLengthRule("密码", 256),
  admin_username: [requiredRule("管理员账号"), minLengthRule("管理员账号", 3), maxLengthRule("管理员账号", 64)],
  admin_password: [requiredRule("管理员密码"), minLengthRule("管理员密码", 6), maxLengthRule("管理员密码", 128)],
  admin_full_name: [requiredRule("姓名"), maxLengthRule("姓名", 80)],
  admin_company: maxLengthRule("公司", 120),
  admin_department: maxLengthRule("部门", 120)
};

async function testConnection() {
  testing.value = true;
  try {
    await testInstallDatabase(databasePayload());
    message.success("数据库连接正常");
  } catch (error) {
    message.error((error as Error).message);
  } finally {
    testing.value = false;
  }
}

async function submit() {
  if (!(await validateForm(formRef.value))) return;
  loading.value = true;
  try {
    await installSystem(form);
    message.success("初始化完成，请登录");
    await router.push("/login");
  } catch (error) {
    message.error((error as Error).message);
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
