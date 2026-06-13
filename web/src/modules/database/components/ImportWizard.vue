<template>
  <n-modal :show="show" preset="card" class="modal-card" :title="t('database.import.title')" @update:show="emit('update:show', $event)">
    <n-form class="form-stack inline-form" label-placement="left" label-width="auto">
      <n-form-item :label="t('field.file')">
        <input type="file" accept=".csv,.xlsx,.sqlite,.db,.sql" @change="handleFile" />
      </n-form-item>
      <n-form-item :label="t('field.format')">
        <n-select v-model:value="form.format" :options="formatOptions" />
      </n-form-item>
      <n-form-item :label="t('field.database')">
        <n-input v-model:value="form.database" placeholder="" />
      </n-form-item>
      <n-form-item :label="t('field.table')">
        <n-input v-model:value="form.target_table" :placeholder="t('database.import.tableHint')" />
      </n-form-item>
      <n-form-item :label="t('database.import.mode')">
        <n-select v-model:value="form.mode" :options="modeOptions" />
      </n-form-item>
      <n-form-item :label="t('database.import.createTable')">
        <n-switch v-model:value="form.create_table" />
      </n-form-item>
    </n-form>
    <template #action>
      <div class="form-actions modal-fixed-actions">
        <n-button @click="emit('update:show', false)">{{ t("common.cancel") }}</n-button>
        <n-button type="primary" :loading="submitting" @click="submit">{{ t("database.import.submit") }}</n-button>
      </div>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { NButton, NForm, NFormItem, NInput, NModal, NSelect, NSwitch, useMessage } from "naive-ui";

import { t } from "../../../i18n";
import { showError } from "../../../utils/message";
import { submitImport, type DataFormat } from "../api";

const props = defineProps<{
  show: boolean;
  connId: string;
  database: string;
  table: string;
}>();
const emit = defineEmits<{ (event: "update:show", value: boolean): void; (event: "submitted", jobId: string): void }>();

const message = useMessage();
const submitting = ref(false);
const file = ref<File | null>(null);
const form = reactive({
  format: "csv" as DataFormat,
  database: props.database,
  target_table: props.table,
  mode: "append",
  create_table: false
});
const formatOptions = [
  { label: "CSV", value: "csv" },
  { label: "XLSX", value: "xlsx" },
  { label: "SQLite", value: "sqlite" },
  { label: "SQL", value: "sql" }
];
const modeOptions = [
  { label: t("database.import.append"), value: "append" },
  { label: t("database.import.overwrite"), value: "overwrite" },
  { label: t("database.import.upsert"), value: "upsert" }
];

function handleFile(event: Event) {
  const input = event.target as HTMLInputElement;
  file.value = input.files?.[0] || null;
}

async function submit() {
  if (!file.value) {
    message.warning(t("database.import.fileRequired"));
    return;
  }
  submitting.value = true;
  try {
    const result = await submitImport(props.connId, {
      file: file.value,
      format: form.format,
      database: form.database,
      target_table: form.target_table,
      mode: form.mode,
      create_table: form.create_table
    });
    emit("submitted", result.job_id);
    emit("update:show", false);
  } catch (error) {
    showError(message, error);
  } finally {
    submitting.value = false;
  }
}
</script>
