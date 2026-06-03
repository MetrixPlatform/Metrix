<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">
        <BrandMark />
        <div>
          <h1 class="auth-title">注册账号</h1>
          <p class="auth-subtitle">提交后等待管理员审核</p>
        </div>
      </div>
      <n-form ref="formRef" class="form-stack" :model="form" :rules="rules" label-placement="top">
        <n-form-item label="账号" path="username">
          <n-input v-model:value="form.username" />
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input v-model:value="form.password" type="password" show-password-on="click" />
        </n-form-item>
        <n-form-item label="确认密码" path="confirm_password">
          <n-input v-model:value="form.confirm_password" type="password" show-password-on="click" />
        </n-form-item>
        <n-form-item label="公司" path="company">
          <n-input v-model:value="form.company" />
        </n-form-item>
        <n-form-item label="部门" path="department">
          <n-input v-model:value="form.department" />
        </n-form-item>
        <n-form-item label="姓名" path="full_name">
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
import type { FormInst, FormRules } from "naive-ui";
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { register } from "../api/auth";
import BrandMark from "../components/BrandMark.vue";
import { maxLengthRule, minLengthRule, requiredRule, validateForm } from "../utils/validation";

const router = useRouter();
const message = useMessage();
const formRef = ref<FormInst | null>(null);
const loading = ref(false);
const form = reactive({ username: "", password: "", confirm_password: "", company: "", department: "", full_name: "" });

const rules: FormRules = {
  username: [requiredRule("账号"), minLengthRule("账号", 3), maxLengthRule("账号", 64)],
  password: [requiredRule("密码"), minLengthRule("密码", 6), maxLengthRule("密码", 128)],
  confirm_password: [
    requiredRule("确认密码"),
    {
      validator: () => form.password === form.confirm_password,
      message: "两次输入的密码不一致",
      trigger: ["input", "blur"]
    }
  ],
  company: [requiredRule("公司"), maxLengthRule("公司", 120)],
  department: [requiredRule("部门"), maxLengthRule("部门", 120)],
  full_name: [requiredRule("姓名"), maxLengthRule("姓名", 80)]
};

async function submit() {
  if (!(await validateForm(formRef.value))) return;
  loading.value = true;
  try {
    await register({
      username: form.username,
      password: form.password,
      company: form.company,
      department: form.department,
      full_name: form.full_name
    });
    message.success("注册申请已提交");
    await router.push("/login");
  } catch (error) {
    message.error((error as Error).message);
  } finally {
    loading.value = false;
  }
}
</script>
