<template>
  <n-modal :show="show" preset="card" class="modal-card container-log-modal" :title="title" @update:show="$emit('update:show', $event)">
    <div class="container-log-toolbar">
      <n-input-number v-model:value="tailValue" :min="1" :max="5000" :show-button="false" />
      <n-button :loading="loading" @click="loadLogs">{{ t("common.refresh") }}</n-button>
      <n-button :disabled="!logs" @click="copyLogs">{{ t("common.copy") }}</n-button>
    </div>
    <n-input class="container-log-content" type="textarea" readonly :value="logs" :autosize="{ minRows: 18, maxRows: 24 }" />
  </n-modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { NButton, NInput, NInputNumber, NModal, useMessage } from "naive-ui";

import { t } from "../../../i18n";
import { copyText } from "../../../utils/clipboard";
import { showError } from "../../../utils/message";
import { getContainerLogs, type ContainerItem } from "../api";

const props = defineProps<{ show: boolean; container: ContainerItem | null }>();
const emit = defineEmits<{ "update:show": [value: boolean] }>();

const message = useMessage();
const loading = ref(false);
const logs = ref("");
const tailValue = ref(200);
const title = computed(() => t("container.logTitle", { name: props.container?.name || "" }));

watch(
  () => props.show,
  (show) => {
    if (show) void loadLogs();
  }
);

async function loadLogs() {
  if (!props.container) return;
  loading.value = true;
  try {
    logs.value = (await getContainerLogs(props.container.id, tailValue.value || 200)).logs;
  } catch (error) {
    showError(message, error);
  } finally {
    loading.value = false;
  }
}

async function copyLogs() {
  await copyText(logs.value);
  message.success(t("common.copied"));
}
</script>

<style scoped>
.container-log-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.container-log-toolbar .n-input-number {
  width: 120px;
}

.container-log-content :deep(textarea) {
  font-family: Consolas, Monaco, "Courier New", monospace;
}
</style>
