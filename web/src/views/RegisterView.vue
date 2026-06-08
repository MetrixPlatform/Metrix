<template>
  <div class="auth-page register-page">
    <div class="auth-card register-card">
      <div class="auth-card-actions">
        <LanguageSwitcher />
        <ThemeToggleButton />
      </div>
      <div class="auth-brand">
        <BrandMark />
        <div>
          <h1 class="auth-title">{{ t("auth.registerAccount") }}</h1>
        </div>
      </div>
      <n-form
        ref="formRef"
        class="register-form inline-form"
        :model="form"
        :rules="rules"
        label-placement="left"
        label-width="auto"
      >
        <div class="register-form-fields">
          <n-form-item :label="t('field.username')" path="username">
            <n-input v-model:value="form.username" placeholder="" />
          </n-form-item>
          <n-form-item :label="t('field.password')" path="password">
            <n-input v-model:value="form.password" type="password" show-password-on="click" placeholder="" />
          </n-form-item>
          <n-form-item :label="t('field.confirmPassword')" path="confirm_password">
            <n-input v-model:value="form.confirm_password" type="password" show-password-on="click" placeholder="" />
          </n-form-item>
          <n-form-item :label="t('field.fullName')" path="full_name">
            <n-input v-model:value="form.full_name" placeholder="" />
          </n-form-item>
          <n-form-item :label="t('field.phone')" path="phone">
            <n-input v-model:value="form.phone" placeholder="" />
          </n-form-item>
          <n-form-item :label="t('field.email')" path="email">
            <n-input v-model:value="form.email" placeholder="" />
          </n-form-item>
          <n-form-item :label="t('field.company')" path="company">
            <n-input v-model:value="form.company" placeholder="" />
          </n-form-item>
          <n-form-item :label="t('field.department')" path="department">
            <n-input v-model:value="form.department" placeholder="" />
          </n-form-item>
        </div>
        <div class="register-form-footer">
          <div class="form-actions register-form-actions">
            <n-button type="primary" :loading="loading" @click="submit">{{ t("auth.submitRegister") }}</n-button>
            <router-link class="muted-link" to="/login">{{ t("auth.backToLogin") }}</router-link>
          </div>
        </div>
      </n-form>
    </div>
    <footer class="auth-footer">
      <CopyrightNotice />
    </footer>
  </div>
</template>

<script setup lang="ts">
import { NButton, NForm, NFormItem, NInput, useDialog, useMessage } from "naive-ui";
import type { FormInst, FormItemRule, FormRules } from "naive-ui";
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { register } from "../api/auth";
import BrandMark from "../components/BrandMark.vue";
import CopyrightNotice from "../components/CopyrightNotice.vue";
import LanguageSwitcher from "../components/LanguageSwitcher.vue";
import ThemeToggleButton from "../components/ThemeToggleButton.vue";
import { t } from "../i18n";
import { settingsStore } from "../stores/settings";
import { messageText, showError } from "../utils/message";
import { emailRule, maxLengthRule, minLengthRule, phoneRule, requiredRule, validateForm } from "../utils/validation";

const router = useRouter();
const dialog = useDialog();
const message = useMessage();
const formRef = ref<FormInst | null>(null);
const loading = ref(false);
const form = reactive({ username: "", password: "", confirm_password: "", full_name: "", phone: "", email: "", company: "", department: "" });
const requiredFields = computed(() => settingsStore.publicSettings.registration_required_fields);

const rules = computed<FormRules>(() => ({
  username: [requiredRule(t("field.username")), minLengthRule(t("field.username"), 3), maxLengthRule(t("field.username"), 64)],
  password: [requiredRule(t("field.password")), minLengthRule(t("field.password"), 6), maxLengthRule(t("field.password"), 128)],
  confirm_password: [
    requiredRule(t("field.confirmPassword")),
    {
      validator: () => form.password === form.confirm_password,
      message: t("validation.passwordMismatch"),
      trigger: ["input", "blur"]
    }
  ],
  full_name: [requiredRule(t("field.fullName")), maxLengthRule(t("field.fullName"), 80)],
  phone: fieldRules(t("field.phone"), requiredFields.value.phone, phoneRule()),
  email: fieldRules(t("field.email"), requiredFields.value.email, emailRule(), maxLengthRule(t("field.email"), 254)),
  company: fieldRules(t("field.company"), requiredFields.value.company, maxLengthRule(t("field.company"), 120)),
  department: fieldRules(t("field.department"), requiredFields.value.department, maxLengthRule(t("field.department"), 120))
}));

onMounted(async () => {
  if (!settingsStore.loaded) {
    await settingsStore.loadPublic().catch(() => undefined);
  }
});

async function submit() {
  if (!(await validateForm(formRef.value))) return;
  loading.value = true;
  try {
    const result = await register({
      username: form.username,
      password: form.password,
      phone: form.phone,
      email: form.email,
      company: form.company,
      department: form.department,
      full_name: form.full_name
    });
    if (result.code === "auth.registerSubmitted") {
      dialog.success({
        title: messageText(result, "auth.registerSubmitted"),
        content: t("auth.registerApprovalTip"),
        positiveText: t("common.ok"),
        closable: false,
        maskClosable: false,
        onPositiveClick: () => {
          void router.push("/login");
        }
      });
      return;
    }
    message.success(messageText(result, "auth.registerSuccess"));
    await router.push("/login");
  } catch (error) {
    showError(message, error);
  } finally {
    loading.value = false;
  }
}

function fieldRules(label: string, required: boolean, ...rules: FormItemRule[]) {
  return required ? [requiredRule(label), ...rules] : rules;
}
</script>
