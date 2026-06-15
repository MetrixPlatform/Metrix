<template>
  <n-modal :show="show" preset="card" class="modal-card container-create-modal" :title="t('container.create')" @update:show="$emit('update:show', $event)">
    <n-form ref="formRef" class="form-stack inline-form" :model="form" :rules="rules" label-placement="left" label-width="auto">
      <n-form-item :label="t('container.field.name')" path="name">
        <n-input v-model:value="form.name" />
      </n-form-item>
      <n-form-item :label="t('container.field.image')" path="image">
        <n-select v-model:value="form.image" filterable tag :options="imageOptions" />
      </n-form-item>
      <n-form-item :label="t('container.field.command')" path="command">
        <n-input v-model:value="form.command" />
      </n-form-item>
      <n-form-item :label="t('container.field.env')">
        <n-input v-model:value="envText" type="textarea" :placeholder="t('container.envPlaceholder')" :autosize="{ minRows: 3, maxRows: 6 }" />
      </n-form-item>
      <n-form-item :label="t('container.field.portsConfig')">
        <n-input v-model:value="portsText" type="textarea" :placeholder="t('container.portPlaceholder')" :autosize="{ minRows: 2, maxRows: 5 }" />
      </n-form-item>
      <n-form-item :label="t('container.field.volumes')">
        <n-input v-model:value="volumesText" type="textarea" :placeholder="t('container.volumePlaceholder')" :autosize="{ minRows: 2, maxRows: 5 }" />
      </n-form-item>
      <n-form-item :label="t('container.field.restartPolicy')">
        <n-select v-model:value="form.restart_policy" :options="restartPolicyOptions" />
      </n-form-item>
      <n-form-item :label="t('container.field.memoryLimit')">
        <n-input-number v-model:value="form.memory_limit_mb" :min="16" :show-button="false" clearable />
      </n-form-item>
      <n-form-item :label="t('container.field.cpuLimit')">
        <n-input-number v-model:value="form.cpu_limit" :min="0.1" :step="0.1" :show-button="false" clearable />
      </n-form-item>
      <n-form-item :label="t('container.field.autoStart')">
        <n-switch v-model:value="form.auto_start" />
      </n-form-item>
    </n-form>
    <template #action>
      <div class="form-actions modal-fixed-actions">
        <n-button @click="$emit('update:show', false)">{{ t("common.cancel") }}</n-button>
        <n-button type="primary" :loading="saving" @click="submit">{{ t("common.save") }}</n-button>
      </div>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { NButton, NForm, NFormItem, NInput, NInputNumber, NModal, NSelect, NSwitch, useMessage } from "naive-ui";
import type { FormInst, FormRules } from "naive-ui";

import { t } from "../../../i18n";
import { showError } from "../../../utils/message";
import { requiredRule, validateForm } from "../../../utils/validation";
import { createContainer, type ContainerCreatePayload, type ContainerPortMapping, type ImageItem } from "../api";

const props = defineProps<{ show: boolean; images: ImageItem[] }>();
const emit = defineEmits<{ "update:show": [value: boolean]; saved: [] }>();

const message = useMessage();
const formRef = ref<FormInst | null>(null);
const saving = ref(false);
const envText = ref("");
const portsText = ref("");
const volumesText = ref("");
const form = reactive<ContainerCreatePayload>({
  name: "",
  image: "",
  command: "",
  env: {},
  ports: [],
  volumes: [],
  restart_policy: "no",
  memory_limit_mb: null,
  cpu_limit: null,
  auto_start: false
});
const rules: FormRules = {
  name: [requiredRule(t("container.field.name"))],
  image: [requiredRule(t("container.field.image"))]
};
const imageOptions = computed(() =>
  props.images.flatMap((image) => (image.repo_tags.length ? image.repo_tags : [image.id]).map((tag) => ({ label: tag, value: tag })))
);
const restartPolicyOptions = [
  { label: "no", value: "no" },
  { label: "always", value: "always" },
  { label: "unless-stopped", value: "unless-stopped" },
  { label: "on-failure", value: "on-failure" }
];

watch(
  () => props.show,
  (show) => {
    if (show) resetForm();
  }
);

async function submit() {
  if (!(await validateForm(formRef.value))) return;
  saving.value = true;
  try {
    await createContainer({
      ...form,
      env: parseEnv(envText.value),
      ports: parsePorts(portsText.value),
      volumes: parseVolumes(volumesText.value)
    });
    message.success(t("container.created"));
    emit("update:show", false);
    emit("saved");
  } catch (error) {
    showError(message, error);
  } finally {
    saving.value = false;
  }
}

function resetForm() {
  form.name = "";
  form.image = imageOptions.value[0]?.value ?? "";
  form.command = "";
  form.env = {};
  form.ports = [];
  form.volumes = [];
  form.restart_policy = "no";
  form.memory_limit_mb = null;
  form.cpu_limit = null;
  form.auto_start = false;
  envText.value = "";
  portsText.value = "";
  volumesText.value = "";
}

function parseEnv(text: string) {
  return Object.fromEntries(
    text
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const index = line.indexOf("=");
        return index > 0 ? [line.slice(0, index).trim(), line.slice(index + 1)] : [line, ""];
      })
  );
}

function parsePorts(text: string): ContainerPortMapping[] {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [host, rest = ""] = line.split(":");
      const [containerPort, protocol = "tcp"] = rest.split("/");
      const parsedProtocol: "tcp" | "udp" = protocol === "udp" ? "udp" : "tcp";
      return { host_port: Number(host) || null, container_port: containerPort || host, protocol: parsedProtocol };
    });
}

function parseVolumes(text: string) {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [volumeName, containerPath, mode = "rw"] = line.split(":");
      return { volume_name: volumeName || "", container_path: containerPath || "", read_only: mode === "ro" };
    });
}
</script>
