<template>
  <div class="page-stack">
    <section class="work-card">
      <h3>个人信息</h3>
      <n-form class="form-stack" label-placement="top">
        <n-form-item label="账号">
          <n-input :value="authStore.user?.username" disabled />
        </n-form-item>
        <n-form-item label="姓名">
          <n-input v-model:value="profile.full_name" />
        </n-form-item>
        <n-form-item label="公司">
          <n-input v-model:value="profile.company" />
        </n-form-item>
        <n-form-item label="部门">
          <n-input v-model:value="profile.department" />
        </n-form-item>
        <div class="form-actions">
          <n-button type="primary" @click="saveProfile">保存资料</n-button>
        </div>
      </n-form>
    </section>
    <section class="work-card">
      <h3>修改密码</h3>
      <n-form class="form-stack" label-placement="top">
        <n-form-item label="旧密码">
          <n-input v-model:value="password.old_password" type="password" show-password-on="click" />
        </n-form-item>
        <n-form-item label="新密码">
          <n-input v-model:value="password.new_password" type="password" show-password-on="click" />
        </n-form-item>
        <div class="form-actions">
          <n-button type="primary" @click="savePassword">修改密码</n-button>
        </div>
      </n-form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { NButton, NForm, NFormItem, NInput, useMessage } from "naive-ui";
import { reactive } from "vue";

import { changePassword, updateProfile } from "../api/auth";
import { authStore } from "../stores/auth";

const message = useMessage();
const profile = reactive({
  full_name: authStore.user?.full_name || "",
  company: authStore.user?.company || "",
  department: authStore.user?.department || ""
});
const password = reactive({ old_password: "", new_password: "" });

async function saveProfile() {
  try {
    const user = await updateProfile(profile);
    authStore.user = user;
    message.success("资料已保存");
  } catch (error) {
    message.error((error as Error).message);
  }
}

async function savePassword() {
  try {
    await changePassword(password);
    password.old_password = "";
    password.new_password = "";
    message.success("密码已修改");
  } catch (error) {
    message.error((error as Error).message);
  }
}
</script>
