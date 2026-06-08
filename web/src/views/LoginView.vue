<template>
  <div class="auth-page login-page" :class="{ 'has-announcement': publicAnnouncements.length > 0 }">
    <div class="auth-top-actions">
      <LanguageSwitcher />
      <n-button quaternary circle :title="themeTitle" @click="toggleTheme">
        <template #icon><n-icon :component="themeIcon" /></template>
      </n-button>
    </div>
    <announcement-ticker v-if="publicAnnouncements.length > 0" class="auth-announcement-ticker" :items="publicAnnouncements" />
    <div class="auth-card login-card">
      <h1 class="auth-wordmark">{{ appName }}</h1>
      <n-form
        ref="formRef"
        class="form-stack inline-form"
        :model="form"
        :rules="rules"
        label-placement="left"
        label-width="auto"
        @keyup.enter="submit"
      >
        <n-form-item :label="t('field.username')" path="username">
          <n-input v-model:value="form.username" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('field.password')" path="password">
          <n-input v-model:value="form.password" type="password" show-password-on="click" placeholder="" />
        </n-form-item>
        <n-button type="primary" block :loading="loading" @click="submit">{{ t("auth.login") }}</n-button>
        <div class="form-actions">
          <router-link v-if="registrationEnabled" class="muted-link" to="/register">{{ t("auth.registerAccount") }}</router-link>
          <n-button text class="muted-link" @click="showForgotModal = true">{{ t("auth.forgotPassword") }}</n-button>
        </div>
      </n-form>
    </div>
    <n-modal v-model:show="showForgotModal" preset="card" class="modal-card" :title="t('auth.forgotPassword')">
      <div class="forgot-password-content">{{ t("auth.forgotPasswordTip") }}</div>
      <div class="form-actions">
        <n-button type="primary" @click="showForgotModal = false">{{ t("common.ok") }}</n-button>
      </div>
    </n-modal>
    <footer class="auth-footer">
      <CopyrightNotice />
    </footer>
  </div>
</template>

<script setup lang="ts">
import { WeatherMoon20Regular as WeatherMoon, WeatherSunny20Regular as WeatherSunny } from "@vicons/fluent";
import { NButton, NForm, NFormItem, NIcon, NInput, NModal, useMessage } from "naive-ui";
import type { FormInst, FormRules } from "naive-ui";
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { login } from "../api/auth";
import { listPublicAnnouncements } from "../api/announcements";
import type { PublicAnnouncementItem } from "../api/types";
import AnnouncementTicker from "../components/AnnouncementTicker.vue";
import CopyrightNotice from "../components/CopyrightNotice.vue";
import LanguageSwitcher from "../components/LanguageSwitcher.vue";
import { t } from "../i18n";
import { appStore } from "../stores/app";
import { authStore } from "../stores/auth";
import { settingsStore } from "../stores/settings";
import { showError } from "../utils/message";
import { maxLengthRule, requiredRule, validateForm } from "../utils/validation";

const router = useRouter();
const message = useMessage();
const formRef = ref<FormInst | null>(null);
const loading = ref(false);
const showForgotModal = ref(false);
const publicAnnouncements = ref<PublicAnnouncementItem[]>([]);
const appName = computed(() => settingsStore.appName());
const registrationEnabled = computed(() => settingsStore.publicSettings.registration_enabled);
const themeIcon = computed(() => (appStore.dark ? WeatherSunny : WeatherMoon));
const themeTitle = computed(() => (appStore.dark ? t("common.themeLight") : t("common.themeDark")));
const form = reactive({ username: "", password: "" });
const rules = computed<FormRules>(() => ({
  username: [requiredRule(t("field.username")), maxLengthRule(t("field.username"), 64)],
  password: [requiredRule(t("field.password")), maxLengthRule(t("field.password"), 128)]
}));

onMounted(async () => {
  try {
    publicAnnouncements.value = await listPublicAnnouncements();
  } catch {
    publicAnnouncements.value = [];
  }
});

async function submit() {
  if (!(await validateForm(formRef.value))) return;
  loading.value = true;
  try {
    const session = await login(form);
    authStore.setSession(session.token, session.user, session.permissions);
    await router.push("/");
  } catch (error) {
    showError(message, error);
  } finally {
    loading.value = false;
  }
}

function toggleTheme() {
  appStore.toggleTheme();
}
</script>
