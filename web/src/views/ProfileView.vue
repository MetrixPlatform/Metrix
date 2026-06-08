<template>
  <div class="profile-grid">
    <section class="work-card profile-card">
      <div class="profile-card-head">
        <h3>{{ t("profile.info") }}</h3>
      </div>
      <n-form ref="profileFormRef" class="form-stack inline-form" :model="profile" :rules="profileRules" label-placement="left" label-width="auto">
        <n-form-item :label="t('field.username')">
          <n-input :value="authStore.user?.username" disabled placeholder="" />
        </n-form-item>
        <n-form-item :label="t('field.fullName')" path="full_name">
          <n-input v-model:value="profile.full_name" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('field.phone')" path="phone">
          <n-input v-model:value="profile.phone" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('field.email')" path="email">
          <n-input v-model:value="profile.email" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('field.company')" path="company">
          <n-input v-model:value="profile.company" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('field.department')" path="department">
          <n-input v-model:value="profile.department" placeholder="" />
        </n-form-item>
        <div class="form-actions">
          <n-button type="primary" @click="saveProfile">{{ t("profile.saveProfile") }}</n-button>
        </div>
      </n-form>
    </section>
    <section class="work-card profile-card">
      <div class="profile-card-head">
        <h3>{{ t("profile.changePassword") }}</h3>
      </div>
      <n-form ref="passwordFormRef" class="form-stack inline-form" :model="password" :rules="passwordRules" label-placement="left" label-width="auto">
        <n-form-item :label="t('field.oldPassword')" path="old_password">
          <n-input v-model:value="password.old_password" type="password" show-password-on="click" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('field.newPassword')" path="new_password">
          <n-input v-model:value="password.new_password" type="password" show-password-on="click" placeholder="" />
        </n-form-item>
        <div class="form-actions">
          <n-button type="primary" @click="savePassword">{{ t("profile.changePassword") }}</n-button>
        </div>
      </n-form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { NButton, NForm, NFormItem, NInput, useMessage } from "naive-ui";
import type { FormInst, FormRules } from "naive-ui";
import { computed, reactive, ref } from "vue";

import { changePassword, updateProfile } from "../api/auth";
import { t } from "../i18n";
import { authStore } from "../stores/auth";
import { messageText, showError } from "../utils/message";
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
const profileRules = computed<FormRules>(() => ({
  full_name: [requiredRule(t("field.fullName")), maxLengthRule(t("field.fullName"), 80)],
  phone: [requiredRule(t("field.phone")), phoneRule()],
  email: [requiredRule(t("field.email")), emailRule(), maxLengthRule(t("field.email"), 254)],
  company: maxLengthRule(t("field.company"), 120),
  department: maxLengthRule(t("field.department"), 120)
}));
const passwordRules = computed<FormRules>(() => ({
  old_password: [requiredRule(t("field.oldPassword")), maxLengthRule(t("field.oldPassword"), 128)],
  new_password: [requiredRule(t("field.newPassword")), minLengthRule(t("field.newPassword"), 6), maxLengthRule(t("field.newPassword"), 128)]
}));

async function saveProfile() {
  if (!(await validateForm(profileFormRef.value))) return;
  try {
    const user = await updateProfile(profile);
    authStore.user = user;
    message.success(t("profile.profileSaved"));
  } catch (error) {
    showError(message, error);
  }
}

async function savePassword() {
  if (!(await validateForm(passwordFormRef.value))) return;
  try {
    const result = await changePassword(password);
    password.old_password = "";
    password.new_password = "";
    message.success(messageText(result, "profile.passwordChanged"));
  } catch (error) {
    showError(message, error);
  }
}
</script>
