<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">
        <BrandMark />
        <div>
          <h1 class="auth-title">Metrix</h1>
          <p class="auth-subtitle">内网数据处理平台</p>
        </div>
      </div>
      <n-form ref="formRef" class="form-stack" :model="form" :rules="rules" label-placement="top" @keyup.enter="submit">
        <n-form-item label="账号" path="username">
          <n-input v-model:value="form.username" placeholder="请输入账号" />
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input v-model:value="form.password" type="password" show-password-on="click" placeholder="请输入密码" />
        </n-form-item>
        <n-button type="primary" block :loading="loading" @click="submit">登录</n-button>
        <div class="form-actions">
          <router-link class="muted-link" to="/register">注册账号</router-link>
          <span>忘记密码请联系管理员</span>
        </div>
      </n-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NButton, NForm, NFormItem, NInput, useMessage } from "naive-ui";
import type { FormInst, FormRules } from "naive-ui";
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { login } from "../api/auth";
import BrandMark from "../components/BrandMark.vue";
import { authStore } from "../stores/auth";
import { maxLengthRule, requiredRule, validateForm } from "../utils/validation";

const router = useRouter();
const message = useMessage();
const formRef = ref<FormInst | null>(null);
const loading = ref(false);
const form = reactive({ username: "", password: "" });
const rules: FormRules = {
  username: [requiredRule("账号"), maxLengthRule("账号", 64)],
  password: [requiredRule("密码"), maxLengthRule("密码", 128)]
};

async function submit() {
  if (!(await validateForm(formRef.value))) return;
  loading.value = true;
  try {
    const session = await login(form);
    authStore.setSession(session.token, session.user, session.permissions);
    await router.push("/");
  } catch (error) {
    message.error((error as Error).message);
  } finally {
    loading.value = false;
  }
}
</script>
