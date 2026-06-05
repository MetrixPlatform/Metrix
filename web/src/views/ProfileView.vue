<template>
  <div class="profile-grid">
    <section class="work-card profile-card">
      <div class="profile-card-head">
        <h3>个人信息</h3>
      </div>
      <n-form ref="profileFormRef" class="form-stack inline-form" :model="profile" :rules="profileRules" label-placement="left" label-width="72">
        <n-form-item label="账号">
          <n-input :value="authStore.user?.username" disabled />
        </n-form-item>
        <n-form-item label="姓名" path="full_name">
          <n-input v-model:value="profile.full_name" />
        </n-form-item>
        <n-form-item label="手机号码" path="phone">
          <n-input v-model:value="profile.phone" />
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="profile.email" />
        </n-form-item>
        <n-form-item label="公司" path="company">
          <n-input v-model:value="profile.company" />
        </n-form-item>
        <n-form-item label="部门" path="department">
          <n-input v-model:value="profile.department" />
        </n-form-item>
        <div class="form-actions">
          <n-button type="primary" @click="saveProfile">保存资料</n-button>
        </div>
      </n-form>
    </section>
    <section class="work-card profile-card">
      <div class="profile-card-head">
        <h3>修改密码</h3>
      </div>
      <n-form ref="passwordFormRef" class="form-stack inline-form" :model="password" :rules="passwordRules" label-placement="left" label-width="72">
        <n-form-item label="旧密码" path="old_password">
          <n-input v-model:value="password.old_password" type="password" show-password-on="click" />
        </n-form-item>
        <n-form-item label="新密码" path="new_password">
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
import type { FormInst, FormRules } from "naive-ui";
import { reactive, ref } from "vue";

import { changePassword, updateProfile } from "../api/auth";
import { authStore } from "../stores/auth";
import { showError } from "../utils/message";
import { emailRule, maxLengthRule, minLengthRule, phoneRule, requiredRule, validateForm } from "../utils/validation";

const message = useMessage();
const profileFormRef = ref<FormInst | null>(null);
const passwordFormRef = ref<FormInst | null>(null);
const profile = reactive({
  full_name: authStore.user?.full_name || "",
  phone: authStore.user?.phone || "",
  email: authStore.user?.email || "",
  company: authStore.user?.company || "",
  department: authStore.user?.department || ""
});
const password = reactive({ old_password: "", new_password: "" });
const profileRules: FormRules = {
  full_name: [requiredRule("姓名"), maxLengthRule("姓名", 80)],
  phone: [requiredRule("手机号码"), phoneRule()],
  email: [requiredRule("邮箱"), emailRule(), maxLengthRule("邮箱", 254)],
  company: maxLengthRule("公司", 120),
  department: maxLengthRule("部门", 120)
};
const passwordRules: FormRules = {
  old_password: [requiredRule("旧密码"), maxLengthRule("旧密码", 128)],
  new_password: [requiredRule("新密码"), minLengthRule("新密码", 6), maxLengthRule("新密码", 128)]
};

async function saveProfile() {
  if (!(await validateForm(profileFormRef.value))) return;
  try {
    const user = await updateProfile(profile);
    authStore.user = user;
    message.success("资料已保存");
  } catch (error) {
    showError(message, error);
  }
}

async function savePassword() {
  if (!(await validateForm(passwordFormRef.value))) return;
  try {
    await changePassword(password);
    password.old_password = "";
    password.new_password = "";
    message.success("密码已修改");
  } catch (error) {
    showError(message, error);
  }
}
</script>
