<template>
  <n-button quaternary circle :title="themeTitle" @click="appStore.toggleTheme">
    <template #icon><n-icon :component="themeIcon" /></template>
  </n-button>
</template>

<script setup lang="ts">
import { WeatherMoon20Regular as WeatherMoon, WeatherSunny20Regular as WeatherSunny } from "@vicons/fluent";
import { NButton, NIcon } from "naive-ui";
import { computed } from "vue";

import { t } from "../i18n";
import { appStore } from "../stores/app";

const themeIcon = computed(() => (appStore.dark ? WeatherSunny : WeatherMoon));
const themeTitle = computed(() => (appStore.dark ? t("common.themeLight") : t("common.themeDark")));
</script>
