<template>
  <script-workbench-view v-if="workingItem" :project="workingItem" @close="closeWorkbench" />

  <section v-else class="work-card table-page-card">
    <div class="toolbar">
      <div class="storage-filter-row">
        <n-input
          v-model:value="filters.keyword"
          class="filter-keyword"
          :placeholder="t('script.searchPlaceholder')"
          clearable
          @clear="searchProjects"
          @keyup.enter="searchProjects"
        />
        <n-button @click="searchProjects">{{ t("common.search") }}</n-button>
      </div>
      <permission-button :permission="SCRIPT_CREATE" type="primary" @click="openCreate">{{ t("script.add") }}</permission-button>
    </div>

    <n-data-table
      class="page-data-table"
      flex-height
      remote
      :columns="columns"
      :data="items"
      :loading="loading"
      :pagination="pagination"
      :row-key="(row) => row.id"
      :scroll-x="tableScrollX"
      @unstable-column-resize="handleColumnResize"
      @update:filters="handleTableFilters"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
      @update:sorter="handleSorter"
    />

    <n-modal v-model:show="showModal" preset="card" class="modal-card script-modal-card" :title="editingItem ? t('script.edit') : t('script.add')">
      <n-form ref="formRef" class="form-stack inline-form" :model="form" :rules="rules" label-placement="left" label-width="auto">
        <n-form-item :label="t('script.field.name')" path="name">
          <n-input v-model:value="form.name" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('script.field.image')" path="base_image">
          <n-select
            v-model:value="form.base_image"
            filterable
            tag
            :options="imageOptions"
            :placeholder="t('script.imagePlaceholder')"
            @update:value="handleImageChange"
          />
        </n-form-item>
        <p v-if="!imagesAvailable" class="script-modal-hint">{{ t("script.dockerUnavailable") }}</p>
        <n-form-item :label="t('script.field.language')" path="language">
          <n-select v-model:value="form.language" :options="languageOptions" />
        </n-form-item>
        <n-form-item :label="t('script.field.runCommand')" path="run_command">
          <n-input v-model:value="form.run_command" :placeholder="t('script.runCommandPlaceholder')" />
        </n-form-item>
        <n-form-item :label="t('script.field.network')" path="network_mode">
          <n-radio-group v-model:value="form.network_mode">
            <n-radio-button value="bridge" :label="t('script.network.bridge')" />
            <n-radio-button value="none" :label="t('script.network.none')" />
          </n-radio-group>
        </n-form-item>
        <n-form-item :label="t('script.field.shared')" path="is_shared">
          <n-switch v-model:value="form.is_shared" />
          <span class="script-shared-hint">{{ t("script.sharedHint") }}</span>
        </n-form-item>
        <n-form-item :label="t('script.field.cpu')" path="cpu_limit">
          <n-input-number v-model:value="form.cpu_limit" :min="0.1" :max="256" :step="0.5" :show-button="false" clearable :placeholder="t('script.unlimited')" />
        </n-form-item>
        <n-form-item :label="t('script.field.memory')" path="memory_limit_mb">
          <n-input-number v-model:value="form.memory_limit_mb" :min="16" :max="1048576" :show-button="false" clearable :placeholder="t('script.unlimited')" />
        </n-form-item>
        <n-form-item :label="t('script.field.timeout')" path="timeout_seconds">
          <n-input-number v-model:value="form.timeout_seconds" :min="0" :max="86400" :show-button="false" :placeholder="t('script.timeoutHint')" />
        </n-form-item>
        <n-form-item :label="t('script.field.env')" path="env">
          <n-input v-model:value="envText" type="textarea" :autosize="{ minRows: 2, maxRows: 6 }" :placeholder="t('script.envHint')" />
        </n-form-item>
        <n-form-item :label="t('script.field.description')" path="description">
          <n-input v-model:value="form.description" type="textarea" :autosize="{ minRows: 1, maxRows: 3 }" placeholder="" />
        </n-form-item>
        <n-form-item v-if="!editingItem" :label="t('script.uploadCode')">
          <div class="script-upload-field">
            <n-button size="small" @click="pickCreateFile">{{ t("script.chooseFile") }}</n-button>
            <span class="script-upload-name">{{ createFileName || t("script.uploadCodeHint") }}</span>
            <input ref="createFileInput" type="file" class="script-upload-input" @change="onCreateFileChange" />
          </div>
        </n-form-item>
      </n-form>
      <template #action>
        <div class="form-actions modal-fixed-actions">
          <n-button @click="showModal = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" :loading="saving" @click="saveProject">{{ t("common.save") }}</n-button>
        </div>
      </template>
    </n-modal>

    <script-run-history-modal v-model:show="showHistory" :project="historyProject" />
  </section>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref, type Component } from "vue";
import {
  Code20Regular,
  Copy20Regular,
  Delete20Regular,
  Edit20Regular,
  History20Regular,
  MoreHorizontal20Regular,
  Play20Regular
} from "@vicons/fluent";
import {
  NButton,
  NDataTable,
  NDropdown,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NInputNumber,
  NModal,
  NRadioButton,
  NRadioGroup,
  NSelect,
  NSwitch,
  NTag,
  useDialog,
  useMessage
} from "naive-ui";
import type { DataTableColumns, DataTableFilterState, DataTableSortState, DropdownOption, FormInst, FormRules, SelectOption } from "naive-ui";

import PermissionButton from "../../../components/PermissionButton.vue";
import { formatDateTime, t } from "../../../i18n";
import { authStore } from "../../../stores/auth";
import { copyText } from "../../../utils/clipboard";
import { messageText, showError } from "../../../utils/message";
import { singleFilterValue, sumColumnWidths, updateColumnWidth, withResizableColumns } from "../../../utils/table";
import { maxLengthRule, numberRequiredRule, requiredRule, validateForm } from "../../../utils/validation";
import {
  createScript,
  deleteScript,
  getScriptRun,
  listScriptImages,
  listScripts,
  submitScriptRun,
  updateScript,
  uploadScriptFile,
  type AvailableImages,
  type ScriptNetworkMode,
  type ScriptProject,
  type ScriptProjectPayload
} from "../api";
import ScriptRunHistoryModal from "../components/ScriptRunHistoryModal.vue";
import ScriptWorkbenchView from "./ScriptWorkbenchView.vue";
import { SCRIPT_CREATE, SCRIPT_DELETE, SCRIPT_MANAGE_OTHERS, SCRIPT_OPERATE, SCRIPT_UPDATE } from "../permissions";

type CreatorFilter = "all" | "me";
type NetworkFilter = ScriptNetworkMode;

const LANGUAGES = ["python", "node", "go", "shell", "custom"];

const message = useMessage();
const dialog = useDialog();
const loading = ref(false);
const saving = ref(false);
const showModal = ref(false);
const formRef = ref<FormInst | null>(null);
const editingItem = ref<ScriptProject | null>(null);
const workingItem = ref<ScriptProject | null>(null);
const items = ref<ScriptProject[]>([]);
const envText = ref("");
const showHistory = ref(false);
const historyProject = ref<ScriptProject | null>(null);
// Projects whose run was triggered from the list and is still running (keeps the run icon spinning).
const runningIds = ref<number[]>([]);
const createFileInput = ref<HTMLInputElement | null>(null);
const createFile = ref<File | null>(null);
const createFileName = ref("");
const images = reactive<AvailableImages>({ presets: [], local_images: [], docker_available: true, message: "" });
const imagesAvailable = computed(() => images.docker_available);
const filters = reactive<{
  keyword: string;
  language: string | null;
  network_mode: NetworkFilter | null;
  created_by: CreatorFilter | null;
  sort_order: "ascend" | "descend";
}>({
  keyword: "",
  language: null,
  network_mode: null,
  created_by: null,
  sort_order: "descend"
});
const form = reactive<ScriptProjectPayload>({
  name: "",
  description: "",
  language: "python",
  base_image: "",
  network_mode: "bridge",
  is_shared: false,
  run_command: "",
  env: {},
  cpu_limit: null,
  memory_limit_mb: null,
  timeout_seconds: 0
});
const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  pageSizes: [20, 50, 100, 500],
  showSizePicker: true,
  prefix: ({ itemCount }: { itemCount: number | undefined }) => t("common.total", { count: itemCount ?? 0 })
});
const columnWidths = reactive<Record<string, number>>({
  name: 170,
  slug: 150,
  language: 100,
  image: 210,
  network: 110,
  creator: 120,
  createdAt: 170,
  actions: 130
});
const columnWidthKeys: Record<string, string> = {
  name: "name",
  slug: "slug",
  language: "language",
  base_image: "image",
  network_mode: "network",
  created_by_username: "creator",
  created_at: "createdAt"
};
const tableScrollX = computed(() => sumColumnWidths(columnWidths));
const languageOptions = computed(() => LANGUAGES.map((value) => ({ label: t(`script.language.${value}`), value })));
const networkOptions = computed(() => [
  { label: t("script.network.bridge"), value: "bridge" },
  { label: t("script.network.none"), value: "none" }
]);
const creatorOptions = computed(() => [
  { label: t("script.creatorAll"), value: "all" },
  { label: t("script.creatorMe"), value: "me" }
]);
const imageOptions = computed<SelectOption[]>(() => {
  const options: SelectOption[] = [];
  const presetImages = new Set<string>();
  for (const preset of images.presets) {
    presetImages.add(preset.image);
    options.push({
      label: preset.available ? `${preset.image} · ${preset.language}` : `${preset.image} (${t("script.imageMissing")})`,
      value: preset.image,
      disabled: !preset.available
    });
  }
  for (const local of images.local_images) {
    if (!presetImages.has(local.image)) {
      options.push({ label: local.image, value: local.image });
    }
  }
  return options;
});
const rules = computed<FormRules>(() => ({
  name: [requiredRule(t("script.field.name")), maxLengthRule(t("script.field.name"), 120)],
  base_image: [requiredRule(t("script.field.image")), maxLengthRule(t("script.field.image"), 500)],
  language: requiredRule(t("script.field.language")),
  timeout_seconds: numberRequiredRule(t("script.field.timeout"))
}));
const columns = computed<DataTableColumns<ScriptProject>>(() =>
  withResizableColumns([
  {
    title: t("script.field.name"),
    key: "name",
    width: columnWidths.name,
    ellipsis: { tooltip: true },
    render: (row) =>
      canManage(row)
        ? h("span", { class: "storage-name-link", title: row.name, onClick: () => openWorkbench(row) }, row.name)
        : h("span", { title: row.name }, row.name)
  },
  {
    title: t("script.field.slug"),
    key: "slug",
    width: columnWidths.slug,
    render: (row) =>
      h("span", { class: "copyable-cell" }, [
        h("code", null, row.slug),
        h(
          NButton,
          { size: "tiny", quaternary: true, circle: true, title: t("common.copy"), onClick: () => void copySlug(row.slug) },
          { icon: () => h(NIcon, { component: Copy20Regular }) }
        )
      ])
  },
  {
    title: t("script.field.language"),
    key: "language",
    width: columnWidths.language,
    filter: true,
    filterMultiple: false,
    filterOptionValue: filters.language,
    filterOptions: languageOptions.value,
    render: (row) => h(NTag, { size: "small", bordered: false }, () => row.language)
  },
  { title: t("script.field.image"), key: "base_image", width: columnWidths.image, ellipsis: { tooltip: true } },
  {
    title: t("script.field.network"),
    key: "network_mode",
    width: columnWidths.network,
    filter: true,
    filterMultiple: false,
    filterOptionValue: filters.network_mode,
    filterOptions: networkOptions.value,
    render: (row) =>
      h(NTag, { size: "small", bordered: false, type: row.network_mode === "bridge" ? "info" : "default" }, () =>
        row.network_mode === "bridge" ? t("script.network.bridge") : t("script.network.none")
      )
  },
  {
    title: t("field.creator"),
    key: "created_by_username",
    width: columnWidths.creator,
    filter: true,
    filterMultiple: false,
    filterOptionValue: filters.created_by,
    filterOptions: creatorOptions.value,
    render: (row) => row.created_by_username || t("common.none")
  },
  {
    title: t("field.createdAt"),
    key: "created_at",
    width: columnWidths.createdAt,
    sorter: true,
    sortOrder: filters.sort_order,
    render: (row) => formatDateTime(row.created_at)
  },
  {
    title: t("common.actions"),
    key: "actions",
    width: columnWidths.actions,
    fixed: "right",
    render: (row) =>
      h(
        "div",
        { class: "table-action-group" },
        [
          authStore.has(SCRIPT_OPERATE)
            ? h(
                NButton,
                {
                  size: "small",
                  quaternary: true,
                  circle: true,
                  type: "primary",
                  loading: isRunning(row.id),
                  disabled: !row.run_command || isRunning(row.id),
                  title: row.run_command ? t("script.run") : t("script.runCommandMissing"),
                  onClick: () => void runFromList(row)
                },
                { icon: () => h(NIcon, { component: Play20Regular }) }
              )
            : null,
          h(
            NButton,
            { size: "small", quaternary: true, circle: true, title: t("script.tab.history"), onClick: () => openHistory(row) },
            { icon: () => h(NIcon, { component: History20Regular }) }
          ),
          renderMoreMenu(row)
        ].filter(Boolean)
      )
  }
  ])
);

onMounted(loadProjects);

async function loadProjects() {
  loading.value = true;
  try {
    const result = await listScripts({
      keyword: filters.keyword,
      language: filters.language || "",
      network_mode: filters.network_mode || "",
      created_by: filters.created_by || "",
      sort_order: filters.sort_order,
      page: pagination.page,
      page_size: pagination.pageSize
    });
    items.value = result.items;
    pagination.itemCount = result.total;
    pagination.page = result.page;
    pagination.pageSize = result.page_size;
  } catch (error) {
    showError(message, error);
  } finally {
    loading.value = false;
  }
}

async function loadImages() {
  try {
    const result = await listScriptImages();
    images.presets = result.presets;
    images.local_images = result.local_images;
    images.docker_available = result.docker_available;
    images.message = result.message;
  } catch (error) {
    showError(message, error);
  }
}

function searchProjects() {
  pagination.page = 1;
  void loadProjects();
}

function handlePageChange(page: number) {
  pagination.page = page;
  void loadProjects();
}

function handlePageSizeChange(pageSize: number) {
  pagination.pageSize = pageSize;
  pagination.page = 1;
  void loadProjects();
}

function handleTableFilters(filterState: DataTableFilterState) {
  const language = singleFilterValue(filterState, "language");
  const network = singleFilterValue(filterState, "network_mode");
  const creator = singleFilterValue(filterState, "created_by_username");
  filters.language = typeof language === "string" && language ? language : null;
  filters.network_mode = network === "bridge" || network === "none" ? network : null;
  filters.created_by = creator === "all" || creator === "me" ? creator : null;
  pagination.page = 1;
  void loadProjects();
}

function handleSorter(sortState: DataTableSortState | DataTableSortState[] | null) {
  const state = Array.isArray(sortState) ? sortState[0] : sortState;
  filters.sort_order = state?.order === "ascend" ? "ascend" : "descend";
  pagination.page = 1;
  void loadProjects();
}

function handleColumnResize(_: number, limitedWidth: number, column: { key?: string | number }) {
  updateColumnWidth(columnWidths, column.key, columnWidthKeys, limitedWidth);
}

function resetForm() {
  Object.assign(form, {
    name: "",
    description: "",
    language: "python",
    base_image: "",
    network_mode: "bridge",
    is_shared: false,
    run_command: "",
    env: {},
    cpu_limit: null,
    memory_limit_mb: null,
    timeout_seconds: 0
  });
  envText.value = "";
  createFile.value = null;
  createFileName.value = "";
}

function openCreate() {
  editingItem.value = null;
  resetForm();
  showModal.value = true;
  void loadImages();
}

function openEdit(item: ScriptProject) {
  editingItem.value = item;
  Object.assign(form, {
    name: item.name,
    description: item.description,
    language: item.language,
    base_image: item.base_image,
    network_mode: item.network_mode,
    is_shared: item.is_shared,
    run_command: item.run_command,
    env: { ...item.env },
    cpu_limit: item.cpu_limit,
    memory_limit_mb: item.memory_limit_mb,
    timeout_seconds: item.timeout_seconds
  });
  envText.value = dictToEnvText(item.env);
  showModal.value = true;
  void loadImages();
}

function handleImageChange(image: string) {
  const preset = images.presets.find((item) => item.image === image);
  if (!preset) return;
  form.language = preset.language;
  if (!form.run_command) {
    form.run_command = preset.run_command;
  }
}

function openWorkbench(item: ScriptProject) {
  workingItem.value = item;
}

function closeWorkbench() {
  workingItem.value = null;
  void loadProjects();
}

async function saveProject() {
  if (!(await validateForm(formRef.value))) return;
  form.env = envTextToDict(envText.value);
  saving.value = true;
  try {
    if (editingItem.value) {
      await updateScript(editingItem.value.id, { ...form });
    } else {
      const created = await createScript({ ...form });
      if (createFile.value) {
        await uploadScriptFile(created.id, "/", createFile.value);
      }
    }
    showModal.value = false;
    await loadProjects();
    message.success(t("script.saved"));
  } catch (error) {
    showError(message, error);
  } finally {
    saving.value = false;
  }
}

function confirmDelete(item: ScriptProject) {
  dialog.warning({
    title: t("script.deleteTitle"),
    content: t("script.deleteConfirm", { name: item.name }),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: () => void removeProject(item)
  });
}

async function removeProject(item: ScriptProject) {
  try {
    const result = await deleteScript(item.id);
    await loadProjects();
    message.success(messageText(result, "script.deleted"));
  } catch (error) {
    showError(message, error);
  }
}

async function copySlug(slug: string) {
  try {
    await copyText(slug);
    message.success(t("common.copied"));
  } catch {
    message.error(t("message.operationFailed"));
  }
}

function canManage(item: ScriptProject) {
  return item.created_by === authStore.user?.id || authStore.has(SCRIPT_MANAGE_OTHERS);
}

function renderIcon(component: Component) {
  return () => h(NIcon, { component });
}

// Run and run-history stay as standalone icons; everything else (workbench/edit/delete)
// is collapsed into this "more" dropdown, and only shown to users who can manage the script.
function moreOptions(item: ScriptProject): DropdownOption[] {
  if (!canManage(item)) return [];
  const options: DropdownOption[] = [{ key: "manage", label: t("script.manage"), icon: renderIcon(Code20Regular) }];
  if (authStore.has(SCRIPT_UPDATE)) options.push({ key: "edit", label: t("common.edit"), icon: renderIcon(Edit20Regular) });
  if (authStore.has(SCRIPT_DELETE)) options.push({ key: "delete", label: t("common.delete"), icon: renderIcon(Delete20Regular) });
  return options;
}

function renderMoreMenu(item: ScriptProject) {
  const options = moreOptions(item);
  if (!options.length) return null;
  return h(
    NDropdown,
    { trigger: "hover", options, onSelect: (key: string) => handleMoreSelect(key, item) },
    {
      default: () =>
        h(
          NButton,
          { size: "small", quaternary: true, circle: true, title: t("common.moreActions") },
          { icon: () => h(NIcon, { component: MoreHorizontal20Regular }) }
        )
    }
  );
}

function handleMoreSelect(key: string, item: ScriptProject) {
  if (key === "manage") openWorkbench(item);
  else if (key === "edit") openEdit(item);
  else if (key === "delete") confirmDelete(item);
}

function isRunning(id: number) {
  return runningIds.value.includes(id);
}

// Keep the run icon spinning from submit until the run actually finishes (not just submitted).
async function runFromList(item: ScriptProject) {
  if (isRunning(item.id)) return;
  runningIds.value = [...runningIds.value, item.id];
  try {
    const submitted = await submitScriptRun(item.id);
    message.success(t("script.runStarted"));
    await waitForRunFinished(submitted.run_id);
  } catch (error) {
    showError(message, error);
  } finally {
    runningIds.value = runningIds.value.filter((id) => id !== item.id);
  }
}

async function waitForRunFinished(runId: string) {
  const terminal = new Set(["success", "failed", "timeout", "canceled"]);
  for (let attempt = 0; attempt < 1800; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 2000));
    try {
      const run = await getScriptRun(runId);
      if (terminal.has(run.status)) return;
    } catch {
      return;
    }
  }
}

function openHistory(item: ScriptProject) {
  historyProject.value = item;
  showHistory.value = true;
}

function pickCreateFile() {
  createFileInput.value?.click();
}

function onCreateFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  input.value = "";
  createFile.value = file;
  createFileName.value = file?.name ?? "";
}

function envTextToDict(text: string): Record<string, string> {
  const result: Record<string, string> = {};
  for (const line of text.split("\n")) {
    const trimmed = line.trim();
    const index = trimmed.indexOf("=");
    if (!trimmed || index <= 0) continue;
    result[trimmed.slice(0, index).trim()] = trimmed.slice(index + 1).trim();
  }
  return result;
}

function dictToEnvText(env: Record<string, string>): string {
  return Object.entries(env)
    .map(([key, value]) => `${key}=${value}`)
    .join("\n");
}
</script>

<style scoped>
.script-shared-hint {
  margin-left: 10px;
  color: var(--text-color-3);
  font-size: 12px;
}

.script-upload-field {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.script-upload-name {
  color: var(--text-color-3);
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.script-upload-input {
  display: none;
}
</style>
