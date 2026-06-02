<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">
        <div class="brand-mark">M</div>
        <div>
          <h1 class="auth-title">初始化 Metrix</h1>
          <p class="auth-subtitle">选择网站数据库并创建初始管理员</p>
        </div>
      </div>
      <n-form class="form-stack" :model="form" label-placement="top">
        <n-form-item label="数据库类型">
          <n-radio-group v-model:value="form.database_type">
            <n-radio-button v-for="option in databaseOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </n-radio-button>
          </n-radio-group>
        </n-form-item>
        <n-form-item v-if="form.database_type === 'sqlite'" label="SQLite 数据库文件">
          <n-input v-model:value="form.sqlite_path" placeholder="留空使用 runtime/metrix.db" />
        </n-form-item>
        <template v-else>
          <n-form-item label="MySQL 地址">
            <n-input v-model:value="form.mysql.host" />
          </n-form-item>
          <n-form-item label="端口">
            <n-input-number v-model:value="form.mysql.port" class="full-width" :min="1" :max="65535" />
          </n-form-item>
          <n-form-item label="数据库名">
            <n-input v-model:value="form.mysql.database" />
          </n-form-item>
          <n-form-item label="用户名">
            <n-input v-model:value="form.mysql.username" />
          </n-form-item>
          <n-form-item label="密码">
            <n-input v-model:value="form.mysql.password" type="password" show-password-on="click" />
          </n-form-item>
        </template>
        <n-form-item label="管理员账号">
          <n-input v-model:value="form.admin_username" />
        </n-form-item>
        <n-form-item label="管理员密码">
          <n-input v-model:value="form.admin_password" type="password" show-password-on="click" />
        </n-form-item>
        <n-form-item label="姓名">
          <n-input v-model:value="form.admin_full_name" />
        </n-form-item>
        <n-form-item label="公司">
          <n-input v-model:value="form.admin_company" />
        </n-form-item>
        <n-form-item label="部门">
          <n-input v-model:value="form.admin_department" />
        </n-form-item>
        <n-button type="primary" block :loading="loading" @click="submit">初始化</n-button>
      </n-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NButton, NForm, NFormItem, NInput, NInputNumber, NRadioButton, NRadioGroup, useMessage } from "naive-ui";
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { installSystem } from "../api/install";

const router = useRouter();
const message = useMessage();
const loading = ref(false);
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

async function submit() {
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
</script>

<style scoped>
.full-width {
  width: 100%;
}
</style>
