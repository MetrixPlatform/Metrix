<template>
  <n-button v-if="authStore.has(permission)" v-bind="$attrs">
    <template v-if="$slots.icon" #icon>
      <slot name="icon" />
    </template>
    <slot />
  </n-button>
</template>

<script setup lang="ts">
import { NButton } from "naive-ui";

import { authStore } from "../stores/auth";

defineProps<{ permission: string }>();
</script>
