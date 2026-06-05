<template>
  <n-config-provider :theme="appStore.dark ? darkTheme : null" :locale="naiveLocale.locale" :date-locale="naiveLocale.dateLocale">
    <n-message-provider>
      <n-dialog-provider>
        <router-view />
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { darkTheme, NConfigProvider, NDialogProvider, NMessageProvider } from "naive-ui";
import { computed } from "vue";

import { naiveLocales } from "./i18n/naive";
import { appStore } from "./stores/app";

const naiveLocale = computed(() => naiveLocales[appStore.locale]);
</script>
