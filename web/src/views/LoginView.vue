<template>
  <div class="auth-page login-page" :class="{ 'has-announcement': publicAnnouncements.length > 0 }">
    <n-button class="auth-theme-button" quaternary circle :title="themeTitle" @click="toggleTheme">
      <template #icon><n-icon :component="themeIcon" /></template>
    </n-button>
    <announcement-ticker v-if="publicAnnouncements.length > 0" class="auth-announcement-ticker" :items="publicAnnouncements" />
    <div class="auth-card login-card">
      <h1 class="auth-wordmark">{{ APP_NAME }}</h1>
      <n-form
        ref="formRef"
        class="form-stack inline-form"
        :model="form"
        :rules="rules"
        label-placement="left"
        label-width="64"
        @keyup.enter="submit"
      >
        <n-form-item label="账号" path="username">
          <n-input v-model:value="form.username" placeholder="请输入账号" />
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input v-model:value="form.password" type="password" show-password-on="click" placeholder="请输入密码" />
        </n-form-item>
        <n-button type="primary" block :loading="loading" @click="submit">登录</n-button>
        <div class="form-actions">
          <router-link class="muted-link" to="/register">注册账号</router-link>
          <n-button text class="muted-link" @click="showForgotModal = true">忘记密码</n-button>
        </div>
      </n-form>
    </div>
    <n-modal v-model:show="showForgotModal" preset="card" class="modal-card" title="忘记密码">
      <div class="forgot-password-content">请联系管理员修改密码。</div>
      <div class="form-actions">
        <n-button type="primary" @click="showForgotModal = false">我知道了</n-button>
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
import { APP_NAME } from "../config/app";
import { appStore } from "../stores/app";
import { authStore } from "../stores/auth";
import { showError } from "../utils/message";
import { maxLengthRule, requiredRule, validateForm } from "../utils/validation";

const router = useRouter();
const message = useMessage();
const formRef = ref<FormInst | null>(null);
const loading = ref(false);
const showForgotModal = ref(false);
const publicAnnouncements = ref<PublicAnnouncementItem[]>([]);
const themeIcon = computed(() => (appStore.dark ? WeatherSunny : WeatherMoon));
const themeTitle = computed(() => (appStore.dark ? "切换浅色主题" : "切换深色主题"));
const form = reactive({ username: "", password: "" });
const rules: FormRules = {
  username: [requiredRule("账号"), maxLengthRule("账号", 64)],
  password: [requiredRule("密码"), maxLengthRule("密码", 128)]
};

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
