<template>
  <span class="status-tag" :class="statusClass">{{ label }}</span>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { t } from "../i18n";

const props = defineProps<{
  status: string | boolean;
  labels?: Record<string, string>;
}>();

const label = computed(() => {
  if (typeof props.status === "boolean") {
    const custom = props.labels?.[String(props.status)];
    if (custom) {
      return custom;
    }
    return props.status ? t("common.enabled") : t("common.disabled");
  }
  return props.labels?.[props.status] || props.status;
});

const statusClass = computed(() => {
  if (props.status === true || props.status === "approved" || props.status === "read") {
    return "success";
  }
  if (props.status === false || props.status === "rejected") {
    return "danger";
  }
  return "warning";
});
</script>
