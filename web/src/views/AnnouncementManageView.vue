<template>
  <section class="work-card table-page-card announcement-manage-card">
    <div class="toolbar announcement-toolbar">
      <div class="announcement-filter-row">
        <n-input v-model:value="filters.keyword" class="filter-keyword" :placeholder="t('announcement.searchPlaceholder')" clearable />
        <n-date-picker
          v-model:value="filters.time_range"
          class="filter-date-range"
          type="datetimerange"
          clearable
          :start-placeholder="t('common.startTime')"
          :end-placeholder="t('common.endTime')"
        />
        <n-button @click="searchAnnouncements">{{ t("common.search") }}</n-button>
      </div>
      <div class="toolbar-group announcement-actions">
        <permission-button
          class="announcement-batch-delete-button"
          permission="action:announcement:delete"
          type="error"
          :disabled="selectedDeletableIds.length === 0"
          @click="removeSelectedAnnouncements"
        >
          {{ batchDeleteText }}
        </permission-button>
        <permission-button class="announcement-create-button" permission="action:announcement:create" type="primary" @click="openCreate">{{ t("announcement.add") }}</permission-button>
      </div>
    </div>
    <n-data-table
      v-model:checked-row-keys="checkedRowKeys"
      class="page-data-table"
      flex-height
      :columns="columns"
      :data="announcements"
      :loading="loading"
      :pagination="pagination"
      :row-key="(row) => row.id"
      :scroll-x="tableScrollX"
      remote
      @unstable-column-resize="handleColumnResize"
      @update:filters="handleTableFilters"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
      @update:sorter="handleSorter"
    />

    <n-modal v-model:show="showModal" preset="card" class="modal-card announcement-edit-modal" :title="editing ? t('announcement.edit') : t('announcement.add')">
      <n-form ref="formRef" class="form-stack inline-form" :model="form" :rules="rules" label-placement="left" label-width="auto">
        <n-form-item :label="t('field.title')" path="title">
          <n-input v-model:value="form.title" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('field.content')" path="content">
          <n-input v-model:value="form.content" type="textarea" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('field.targetType')">
          <n-select v-model:value="form.target_type" :options="targetTypeOptions" placeholder="" />
        </n-form-item>
        <n-form-item v-if="form.target_type === 'permission'" :label="t('field.permissionCode')">
          <n-input v-model:value="form.target_value" :placeholder="t('announcement.permissionTargetPlaceholder')" />
        </n-form-item>
        <n-form-item v-if="form.target_type === 'company'" :label="t('field.company')">
          <n-input v-model:value="form.target_value" placeholder="" />
        </n-form-item>
        <template v-if="form.target_type === 'company_department'">
          <n-form-item :label="t('field.company')">
            <n-input v-model:value="targetCompany" placeholder="" />
          </n-form-item>
          <n-form-item :label="t('field.departmentOrPosition')">
            <n-input v-model:value="targetDepartment" placeholder="" />
          </n-form-item>
        </template>
        <n-form-item v-if="form.target_type === 'user'" :label="t('field.username')">
          <n-input v-model:value="form.target_value" type="textarea" :placeholder="t('announcement.userTargetPlaceholder')" />
        </n-form-item>
        <n-form-item :label="t('field.displayModes')" path="display_modes">
          <n-checkbox-group v-model:value="form.display_modes">
            <n-space>
              <n-checkbox value="popup">{{ t("announcement.displayPopup") }}</n-checkbox>
              <n-checkbox value="ticker">{{ t("announcement.displayTicker") }}</n-checkbox>
              <n-checkbox value="sidebar">{{ t("announcement.displaySidebar") }}</n-checkbox>
            </n-space>
          </n-checkbox-group>
        </n-form-item>
        <n-form-item :label="t('common.enabled')">
          <n-switch v-model:value="form.is_active" />
        </n-form-item>
        <div class="form-actions">
          <n-button @click="showModal = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" @click="saveAnnouncement">{{ t("common.save") }}</n-button>
        </div>
      </n-form>
    </n-modal>
  </section>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from "vue";
import { Delete20Regular, Edit20Regular } from "@vicons/fluent";
import {
  NButton,
  NCheckbox,
  NCheckboxGroup,
  NDataTable,
  NDatePicker,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NModal,
  NSelect,
  NSpace,
  NSwitch,
  useDialog,
  useMessage
} from "naive-ui";
import type { DataTableColumns, DataTableFilterState, DataTableRowKey, DataTableSortState, FormInst, FormRules } from "naive-ui";

import {
  batchDeleteAnnouncements,
  createAnnouncement,
  deleteAnnouncement,
  listAnnouncements,
  updateAnnouncement,
  type AnnouncementPayload
} from "../api/announcements";
import type { AnnouncementItem, AnnouncementTargetType } from "../api/types";
import PermissionButton from "../components/PermissionButton.vue";
import StatusTag from "../components/StatusTag.vue";
import { formatDateTime, t } from "../i18n";
import { authStore } from "../stores/auth";
import { messageText, showError } from "../utils/message";
import { singleFilterValue, sumColumnWidths, updateColumnWidth, withResizableColumns } from "../utils/table";
import { maxLengthRule, requiredRule, validateForm } from "../utils/validation";

const message = useMessage();
const dialog = useDialog();
const loading = ref(false);
const announcements = ref<AnnouncementItem[]>([]);
const checkedRowKeys = ref<DataTableRowKey[]>([]);
const showModal = ref(false);
const editing = ref<AnnouncementItem | null>(null);
const formRef = ref<FormInst | null>(null);
const targetCompany = ref("");
const targetDepartment = ref("");
type AnnouncementDisplayMode = "popup" | "ticker" | "sidebar";
type AnnouncementStatusFilter = "true" | "false";
type AnnouncementCreatorFilter = "all" | "me";
const filters = reactive<{
  keyword: string;
  target_type: AnnouncementTargetType | null;
  display_mode: AnnouncementDisplayMode | null;
  is_active: AnnouncementStatusFilter | null;
  created_by: AnnouncementCreatorFilter | null;
  sort_order: "ascend" | "descend";
  time_range: [number, number] | null;
}>({
  keyword: "",
  target_type: null,
  display_mode: null,
  is_active: null,
  created_by: null,
  sort_order: "descend",
  time_range: null
});
const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  pageSizes: [20, 50, 100, 500],
  showSizePicker: true,
  prefix: ({ itemCount }: { itemCount: number | undefined }) => t("common.total", { count: itemCount ?? 0 })
});
const form = reactive<AnnouncementPayload & { display_modes: string[] }>({
  title: "",
  content: "",
  target_type: "all",
  target_value: "",
  show_popup: false,
  show_ticker: false,
  show_sidebar: true,
  is_active: true,
  display_modes: ["sidebar"]
});
const rules = computed<FormRules>(() => ({
  title: [requiredRule(t("field.title")), maxLengthRule(t("field.title"), 120)],
  content: [requiredRule(t("field.content")), maxLengthRule(t("field.content"), 2000)],
  display_modes: {
    validator: () => form.display_modes.length > 0,
    message: t("validation.displayModeRequired"),
    trigger: "change"
  }
}));

const targetTypeOptions = computed(() => [
  { label: t("announcement.targetAll"), value: "all" },
  { label: t("announcement.targetAuthenticated"), value: "authenticated" },
  { label: t("announcement.targetPermission"), value: "permission" },
  { label: t("announcement.targetCompany"), value: "company" },
  { label: t("announcement.targetCompanyDepartment"), value: "company_department" },
  { label: t("announcement.targetUser"), value: "user" }
]);
const displayModeOptions = computed(() => [
  { label: t("announcement.displayPopup"), value: "popup" },
  { label: t("announcement.displayTicker"), value: "ticker" },
  { label: t("announcement.displaySidebar"), value: "sidebar" }
]);
const statusOptions = computed(() => [
  { label: t("common.enabled"), value: "true" },
  { label: t("common.disabled"), value: "false" }
]);
const creatorOptions = computed(() => [
  { label: t("announcement.creatorAll"), value: "all" },
  { label: t("announcement.creatorMe"), value: "me" }
]);
const announcementColumnWidths = reactive<Record<string, number>>({
  selection: 48,
  title: 180,
  targetType: 180,
  displayMode: 150,
  status: 90,
  creator: 120,
  createdAt: 170,
  actions: 130
});
const announcementColumnWidthKeys: Record<string, string> = {
  title: "title",
  target_type: "targetType",
  display_mode: "displayMode",
  is_active: "status",
  created_by: "creator",
  created_at: "createdAt"
};
const ANNOUNCEMENT_UPDATE = "action:announcement:update";
const ANNOUNCEMENT_DELETE = "action:announcement:delete";
const ANNOUNCEMENT_MANAGE_OTHERS = "action:announcement:manage_others";
const tableScrollX = computed(() =>
  authStore.has(ANNOUNCEMENT_DELETE)
    ? sumColumnWidths(announcementColumnWidths)
    : sumColumnWidths(announcementColumnWidths) - announcementColumnWidths.selection
);

const selectedDeletableIds = computed(() =>
  checkedRowKeys.value.filter((id): id is number => {
    if (typeof id !== "number") return false;
    const row = announcements.value.find((item) => item.id === id);
    return Boolean(row && canDeleteAnnouncement(row));
  })
);
const batchDeleteText = computed(() =>
  selectedDeletableIds.value.length > 0
    ? t("announcement.batchDeleteCount", { count: selectedDeletableIds.value.length })
    : t("announcement.batchDelete")
);

const columns = computed<DataTableColumns<AnnouncementItem>>(() => {
  const dataColumns: DataTableColumns<AnnouncementItem> = [
    { title: t("field.title"), key: "title", width: announcementColumnWidths.title },
    {
      title: t("field.targetType"),
      key: "target_type",
      width: announcementColumnWidths.targetType,
      filter: (value, row) => row.target_type === value,
      filterMultiple: false,
      filterOptionValue: filters.target_type,
      filterOptions: targetTypeOptions.value,
      render: (row) => targetLabel(row)
    },
    {
      title: t("field.displayModes"),
      key: "display_mode",
      width: announcementColumnWidths.displayMode,
      filter: (value, row) => matchesDisplayMode(row, value),
      filterMultiple: false,
      filterOptionValue: filters.display_mode,
      filterOptions: displayModeOptions.value,
      render: (row) => displayLabel(row)
    },
    {
      title: t("field.status"),
      key: "is_active",
      width: announcementColumnWidths.status,
      filter: (value, row) => row.is_active === (value === "true"),
      filterMultiple: false,
      filterOptionValue: filters.is_active,
      filterOptions: statusOptions.value,
      render: (row) => h(StatusTag, { status: row.is_active })
    },
    {
      title: t("field.creator"),
      key: "created_by",
      width: announcementColumnWidths.creator,
      filter: () => true,
      filterMultiple: false,
      filterOptionValue: filters.created_by,
      filterOptions: creatorOptions.value,
      render: (row) => row.created_by_username || t("common.none")
    },
    {
      title: t("field.createdAt"),
      key: "created_at",
      width: announcementColumnWidths.createdAt,
      sorter: true,
      sortOrder: filters.sort_order,
      render: (row) => formatTime(row.created_at)
    },
    {
      title: t("common.actions"),
      key: "actions",
      width: announcementColumnWidths.actions,
      fixed: "right",
      render: (row) =>
        h(
          "div",
          { class: "table-action-group" },
          [
            canUpdateAnnouncement(row)
              ? h(
                  NButton,
                  { size: "small", quaternary: true, circle: true, title: t("common.edit"), onClick: () => openEdit(row) },
                  { icon: () => h(NIcon, { component: Edit20Regular }) }
                )
              : null,
            canDeleteAnnouncement(row)
              ? h(
                  NButton,
                  { size: "small", quaternary: true, circle: true, title: t("common.delete"), type: "error", onClick: () => removeAnnouncement(row) },
                  { icon: () => h(NIcon, { component: Delete20Regular }) }
                )
              : null
          ].filter(Boolean)
        )
    }
  ];
  const visibleColumns = authStore.has(ANNOUNCEMENT_DELETE)
    ? [{ type: "selection" as const, width: announcementColumnWidths.selection, disabled: (row: AnnouncementItem) => !canDeleteAnnouncement(row) }, ...dataColumns]
    : dataColumns;
  return withResizableColumns(visibleColumns);
});

onMounted(async () => {
  await loadAnnouncements();
});

async function loadAnnouncements() {
  loading.value = true;
  try {
    const result = await listAnnouncements({
      keyword: filters.keyword,
      target_type: filters.target_type || "",
      display_mode: filters.display_mode || "",
      is_active: filters.is_active ? filters.is_active === "true" : null,
      created_by: filters.created_by || "",
      sort_order: filters.sort_order,
      start_time: filters.time_range ? new Date(filters.time_range[0]).toISOString() : "",
      end_time: filters.time_range ? new Date(filters.time_range[1]).toISOString() : "",
      page: pagination.page,
      page_size: pagination.pageSize
    });
    announcements.value = result.items;
    pagination.itemCount = result.total;
    pagination.page = result.page;
    pagination.pageSize = result.page_size;
    checkedRowKeys.value = checkedRowKeys.value.filter((key) => {
      const row = announcements.value.find((item) => item.id === key);
      return Boolean(row && canDeleteAnnouncement(row));
    });
  } catch (error) {
    showError(message, error);
  } finally {
    loading.value = false;
  }
}

function searchAnnouncements() {
  pagination.page = 1;
  void loadAnnouncements();
}

function handleTableFilters(filterState: DataTableFilterState) {
  const targetType = singleFilterValue(filterState, "target_type");
  const displayMode = singleFilterValue(filterState, "display_mode");
  const activeStatus = singleFilterValue(filterState, "is_active");
  const creator = singleFilterValue(filterState, "created_by");
  filters.target_type = isTargetType(targetType) ? targetType : null;
  filters.display_mode = isDisplayMode(displayMode) ? displayMode : null;
  filters.is_active = isStatusFilter(activeStatus) ? activeStatus : null;
  filters.created_by = isCreatorFilter(creator) ? creator : null;
  pagination.page = 1;
  void loadAnnouncements();
}

function handleSorter(sortState: DataTableSortState | DataTableSortState[] | null) {
  const state = Array.isArray(sortState) ? sortState[0] : sortState;
  filters.sort_order = state?.order === "ascend" ? "ascend" : "descend";
  pagination.page = 1;
  void loadAnnouncements();
}

function handlePageChange(page: number) {
  pagination.page = page;
  void loadAnnouncements();
}

function handlePageSizeChange(pageSize: number) {
  pagination.pageSize = pageSize;
  pagination.page = 1;
  void loadAnnouncements();
}

function handleColumnResize(_: number, limitedWidth: number, column: { key?: string | number }) {
  updateColumnWidth(announcementColumnWidths, column.key, announcementColumnWidthKeys, limitedWidth);
}

function isTargetType(value: unknown): value is AnnouncementTargetType {
  return typeof value === "string" && targetTypeOptions.value.some((option) => option.value === value);
}

function isDisplayMode(value: unknown): value is AnnouncementDisplayMode {
  return typeof value === "string" && displayModeOptions.value.some((option) => option.value === value);
}

function isStatusFilter(value: unknown): value is AnnouncementStatusFilter {
  return value === "true" || value === "false";
}

function isCreatorFilter(value: unknown): value is AnnouncementCreatorFilter {
  return value === "all" || value === "me";
}

function canManageAnnouncement(row: AnnouncementItem) {
  return row.created_by === authStore.user?.id || authStore.has(ANNOUNCEMENT_MANAGE_OTHERS);
}

function canUpdateAnnouncement(row: AnnouncementItem) {
  return authStore.has(ANNOUNCEMENT_UPDATE) && canManageAnnouncement(row);
}

function canDeleteAnnouncement(row: AnnouncementItem) {
  return authStore.has(ANNOUNCEMENT_DELETE) && canManageAnnouncement(row);
}

function openCreate() {
  editing.value = null;
  targetCompany.value = "";
  targetDepartment.value = "";
  Object.assign(form, {
    title: "",
    content: "",
    target_type: "all" as AnnouncementTargetType,
    target_value: "",
    show_popup: false,
    show_ticker: false,
    show_sidebar: true,
    is_active: true,
    display_modes: ["sidebar"]
  });
  showModal.value = true;
}

function openEdit(row: AnnouncementItem) {
  editing.value = row;
  const [company, department] = row.target_type === "company_department" ? splitCompanyDepartment(row.target_value) : ["", ""];
  targetCompany.value = company;
  targetDepartment.value = department;
  Object.assign(form, {
    title: row.title,
    content: row.content,
    target_type: row.target_type,
    target_value: row.target_type === "company_department" ? "" : row.target_value,
    show_popup: row.show_popup,
    show_ticker: row.show_ticker,
    show_sidebar: row.show_sidebar,
    is_active: row.is_active,
    display_modes: [
      row.show_popup ? "popup" : "",
      row.show_ticker ? "ticker" : "",
      row.show_sidebar ? "sidebar" : ""
    ].filter(Boolean)
  });
  showModal.value = true;
}

async function saveAnnouncement() {
  if (!(await validateForm(formRef.value))) return;
  const payload = buildPayload();
  if (!payload) return;
  try {
    if (editing.value) {
      await updateAnnouncement(editing.value.id, payload);
    } else {
      await createAnnouncement(payload);
    }
    showModal.value = false;
    await loadAnnouncements();
    message.success(t("announcement.saved"));
  } catch (error) {
    showError(message, error);
  }
}

function buildPayload(): AnnouncementPayload | null {
  const modes = new Set(form.display_modes);
  const targetValue = normalizedTargetValue();
  if (!["all", "authenticated"].includes(form.target_type) && !targetValue) {
    message.error(t("announcement.targetRequired"));
    return null;
  }
  if (modes.size === 0) {
    message.error(t("validation.displayModeRequired"));
    return null;
  }
  return {
    title: form.title,
    content: form.content,
    target_type: form.target_type,
    target_value: targetValue,
    show_popup: modes.has("popup"),
    show_ticker: modes.has("ticker"),
    show_sidebar: modes.has("sidebar"),
    is_active: form.is_active
  };
}

function normalizedTargetValue() {
  if (form.target_type === "all" || form.target_type === "authenticated") return "";
  if (form.target_type === "company_department") {
    return targetCompany.value.trim() && targetDepartment.value.trim()
      ? `${targetCompany.value.trim()}|${targetDepartment.value.trim()}`
      : "";
  }
  return form.target_value.trim();
}

function removeAnnouncement(row: AnnouncementItem) {
  dialog.warning({
    title: t("announcement.deleteTitle"),
    content: t("announcement.deleteConfirm", { title: row.title }),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: async () => {
      try {
        const result = await deleteAnnouncement(row.id);
        await loadAnnouncements();
        message.success(messageText(result, "announcement.deleted"));
      } catch (error) {
        showError(message, error);
      }
    }
  });
}

function removeSelectedAnnouncements() {
  const ids = selectedDeletableIds.value;
  if (ids.length === 0) return;
  dialog.warning({
    title: t("announcement.batchDeleteTitle"),
    content: t("announcement.batchDeleteConfirm", { count: ids.length }),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: async () => {
      try {
        const result = await batchDeleteAnnouncements(ids);
        checkedRowKeys.value = [];
        await loadAnnouncements();
        message.success(messageText(result, "announcement.batchDeleted"));
      } catch (error) {
        showError(message, error);
      }
    }
  });
}

function targetLabel(row: AnnouncementItem) {
  const labels: Record<AnnouncementTargetType, string> = {
    all: t("announcement.targetAll"),
    authenticated: t("announcement.targetAuthenticated"),
    permission: t("announcement.targetPermissionShort"),
    company: t("announcement.targetCompanyShort"),
    company_department: t("announcement.targetCompanyDepartmentShort"),
    user: t("announcement.targetUserShort")
  };
  return ["all", "authenticated"].includes(row.target_type)
    ? labels[row.target_type]
    : `${labels[row.target_type]}${t("common.labelSeparator")}${formatTargetValue(row)}`;
}

function displayLabel(row: AnnouncementItem) {
  return [
    row.show_popup ? t("announcement.displayPopup") : "",
    row.show_ticker ? t("announcement.displayTicker") : "",
    row.show_sidebar ? t("announcement.displaySidebar") : ""
  ].filter(Boolean).join(t("common.listSeparator"));
}

function matchesDisplayMode(row: AnnouncementItem, value: unknown) {
  if (value === "popup") return row.show_popup;
  if (value === "ticker") return row.show_ticker;
  if (value === "sidebar") return row.show_sidebar;
  return true;
}

function formatTargetValue(row: AnnouncementItem) {
  if (row.target_type !== "company_department") return row.target_value;
  const [company, department] = splitCompanyDepartment(row.target_value);
  return `${company} - ${department}`;
}

function splitCompanyDepartment(value: string) {
  const [company = "", department = ""] = value.split("|");
  return [company, department];
}

function formatTime(value: string) {
  return formatDateTime(value);
}
</script>
