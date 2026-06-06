<template>
  <div class="brand-mark">
    <img class="brand-logo" :src="logoUrl" :alt="appName" />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { settingsStore } from "../stores/settings";

const logoUrl = "/favicon.svg";
const appName = computed(() => settingsStore.appName());
</script>
