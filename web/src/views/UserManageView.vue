<template>
  <section class="work-card table-page-card">
    <div class="toolbar user-toolbar">
      <div class="user-filter-row">
        <n-input v-model:value="filters.keyword" class="filter-keyword" :placeholder="t('user.searchPlaceholder')" clearable />
        <n-date-picker
          v-model:value="filters.time_range"
          class="filter-date-range"
          type="datetimerange"
          clearable
          :start-placeholder="t('common.startTime')"
          :end-placeholder="t('common.endTime')"
        />
        <n-button @click="searchUsers">{{ t("common.search") }}</n-button>
      </div>
      <permission-button class="user-create-button" permission="action:user:create" type="primary" @click="openCreate">{{ t("user.add") }}</permission-button>
    </div>
    <n-data-table
      class="page-data-table"
      flex-height
      :columns="columns"
      :data="users"
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
    <n-modal v-model:show="showApproveModal" preset="card" class="modal-card" :title="t('user.approveTitle')">
      <n-checkbox-group v-model:value="roleIds">
        <n-space>
          <n-checkbox v-for="role in roles" :key="role.id" :value="role.id">{{ roleName(role) }}</n-checkbox>
        </n-space>
      </n-checkbox-group>
      <div class="form-actions">
        <n-button @click="showApproveModal = false">{{ t("common.cancel") }}</n-button>
        <n-button type="primary" @click="saveApprove">{{ t("user.pass") }}</n-button>
      </div>
    </n-modal>
    <n-modal v-model:show="showRejectModal" preset="card" class="modal-card" :title="t('user.rejectTitle')">
      <n-form ref="rejectFormRef" class="inline-form" :model="rejectForm" :rules="rejectRules" label-placement="left" label-width="auto">
        <n-form-item :label="t('field.reason')" path="reason">
          <n-input v-model:value="rejectForm.reason" type="textarea" />
        </n-form-item>
      </n-form>
      <div class="form-actions">
        <n-button @click="showRejectModal = false">{{ t("common.cancel") }}</n-button>
        <n-button type="error" @click="saveReject">{{ t("user.reject") }}</n-button>
      </div>
    </n-modal>
    <n-modal v-model:show="showUserModal" preset="card" class="modal-card" :title="editingUser ? t('user.edit') : t('user.add')">
      <n-form ref="userFormRef" class="form-stack inline-form" :model="userForm" :rules="userRules" label-placement="left" label-width="auto">
        <n-form-item v-if="!editingUser" :label="t('field.username')" path="username">
          <n-input v-model:value="userForm.username" />
        </n-form-item>
        <n-form-item v-if="!editingUser" :label="t('field.password')" path="password">
          <n-input v-model:value="userForm.password" type="password" show-password-on="click" />
        </n-form-item>
        <n-form-item :label="t('field.fullName')" path="full_name">
          <n-input v-model:value="userForm.full_name" />
        </n-form-item>
        <n-form-item :label="t('field.phone')" path="phone">
          <n-input v-model:value="userForm.phone" />
        </n-form-item>
        <n-form-item :label="t('field.email')" path="email">
          <n-input v-model:value="userForm.email" />
        </n-form-item>
        <n-form-item :label="t('field.company')" path="company">
          <n-input v-model:value="userForm.company" />
        </n-form-item>
        <n-form-item :label="t('field.department')" path="department">
          <n-input v-model:value="userForm.department" />
        </n-form-item>
        <n-form-item v-if="!editingUser" :label="t('field.role')">
          <n-checkbox-group v-model:value="roleIds">
            <n-space>
              <n-checkbox v-for="role in roles" :key="role.id" :value="role.id">{{ roleName(role) }}</n-checkbox>
            </n-space>
          </n-checkbox-group>
        </n-form-item>
        <div class="form-actions">
          <n-button @click="showUserModal = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" @click="saveUser">{{ t("common.save") }}</n-button>
        </div>
      </n-form>
    </n-modal>
    <n-modal v-model:show="showRoleModal" preset="card" class="modal-card" :title="t('user.assignRoles')">
      <n-checkbox-group v-model:value="roleIds">
        <n-space>
          <n-checkbox v-for="role in roles" :key="role.id" :value="role.id">{{ roleName(role) }}</n-checkbox>
        </n-space>
      </n-checkbox-group>
      <div class="form-actions">
        <n-button @click="showRoleModal = false">{{ t("common.cancel") }}</n-button>
        <n-button type="primary" @click="saveRoles">{{ t("common.save") }}</n-button>
      </div>
    </n-modal>
    <n-modal v-model:show="showPasswordModal" preset="card" class="modal-card" :title="t('user.resetPassword')">
      <n-form ref="passwordFormRef" class="form-stack inline-form" :model="passwordForm" :rules="passwordRules" label-placement="left" label-width="auto">
        <n-form-item :label="t('field.newPassword')" path="password">
          <n-input v-model:value="passwordForm.password" type="password" show-password-on="click" />
        </n-form-item>
        <div class="form-actions">
          <n-button @click="showPasswordModal = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" @click="savePassword">{{ t("common.save") }}</n-button>
        </div>
      </n-form>
    </n-modal>
  </section>
</template>

<script setup lang="ts">
import { MoreHorizontal20Regular } from "@vicons/fluent";
import { computed, h, onMounted, reactive, ref } from "vue";
import {
  NButton,
  NCheckbox,
  NCheckboxGroup,
  NDataTable,
  NDatePicker,
  NDropdown,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NModal,
  NSpace,
  useDialog,
  useMessage
} from "naive-ui";
import type { DataTableColumns, DataTableFilterState, DataTableSortState, DropdownOption, FormInst, FormRules } from "naive-ui";

import { approveUser, assignRoles, createUser, deleteUser, disableUser, enableUser, listUserRoleOptions, listUsers, rejectUser, resetPassword, updateUser } from "../api/users";
import type { RoleBrief, UserListItem } from "../api/types";
import PermissionButton from "../components/PermissionButton.vue";
import StatusTag from "../components/StatusTag.vue";
import { formatDateTime, t } from "../i18n";
import { roleName } from "../i18n/builtins";
import { authStore } from "../stores/auth";
import { messageText, showError } from "../utils/message";
import { singleFilterValue, sumColumnWidths, updateColumnWidth, withResizableColumns } from "../utils/table";
import { emailRule, maxLengthRule, minLengthRule, phoneRule, requiredRule, validateForm } from "../utils/validation";

const message = useMessage();
const dialog = useDialog();
const loading = ref(false);
const userFormRef = ref<FormInst | null>(null);
const passwordFormRef = ref<FormInst | null>(null);
const rejectFormRef = ref<FormInst | null>(null);
const users = ref<UserListItem[]>([]);
const roles = ref<RoleBrief[]>([]);
const showApproveModal = ref(false);
const showRejectModal = ref(false);
const showUserModal = ref(false);
const showRoleModal = ref(false);
const showPasswordModal = ref(false);
const editingUser = ref<UserListItem | null>(null);
const approvalTarget = ref<UserListItem | null>(null);
const roleTarget = ref<UserListItem | null>(null);
const passwordTarget = ref<UserListItem | null>(null);
const roleIds = ref<number[]>([]);
const passwordForm = reactive({ password: "" });
const rejectForm = reactive({ reason: "" });
type UserApprovalFilter = "pending" | "approved" | "rejected";
type UserActiveFilter = "true" | "false";
const filters = reactive<{
  keyword: string;
  approval_status: UserApprovalFilter | null;
  is_active: UserActiveFilter | null;
  sort_order: "ascend" | "descend";
  time_range: [number, number] | null;
}>({
  keyword: "",
  approval_status: null,
  is_active: null,
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
const userForm = reactive({
  username: "",
  password: "",
  full_name: "",
  phone: "",
  email: "",
  company: "",
  department: ""
});
const userRules = computed<FormRules>(() => ({
  username: [requiredRule(t("field.username")), minLengthRule(t("field.username"), 3), maxLengthRule(t("field.username"), 64)],
  password: [requiredRule(t("field.password")), minLengthRule(t("field.password"), 6), maxLengthRule(t("field.password"), 128)],
  full_name: [requiredRule(t("field.fullName")), maxLengthRule(t("field.fullName"), 80)],
  phone: [requiredRule(t("field.phone")), phoneRule()],
  email: [requiredRule(t("field.email")), emailRule(), maxLengthRule(t("field.email"), 254)],
  company: maxLengthRule(t("field.company"), 120),
  department: maxLengthRule(t("field.department"), 120)
}));
const passwordRules = computed<FormRules>(() => ({
  password: [requiredRule(t("field.newPassword")), minLengthRule(t("field.newPassword"), 6), maxLengthRule(t("field.newPassword"), 128)]
}));
const rejectRules = computed<FormRules>(() => ({
  reason: maxLengthRule(t("field.reason"), 500)
}));
const adminRoleId = computed(() => roles.value.find((role) => role.code === "admin")?.id ?? null);
const needsRoleOptions = computed(() => authStore.has("action:user:create") || authStore.has("action:user:operate"));

const approvalOptions = computed(() => [
  { label: t("status.pending"), value: "pending" },
  { label: t("status.approved"), value: "approved" },
  { label: t("status.rejected"), value: "rejected" }
]);
const activeOptions = computed(() => [
  { label: t("common.enabled"), value: "true" },
  { label: t("common.disabled"), value: "false" }
]);
const userColumnWidths = reactive<Record<string, number>>({
  username: 130,
  fullName: 120,
  phone: 130,
  email: 200,
  company: 140,
  department: 120,
  approval: 100,
  status: 90,
  roles: 160,
  createdAt: 170,
  actions: 72
});
const userColumnWidthKeys: Record<string, string> = {
  username: "username",
  full_name: "fullName",
  phone: "phone",
  email: "email",
  company: "company",
  department: "department",
  approval_status: "approval",
  is_active: "status",
  roles: "roles",
  created_at: "createdAt"
};
const tableScrollX = computed(() => sumColumnWidths(userColumnWidths));

const columns = computed<DataTableColumns<UserListItem>>(() =>
  withResizableColumns([
    { title: t("field.username"), key: "username", width: userColumnWidths.username },
    { title: t("field.fullName"), key: "full_name", width: userColumnWidths.fullName },
    { title: t("field.phone"), key: "phone", width: userColumnWidths.phone },
    { title: t("field.email"), key: "email", width: userColumnWidths.email },
    { title: t("field.company"), key: "company", width: userColumnWidths.company },
    { title: t("field.department"), key: "department", width: userColumnWidths.department },
    {
      title: t("field.approval"),
      key: "approval_status",
      width: userColumnWidths.approval,
      filter: (value, row) => row.approval_status === value,
      filterMultiple: false,
      filterOptionValue: filters.approval_status,
      filterOptions: approvalOptions.value,
      render: (row) => h(StatusTag, { status: row.approval_status, labels: approvalLabels.value })
    },
    {
      title: t("field.status"),
      key: "is_active",
      width: userColumnWidths.status,
      filter: (value, row) => row.is_active === (value === "true"),
      filterMultiple: false,
      filterOptionValue: filters.is_active,
      filterOptions: activeOptions.value,
      render: (row) => h(StatusTag, { status: row.is_active })
    },
    { title: t("field.roles"), key: "roles", width: userColumnWidths.roles, render: (row) => row.roles.map((role) => roleName(role)).join(t("common.listSeparator")) || t("common.none") },
    {
      title: t("field.createdAt"),
      key: "created_at",
      width: userColumnWidths.createdAt,
      sorter: true,
      sortOrder: filters.sort_order,
      render: (row) => formatTime(row.created_at)
    },
    {
      title: t("common.actions"),
      key: "actions",
      width: userColumnWidths.actions,
      fixed: "right",
      align: "center",
      render: (row) => {
        const options = rowActionOptions(row);
        return h(
          NDropdown,
          { trigger: "click", placement: "bottom-end", options, onSelect: (key) => handleRowAction(row, String(key)) },
          {
            default: () =>
              h(
                NButton,
                { class: "row-action-button", size: "small", quaternary: true, circle: true, title: t("common.moreActions"), disabled: options.length === 0 },
                {
                  icon: () => h(NIcon, { component: MoreHorizontal20Regular })
                }
              )
          }
        );
      }
    }
  ])
);

const approvalLabels = computed(() => ({ pending: t("status.pending"), approved: t("status.approved"), rejected: t("status.rejected") }));

onMounted(async () => {
  await Promise.all([loadUsers(), needsRoleOptions.value ? loadRoles() : Promise.resolve()]);
});

async function loadUsers() {
  loading.value = true;
  try {
    const result = await listUsers({
      keyword: filters.keyword,
      approval_status: filters.approval_status || undefined,
      is_active: filters.is_active ? filters.is_active === "true" : null,
      sort_order: filters.sort_order,
      start_time: filters.time_range ? new Date(filters.time_range[0]).toISOString() : "",
      end_time: filters.time_range ? new Date(filters.time_range[1]).toISOString() : "",
      page: pagination.page,
      page_size: pagination.pageSize
    });
    users.value = result.items;
    pagination.itemCount = result.total;
    pagination.page = result.page;
    pagination.pageSize = result.page_size;
  } catch (error) {
    showError(message, error);
  } finally {
    loading.value = false;
  }
}

function searchUsers() {
  pagination.page = 1;
  void loadUsers();
}

function handlePageChange(page: number) {
  pagination.page = page;
  void loadUsers();
}

function handlePageSizeChange(pageSize: number) {
  pagination.pageSize = pageSize;
  pagination.page = 1;
  void loadUsers();
}

function handleTableFilters(filterState: DataTableFilterState) {
  const approvalStatus = singleFilterValue(filterState, "approval_status");
  const activeStatus = singleFilterValue(filterState, "is_active");
  filters.approval_status = isUserApprovalFilter(approvalStatus) ? approvalStatus : null;
  filters.is_active = isUserActiveFilter(activeStatus) ? activeStatus : null;
  pagination.page = 1;
  void loadUsers();
}

function handleSorter(sortState: DataTableSortState | DataTableSortState[] | null) {
  const state = Array.isArray(sortState) ? sortState[0] : sortState;
  filters.sort_order = state?.order === "ascend" ? "ascend" : "descend";
  pagination.page = 1;
  void loadUsers();
}

function handleColumnResize(_: number, limitedWidth: number, column: { key?: string | number }) {
  updateColumnWidth(userColumnWidths, column.key, userColumnWidthKeys, limitedWidth);
}

function isUserApprovalFilter(value: unknown): value is UserApprovalFilter {
  return value === "pending" || value === "approved" || value === "rejected";
}

function isUserActiveFilter(value: unknown): value is UserActiveFilter {
  return value === "true" || value === "false";
}

async function loadRoles() {
  try {
    roles.value = await listUserRoleOptions();
  } catch (error) {
    showError(message, error);
  }
}

function openCreate() {
  editingUser.value = null;
  Object.assign(userForm, { username: "", password: "", full_name: "", phone: "", email: "", company: "", department: "" });
  roleIds.value = [];
  showUserModal.value = true;
}

function openEdit(user: UserListItem) {
  editingUser.value = user;
  Object.assign(userForm, {
    username: user.username,
    password: "",
    full_name: user.full_name,
    phone: user.phone,
    email: user.email,
    company: user.company,
    department: user.department
  });
  showUserModal.value = true;
}

async function saveUser() {
  if (!(await validateForm(userFormRef.value))) return;
  try {
    if (editingUser.value) {
      await updateUser(editingUser.value.id, userForm);
    } else {
      await createUser({ ...userForm, role_ids: roleIds.value });
    }
    showUserModal.value = false;
    await loadUsers();
    message.success(t("user.saved"));
  } catch (error) {
    showError(message, error);
  }
}

function openApprove(user: UserListItem) {
  approvalTarget.value = user;
  roleIds.value = [];
  showApproveModal.value = true;
}

async function saveApprove() {
  if (!approvalTarget.value) return;
  try {
    await approveUser(approvalTarget.value.id, roleIds.value);
    showApproveModal.value = false;
    await loadUsers();
    message.success(t("user.approved"));
  } catch (error) {
    showError(message, error);
  }
}

function openReject(user: UserListItem) {
  approvalTarget.value = user;
  rejectForm.reason = "";
  showRejectModal.value = true;
}

async function saveReject() {
  if (!approvalTarget.value) return;
  if (!(await validateForm(rejectFormRef.value))) return;
  try {
    await rejectUser(approvalTarget.value.id, rejectForm.reason);
    showRejectModal.value = false;
    await loadUsers();
    message.success(t("user.rejected"));
  } catch (error) {
    showError(message, error);
  }
}

function rowActionOptions(user: UserListItem): DropdownOption[] {
  const options: DropdownOption[] = [];
  if (user.approval_status === "pending" && authStore.has("action:user:operate")) {
    options.push({ label: t("user.pass"), key: "approve" }, { label: t("user.reject"), key: "reject" });
  }
  if (authStore.has("action:user:update")) {
    options.push({ label: t("common.edit"), key: "edit" });
  }
  if (user.approval_status === "approved" && authStore.has("action:user:operate")) {
    options.push(
      { label: user.is_active ? t("common.disabled") : t("common.enabled"), key: "toggle-active" },
      { label: t("field.role"), key: "roles" },
      { label: t("field.password"), key: "password" }
    );
  }
  if (authStore.has("action:user:delete")) {
    options.push({ label: t("common.delete"), key: "delete", disabled: Boolean(deleteDisabledReason(user)) });
  }
  return options;
}

function handleRowAction(user: UserListItem, key: string) {
  const actions: Record<string, () => void> = {
    approve: () => openApprove(user),
    reject: () => openReject(user),
    edit: () => openEdit(user),
    "toggle-active": () => void toggleActive(user),
    roles: () => openRoles(user),
    password: () => openPassword(user),
    delete: () => confirmDelete(user)
  };
  actions[key]?.();
}

async function toggleActive(user: UserListItem) {
  try {
    if (user.is_active) {
      await disableUser(user.id);
    } else {
      await enableUser(user.id);
    }
    await loadUsers();
  } catch (error) {
    showError(message, error);
  }
}

function openRoles(user: UserListItem) {
  roleTarget.value = user;
  roleIds.value = user.roles.map((role) => role.id);
  showRoleModal.value = true;
}

async function saveRoles() {
  if (!roleTarget.value) return;
  if (guardRoleChange(roleTarget.value)) return;
  try {
    await assignRoles(roleTarget.value.id, roleIds.value);
    showRoleModal.value = false;
    await loadUsers();
    message.success(t("user.rolesUpdated"));
  } catch (error) {
    showError(message, error);
  }
}

function openPassword(user: UserListItem) {
  passwordTarget.value = user;
  passwordForm.password = "";
  showPasswordModal.value = true;
}

async function savePassword() {
  if (!passwordTarget.value) return;
  if (!(await validateForm(passwordFormRef.value))) return;
  try {
    const result = await resetPassword(passwordTarget.value.id, passwordForm.password);
    showPasswordModal.value = false;
    message.success(messageText(result, "user.passwordReset"));
  } catch (error) {
    showError(message, error);
  }
}

function confirmDelete(user: UserListItem) {
  const disabledReason = deleteDisabledReason(user);
  if (disabledReason) {
    message.error(disabledReason);
    return;
  }
  dialog.warning({
    title: t("user.deleteTitle"),
    content: t("user.deleteConfirm", { name: user.username }),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: async () => {
      try {
        const result = await deleteUser(user.id);
        await loadUsers();
        message.success(messageText(result, "user.deleted"));
      } catch (error) {
        showError(message, error);
      }
    }
  });
}

function hasAdminRole(user: UserListItem) {
  return user.roles.some((role) => role.code === "admin");
}

function guardRoleChange(user: UserListItem) {
  const removingAdminRole = hasAdminRole(user) && adminRoleId.value !== null && !roleIds.value.includes(adminRoleId.value);
  if (!removingAdminRole) return false;
  if (authStore.user?.id === user.id) {
    message.error(t("user.cannotRemoveSelfAdmin"));
    return true;
  }
  return false;
}

function deleteDisabledReason(user: UserListItem) {
  if (user.is_builtin) return t("user.builtinCannotDelete");
  return "";
}

function formatTime(value: string) {
  return formatDateTime(value);
}
</script>
