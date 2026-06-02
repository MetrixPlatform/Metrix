<template>
  <n-config-provider :theme="appStore.dark ? darkTheme : null">
    <n-message-provider>
      <n-dialog-provider>
        <router-view />
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { darkTheme, NConfigProvider, NDialogProvider, NMessageProvider } from "naive-ui";

import { appStore } from "./stores/app";
</script>
