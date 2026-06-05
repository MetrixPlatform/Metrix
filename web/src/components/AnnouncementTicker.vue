<template>
  <div class="announcement-ticker" role="status">
    <n-icon class="announcement-ticker-icon" :component="MegaphoneLoud20Regular" />
    <div class="announcement-ticker-viewport">
      <div :key="currentItem?.id" class="announcement-ticker-text">
        <strong>{{ currentItem?.title }}</strong>
        <span>{{ currentItem?.content }}</span>
      </div>
    </div>
    <n-button v-if="closable && currentItem" quaternary circle size="small" :title="t('announcement.closeTicker')" @click="emitClose">
      <template #icon><n-icon :component="Dismiss20Regular" /></template>
    </n-button>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { Dismiss20Regular, MegaphoneLoud20Regular } from "@vicons/fluent";
import { NButton, NIcon } from "naive-ui";

import { t } from "../i18n";

interface TickerItem {
  id: number;
  title: string;
  content: string;
}

const props = defineProps<{
  items: TickerItem[];
  closable?: boolean;
}>();
const emit = defineEmits<{
  close: [item: TickerItem];
}>();

const activeIndex = ref(0);
let timer = 0;

const currentItem = computed(() => props.items[activeIndex.value] || props.items[0] || null);

watch(
  () => props.items.length,
  () => {
    activeIndex.value = 0;
    restartTimer();
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  window.clearInterval(timer);
});

function restartTimer() {
  window.clearInterval(timer);
  if (props.items.length <= 1) return;
  timer = window.setInterval(() => {
    activeIndex.value = (activeIndex.value + 1) % props.items.length;
  }, 9000);
}

function emitClose() {
  if (currentItem.value) {
    emit("close", currentItem.value);
  }
}
</script>
