<template>
  <n-dropdown trigger="click" :options="options" @select="setLocale">
    <n-button class="language-switcher-button" quaternary circle :title="t('common.language')">
      <span class="language-switcher-icon" aria-hidden="true">
        <span class="language-switcher-zh">文</span>
        <span class="language-switcher-en">A</span>
      </span>
    </n-button>
  </n-dropdown>
</template>

<script setup lang="ts">
import { NButton, NDropdown } from "naive-ui";
import { computed } from "vue";

import { appStore } from "../stores/app";
import { localeOptions, t, type Locale } from "../i18n";

const options = computed(() =>
  localeOptions.map((option) => ({
    label: t(option.labelKey),
    key: option.value
  }))
);

function setLocale(value: string | number) {
  void appStore.setLocale(value as Locale);
}
</script>
