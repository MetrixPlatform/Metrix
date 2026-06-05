<template>
  <section class="work-card table-page-card">
    <div class="toolbar user-toolbar">
      <div class="user-filter-row">
        <n-input v-model:value="filters.keyword" class="filter-keyword" placeholder="搜索账号、姓名、手机、邮箱、公司、部门" clearable />
        <n-date-picker
          v-model:value="filters.time_range"
          class="filter-date-range"
          type="datetimerange"
          clearable
          start-placeholder="开始时间"
          end-placeholder="结束时间"
        />
        <n-button @click="searchUsers">查询</n-button>
      </div>
      <permission-button class="user-create-button" permission="action:user:create" type="primary" @click="openCreate">新增用户</permission-button>
    </div>
    <n-data-table
      class="page-data-table"
      flex-height
      :columns="columns"
      :data="users"
      :loading="loading"
      :pagination="pagination"
      :row-key="(row) => row.id"
      :scroll-x="1380"
      remote
      @update:filters="handleTableFilters"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
      @update:sorter="handleSorter"
    />
    <n-modal v-model:show="showApproveModal" preset="card" class="modal-card" title="审核通过">
      <n-checkbox-group v-model:value="roleIds">
        <n-space>
          <n-checkbox v-for="role in roles" :key="role.id" :value="role.id">{{ role.name }}</n-checkbox>
        </n-space>
      </n-checkbox-group>
      <div class="form-actions">
        <n-button @click="showApproveModal = false">取消</n-button>
        <n-button type="primary" @click="saveApprove">通过</n-button>
      </div>
    </n-modal>
    <n-modal v-model:show="showRejectModal" preset="card" class="modal-card" title="驳回注册">
      <n-form ref="rejectFormRef" class="inline-form" :model="rejectForm" :rules="rejectRules" label-placement="left" label-width="88">
        <n-form-item label="驳回原因" path="reason">
          <n-input v-model:value="rejectForm.reason" type="textarea" placeholder="驳回原因" />
        </n-form-item>
      </n-form>
      <div class="form-actions">
        <n-button @click="showRejectModal = false">取消</n-button>
        <n-button type="error" @click="saveReject">驳回</n-button>
      </div>
    </n-modal>
    <n-modal v-model:show="showUserModal" preset="card" class="modal-card" :title="editingUser ? '编辑用户' : '新增用户'">
      <n-form ref="userFormRef" class="form-stack inline-form" :model="userForm" :rules="userRules" label-placement="left" label-width="80">
        <n-form-item v-if="!editingUser" label="账号" path="username">
          <n-input v-model:value="userForm.username" />
        </n-form-item>
        <n-form-item v-if="!editingUser" label="密码" path="password">
          <n-input v-model:value="userForm.password" type="password" show-password-on="click" />
        </n-form-item>
        <n-form-item label="姓名" path="full_name">
          <n-input v-model:value="userForm.full_name" />
        </n-form-item>
        <n-form-item label="手机号码" path="phone">
          <n-input v-model:value="userForm.phone" />
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="userForm.email" />
        </n-form-item>
        <n-form-item label="公司" path="company">
          <n-input v-model:value="userForm.company" />
        </n-form-item>
        <n-form-item label="部门" path="department">
          <n-input v-model:value="userForm.department" />
        </n-form-item>
        <n-form-item v-if="!editingUser" label="角色">
          <n-checkbox-group v-model:value="roleIds">
            <n-space>
              <n-checkbox v-for="role in roles" :key="role.id" :value="role.id">{{ role.name }}</n-checkbox>
            </n-space>
          </n-checkbox-group>
        </n-form-item>
        <div class="form-actions">
          <n-button @click="showUserModal = false">取消</n-button>
          <n-button type="primary" @click="saveUser">保存</n-button>
        </div>
      </n-form>
    </n-modal>
    <n-modal v-model:show="showRoleModal" preset="card" class="modal-card" title="分配角色">
      <n-checkbox-group v-model:value="roleIds">
        <n-space>
          <n-checkbox v-for="role in roles" :key="role.id" :value="role.id">{{ role.name }}</n-checkbox>
        </n-space>
      </n-checkbox-group>
      <div class="form-actions">
        <n-button @click="showRoleModal = false">取消</n-button>
        <n-button type="primary" @click="saveRoles">保存</n-button>
      </div>
    </n-modal>
    <n-modal v-model:show="showPasswordModal" preset="card" class="modal-card" title="重置密码">
      <n-form ref="passwordFormRef" class="form-stack inline-form" :model="passwordForm" :rules="passwordRules" label-placement="left" label-width="88">
        <n-form-item label="新密码" path="password">
          <n-input v-model:value="passwordForm.password" type="password" show-password-on="click" />
        </n-form-item>
        <div class="form-actions">
          <n-button @click="showPasswordModal = false">取消</n-button>
          <n-button type="primary" @click="savePassword">保存</n-button>
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
import { authStore } from "../stores/auth";
import { showError } from "../utils/message";
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
  prefix: ({ itemCount }: { itemCount: number | undefined }) => `共 ${itemCount ?? 0} 条`
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
const userRules: FormRules = {
  username: [requiredRule("账号"), minLengthRule("账号", 3), maxLengthRule("账号", 64)],
  password: [requiredRule("密码"), minLengthRule("密码", 6), maxLengthRule("密码", 128)],
  full_name: [requiredRule("姓名"), maxLengthRule("姓名", 80)],
  phone: [requiredRule("手机号码"), phoneRule()],
  email: [requiredRule("邮箱"), emailRule(), maxLengthRule("邮箱", 254)],
  company: maxLengthRule("公司", 120),
  department: maxLengthRule("部门", 120)
};
const passwordRules: FormRules = {
  password: [requiredRule("新密码"), minLengthRule("新密码", 6), maxLengthRule("新密码", 128)]
};
const rejectRules: FormRules = {
  reason: maxLengthRule("驳回原因", 500)
};
const adminRoleId = computed(() => roles.value.find((role) => role.code === "admin")?.id ?? null);
const needsRoleOptions = computed(() => authStore.has("action:user:create") || authStore.has("action:user:operate"));

const approvalOptions = [
  { label: "待审核", value: "pending" },
  { label: "已通过", value: "approved" },
  { label: "已驳回", value: "rejected" }
];
const activeOptions = [
  { label: "启用", value: "true" },
  { label: "禁用", value: "false" }
];

const columns = computed<DataTableColumns<UserListItem>>(() => [
  { title: "账号", key: "username", width: 130 },
  { title: "姓名", key: "full_name", width: 120 },
  { title: "手机号码", key: "phone", width: 130 },
  { title: "邮箱", key: "email", width: 200 },
  { title: "公司", key: "company", width: 140 },
  { title: "部门", key: "department", width: 120 },
  {
    title: "审核",
    key: "approval_status",
    width: 100,
    filter: (value, row) => row.approval_status === value,
    filterMultiple: false,
    filterOptionValue: filters.approval_status,
    filterOptions: approvalOptions,
    render: (row) => h(StatusTag, { status: row.approval_status, labels: approvalLabels })
  },
  {
    title: "状态",
    key: "is_active",
    width: 90,
    filter: (value, row) => row.is_active === (value === "true"),
    filterMultiple: false,
    filterOptionValue: filters.is_active,
    filterOptions: activeOptions,
    render: (row) => h(StatusTag, { status: row.is_active })
  },
  { title: "角色", key: "roles", width: 160, render: (row) => row.roles.map((role) => role.name).join("、") || "-" },
  {
    title: "注册时间",
    key: "created_at",
    width: 170,
    sorter: true,
    sortOrder: filters.sort_order,
    render: (row) => formatTime(row.created_at)
  },
  {
    title: "操作",
    key: "actions",
    width: 64,
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
              { class: "row-action-button", size: "small", quaternary: true, circle: true, title: "更多操作", disabled: options.length === 0 },
              {
                icon: () => h(NIcon, { component: MoreHorizontal20Regular })
              }
            )
        }
      );
    }
  }
]);

const approvalLabels = { pending: "待审核", approved: "已通过", rejected: "已驳回" };

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

function singleFilterValue(filterState: DataTableFilterState, key: string) {
  const value = filterState[key];
  return Array.isArray(value) ? value[0] ?? null : value ?? null;
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
    message.success("用户已保存");
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
    message.success("已审核通过");
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
    message.success("已驳回");
  } catch (error) {
    showError(message, error);
  }
}

function rowActionOptions(user: UserListItem): DropdownOption[] {
  const options: DropdownOption[] = [];
  if (user.approval_status === "pending" && authStore.has("action:user:operate")) {
    options.push({ label: "通过", key: "approve" }, { label: "驳回", key: "reject" });
  }
  if (authStore.has("action:user:update")) {
    options.push({ label: "编辑", key: "edit" });
  }
  if (user.approval_status === "approved" && authStore.has("action:user:operate")) {
    options.push(
      { label: user.is_active ? "禁用" : "启用", key: "toggle-active" },
      { label: "角色", key: "roles" },
      { label: "密码", key: "password" }
    );
  }
  if (authStore.has("action:user:delete")) {
    options.push({ label: "删除", key: "delete", disabled: Boolean(deleteDisabledReason(user)) });
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
    message.success("角色已更新");
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
    await resetPassword(passwordTarget.value.id, passwordForm.password);
    showPasswordModal.value = false;
    message.success("密码已重置");
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
    title: "删除用户",
    content: `确认删除 ${user.username}？`,
    positiveText: "删除",
    negativeText: "取消",
    onPositiveClick: async () => {
      try {
        await deleteUser(user.id);
        await loadUsers();
        message.success("用户已删除");
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
    message.error("不能移除自己的管理员角色");
    return true;
  }
  return false;
}

function deleteDisabledReason(user: UserListItem) {
  if (user.is_builtin) return "内置用户不能删除";
  return "";
}

function formatTime(value: string) {
  return new Date(value).toLocaleString();
}
</script>
