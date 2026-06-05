<template>
  <n-dropdown trigger="click" :options="options" @select="setLocale">
    <n-button quaternary :title="t('common.language')">
      <template #icon><n-icon :component="LocalLanguage20Regular" /></template>
      {{ currentLabel }}
    </n-button>
  </n-dropdown>
</template>

<script setup lang="ts">
import { LocalLanguage20Regular } from "@vicons/fluent";
import { NButton, NDropdown, NIcon } from "naive-ui";
import { computed } from "vue";

import { appStore } from "../stores/app";
import { localeOptions, t, type Locale } from "../i18n";

const options = computed(() =>
  localeOptions.map((option) => ({
    label: t(option.labelKey),
    key: option.value
  }))
);
const currentLabel = computed(() => localeOptions.find((option) => option.value === appStore.locale)?.shortLabel || "ZH");

function setLocale(value: string | number) {
  appStore.setLocale(value as Locale);
}
</script>
