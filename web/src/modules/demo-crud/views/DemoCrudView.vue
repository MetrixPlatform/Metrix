<template>
  <section class="work-card table-page-card">
    <div class="toolbar">
      <div class="toolbar-group">
        <n-input v-model:value="filters.keyword" class="filter-keyword" :placeholder="t('demoCrud.searchPlaceholder')" clearable />
        <n-input v-model:value="filters.category" :placeholder="t('demoCrud.categoryPlaceholder')" clearable />
        <n-button @click="searchItems">{{ t("common.search") }}</n-button>
      </div>
      <permission-button :permission="DEMO_ITEM_CREATE" type="primary" @click="openCreate">{{ t("demoCrud.add") }}</permission-button>
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

    <n-modal v-model:show="showModal" preset="card" class="modal-card" :title="editingItem ? t('demoCrud.edit') : t('demoCrud.add')">
      <n-form ref="formRef" class="form-stack inline-form" :model="form" :rules="rules" label-placement="left" label-width="auto">
        <n-form-item :label="t('demoCrud.field.name')" path="name">
          <n-input v-model:value="form.name" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('demoCrud.field.category')" path="category">
          <n-input v-model:value="form.category" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('demoCrud.field.description')" path="description">
          <n-input v-model:value="form.description" type="textarea" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('field.status')" path="is_active">
          <n-switch v-model:value="form.is_active">
            <template #checked>{{ t("common.enabled") }}</template>
            <template #unchecked>{{ t("common.disabled") }}</template>
          </n-switch>
        </n-form-item>
        <div class="form-actions">
          <n-button @click="showModal = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" @click="saveItem">{{ t("common.save") }}</n-button>
        </div>
      </n-form>
    </n-modal>
  </section>
</template>

<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from "vue";
import { NButton, NDataTable, NForm, NFormItem, NInput, NModal, NSpace, NSwitch, useDialog, useMessage } from "naive-ui";
import type { DataTableColumns, DataTableFilterState, DataTableSortState, FormInst, FormRules } from "naive-ui";

import PermissionButton from "../../../components/PermissionButton.vue";
import StatusTag from "../../../components/StatusTag.vue";
import { formatDateTime, t } from "../../../i18n";
import { authStore } from "../../../stores/auth";
import { messageText, showError } from "../../../utils/message";
import { singleFilterValue, sumColumnWidths, updateColumnWidth, withResizableColumns } from "../../../utils/table";
import { maxLengthRule, requiredRule, validateForm } from "../../../utils/validation";
import { createDemoItem, deleteDemoItem, listDemoItems, updateDemoItem, type DemoItem, type DemoItemPayload } from "../api";
import { DEMO_ITEM_CREATE, DEMO_ITEM_DELETE, DEMO_ITEM_MANAGE_OTHERS, DEMO_ITEM_UPDATE } from "../permissions";

type ActiveFilter = "true" | "false";
type CreatorFilter = "all" | "me";

const message = useMessage();
const dialog = useDialog();
const loading = ref(false);
const showModal = ref(false);
const formRef = ref<FormInst | null>(null);
const editingItem = ref<DemoItem | null>(null);
const items = ref<DemoItem[]>([]);
const filters = reactive<{
  keyword: string;
  category: string;
  is_active: ActiveFilter | null;
  created_by: CreatorFilter | null;
  sort_order: "ascend" | "descend";
}>({
  keyword: "",
  category: "",
  is_active: null,
  created_by: null,
  sort_order: "descend"
});
const form = reactive<DemoItemPayload>({
  name: "",
  category: "",
  description: "",
  is_active: true
});
const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  pageSizes: [20, 50, 100, 500],
  showSizePicker: true,
  prefix: ({ itemCount }: { itemCount: number | undefined }) => t("common.total", { count: itemCount ?? 0 })
});
const rules = computed<FormRules>(() => ({
  name: [requiredRule(t("demoCrud.field.name")), maxLengthRule(t("demoCrud.field.name"), 120)],
  category: maxLengthRule(t("demoCrud.field.category"), 80),
  description: maxLengthRule(t("demoCrud.field.description"), 1000)
}));
const activeOptions = computed(() => [
  { label: t("common.enabled"), value: "true" },
  { label: t("common.disabled"), value: "false" }
]);
const creatorOptions = computed(() => [
  { label: t("demoCrud.creatorAll"), value: "all" },
  { label: t("demoCrud.creatorMe"), value: "me" }
]);
const columnWidths = reactive<Record<string, number>>({
  name: 180,
  category: 140,
  description: 240,
  isActive: 100,
  creator: 140,
  createdAt: 170,
  actions: 128
});
const columnWidthKeys: Record<string, string> = {
  name: "name",
  category: "category",
  description: "description",
  is_active: "isActive",
  created_by_username: "creator",
  created_at: "createdAt"
};
const tableScrollX = computed(() => sumColumnWidths(columnWidths));
const statusLabels = computed(() => ({ true: t("common.enabled"), false: t("common.disabled") }));
const columns = computed<DataTableColumns<DemoItem>>(() =>
  withResizableColumns([
    { title: t("demoCrud.field.name"), key: "name", width: columnWidths.name },
    { title: t("demoCrud.field.category"), key: "category", width: columnWidths.category },
    { title: t("demoCrud.field.description"), key: "description", ellipsis: { tooltip: true }, width: columnWidths.description },
    {
      title: t("field.status"),
      key: "is_active",
      width: columnWidths.isActive,
      filter: (value, row) => row.is_active === (value === "true"),
      filterMultiple: false,
      filterOptionValue: filters.is_active,
      filterOptions: activeOptions.value,
      render: (row) => h(StatusTag, { status: row.is_active, labels: statusLabels.value })
    },
    {
      title: t("field.creator"),
      key: "created_by_username",
      width: columnWidths.creator,
      filter: () => true,
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
      align: "center",
      render: (row) =>
        h(NSpace, { size: 6, wrap: false, justify: "center" }, () => [
          authStore.has(DEMO_ITEM_UPDATE) && canManage(row)
            ? h(NButton, { size: "small", quaternary: true, onClick: () => openEdit(row) }, () => t("common.edit"))
            : null,
          authStore.has(DEMO_ITEM_DELETE) && canManage(row)
            ? h(NButton, { size: "small", quaternary: true, type: "error", onClick: () => confirmDelete(row) }, () => t("common.delete"))
            : null
        ])
    }
  ])
);

onMounted(loadItems);

async function loadItems() {
  loading.value = true;
  try {
    const result = await listDemoItems({
      keyword: filters.keyword,
      category: filters.category,
      is_active: filters.is_active ? filters.is_active === "true" : null,
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

function searchItems() {
  pagination.page = 1;
  void loadItems();
}

function handlePageChange(page: number) {
  pagination.page = page;
  void loadItems();
}

function handlePageSizeChange(pageSize: number) {
  pagination.pageSize = pageSize;
  pagination.page = 1;
  void loadItems();
}

function handleTableFilters(filterState: DataTableFilterState) {
  const active = singleFilterValue(filterState, "is_active");
  const creator = singleFilterValue(filterState, "created_by_username");
  filters.is_active = isActiveFilter(active) ? active : null;
  filters.created_by = isCreatorFilter(creator) ? creator : null;
  pagination.page = 1;
  void loadItems();
}

function handleSorter(sortState: DataTableSortState | DataTableSortState[] | null) {
  const state = Array.isArray(sortState) ? sortState[0] : sortState;
  filters.sort_order = state?.order === "ascend" ? "ascend" : "descend";
  pagination.page = 1;
  void loadItems();
}

function handleColumnResize(_: number, limitedWidth: number, column: { key?: string | number }) {
  updateColumnWidth(columnWidths, column.key, columnWidthKeys, limitedWidth);
}

function openCreate() {
  editingItem.value = null;
  Object.assign(form, { name: "", category: "", description: "", is_active: true });
  showModal.value = true;
}

function openEdit(item: DemoItem) {
  editingItem.value = item;
  Object.assign(form, {
    name: item.name,
    category: item.category,
    description: item.description,
    is_active: item.is_active
  });
  showModal.value = true;
}

async function saveItem() {
  if (!(await validateForm(formRef.value))) return;
  try {
    if (editingItem.value) {
      await updateDemoItem(editingItem.value.id, form);
    } else {
      await createDemoItem(form);
    }
    showModal.value = false;
    await loadItems();
    message.success(t("demoCrud.saved"));
  } catch (error) {
    showError(message, error);
  }
}

function confirmDelete(item: DemoItem) {
  dialog.warning({
    title: t("demoCrud.deleteTitle"),
    content: t("demoCrud.deleteConfirm", { name: item.name }),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: () => void removeItem(item)
  });
}

async function removeItem(item: DemoItem) {
  try {
    const result = await deleteDemoItem(item.id);
    await loadItems();
    message.success(messageText(result, "demoCrud.deleted"));
  } catch (error) {
    showError(message, error);
  }
}

function canManage(item: DemoItem) {
  return item.created_by === authStore.user?.id || authStore.has(DEMO_ITEM_MANAGE_OTHERS);
}

function isActiveFilter(value: unknown): value is ActiveFilter {
  return value === "true" || value === "false";
}

function isCreatorFilter(value: unknown): value is CreatorFilter {
  return value === "all" || value === "me";
}
</script>
