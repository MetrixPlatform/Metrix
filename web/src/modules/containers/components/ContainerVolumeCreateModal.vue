<template>
  <n-modal :show="show" preset="card" class="modal-card" :title="t('container.createVolume')" @update:show="$emit('update:show', $event)">
    <n-form ref="formRef" class="form-stack inline-form" :model="form" :rules="rules" label-placement="left" label-width="auto">
      <n-form-item :label="t('container.field.volumeName')" path="name">
        <n-input v-model:value="form.name" />
      </n-form-item>
      <n-form-item :label="t('container.field.driver')" path="driver">
        <n-input v-model:value="form.driver" />
      </n-form-item>
    </n-form>
    <template #action>
      <div class="form-actions modal-fixed-actions">
        <n-button @click="$emit('update:show', false)">{{ t("common.cancel") }}</n-button>
        <n-button type="primary" :loading="saving" @click="submit">{{ t("common.create") }}</n-button>
      </div>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import { NButton, NForm, NFormItem, NInput, NModal, useMessage } from "naive-ui";
import type { FormInst, FormRules } from "naive-ui";

import { t } from "../../../i18n";
import { showError } from "../../../utils/message";
import { requiredRule, validateForm } from "../../../utils/validation";
import { createVolume } from "../api";

const props = defineProps<{ show: boolean }>();
const emit = defineEmits<{ "update:show": [value: boolean]; saved: [] }>();

const message = useMessage();
const formRef = ref<FormInst | null>(null);
const saving = ref(false);
const form = reactive({ name: "", driver: "local" });
const rules: FormRules = {
  name: [requiredRule(t("container.field.volumeName"))],
  driver: [requiredRule(t("container.field.driver"))]
};

watch(
  () => props.show,
  (show) => {
    if (show) {
      form.name = "";
      form.driver = "local";
    }
  }
);

async function submit() {
  if (!(await validateForm(formRef.value))) return;
  saving.value = true;
  try {
    await createVolume({ name: form.name, driver: form.driver || "local" });
    message.success(t("container.volumeCreated"));
    emit("update:show", false);
    emit("saved");
  } catch (error) {
    showError(message, error);
  } finally {
    saving.value = false;
  }
}
</script>
