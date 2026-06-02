<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">
        <div class="brand-mark">M</div>
        <div>
          <h1 class="auth-title">注册账号</h1>
          <p class="auth-subtitle">提交后等待管理员审核</p>
        </div>
      </div>
      <n-form class="form-stack" :model="form" label-placement="top">
        <n-form-item label="账号">
          <n-input v-model:value="form.username" />
        </n-form-item>
        <n-form-item label="密码">
          <n-input v-model:value="form.password" type="password" show-password-on="click" />
        </n-form-item>
        <n-form-item label="确认密码">
          <n-input v-model:value="confirmPassword" type="password" show-password-on="click" />
        </n-form-item>
        <n-form-item label="公司">
          <n-input v-model:value="form.company" />
        </n-form-item>
        <n-form-item label="部门">
          <n-input v-model:value="form.department" />
        </n-form-item>
        <n-form-item label="姓名">
          <n-input v-model:value="form.full_name" />
        </n-form-item>
        <n-button type="primary" block :loading="loading" @click="submit">提交注册</n-button>
        <div class="form-actions">
          <router-link class="muted-link" to="/login">返回登录</router-link>
        </div>
      </n-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NButton, NForm, NFormItem, NInput, useMessage } from "naive-ui";
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { register } from "../api/auth";

const router = useRouter();
const message = useMessage();
const loading = ref(false);
const confirmPassword = ref("");
const form = reactive({ username: "", password: "", company: "", department: "", full_name: "" });

async function submit() {
  if (form.password !== confirmPassword.value) {
    message.error("两次输入的密码不一致");
    return;
  }
  loading.value = true;
  try {
    await register(form);
    message.success("注册申请已提交");
    await router.push("/login");
  } catch (error) {
    message.error((error as Error).message);
  } finally {
    loading.value = false;
  }
}
</script>
