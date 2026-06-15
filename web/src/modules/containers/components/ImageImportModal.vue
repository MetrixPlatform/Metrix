<template>
  <n-modal :show="show" preset="card" class="modal-card" :title="t('container.importImage')" @update:show="$emit('update:show', $event)">
    <div class="form-stack">
      <n-upload :max="1" accept=".tar,application/x-tar,application/octet-stream" :default-upload="false" @change="handleChange">
        <n-upload-dragger>
          <div>{{ t("container.uploadTar") }}</div>
        </n-upload-dragger>
      </n-upload>
      <n-progress v-if="progress > 0 && progress < 100" type="line" :percentage="progress" />
    </div>
    <template #action>
      <div class="form-actions modal-fixed-actions">
        <n-button @click="$emit('update:show', false)">{{ t("common.cancel") }}</n-button>
        <n-button type="primary" :loading="uploading" :disabled="!file" @click="submit">{{ t("container.importImage") }}</n-button>
      </div>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { NButton, NModal, NProgress, NUpload, NUploadDragger, useMessage } from "naive-ui";
import type { UploadFileInfo } from "naive-ui";

import { t } from "../../../i18n";
import { showError } from "../../../utils/message";
import { importImage } from "../api";

defineProps<{ show: boolean }>();
const emit = defineEmits<{ "update:show": [value: boolean]; submitted: [] }>();

const message = useMessage();
const file = ref<File | null>(null);
const uploading = ref(false);
const progress = ref(0);

function handleChange(options: { fileList: UploadFileInfo[] }) {
  const uploadFile = options.fileList.at(-1);
  file.value = (uploadFile?.file as File | undefined) ?? null;
}

async function submit() {
  if (!file.value) return;
  uploading.value = true;
  progress.value = 0;
  try {
    await importImage(file.value, (event) => {
      progress.value = event.percent;
    });
    message.success(t("container.submitted"));
    emit("update:show", false);
    emit("submitted");
  } catch (error) {
    showError(message, error);
  } finally {
    uploading.value = false;
  }
}
</script>
