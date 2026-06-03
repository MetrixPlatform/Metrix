<template>
  <section class="work-card">
    <div class="toolbar">
      <div class="toolbar-group">
        <n-input v-model:value="filters.keyword" placeholder="搜索账号、姓名、公司、部门" clearable />
        <n-select v-model:value="filters.approval_status" :options="approvalOptions" clearable placeholder="审核状态" />
        <n-select v-model:value="filters.is_active" :options="activeOptions" clearable placeholder="启用状态" />
        <n-button @click="loadUsers">查询</n-button>
      </div>
      <permission-button permission="action:user:create" type="primary" @click="openCreate">新增用户</permission-button>
    </div>
    <n-data-table :columns="columns" :data="users" :loading="loading" :row-key="(row) => row.id" :scroll-x="1180" />
    <n-modal v-model:show="showUserModal" preset="card" class="modal-card" :title="editingUser ? '编辑用户' : '新增用户'">
      <n-form ref="userFormRef" class="form-stack" :model="userForm" :rules="userRules" label-placement="top">
        <n-form-item v-if="!editingUser" label="账号" path="username">
          <n-input v-model:value="userForm.username" />
        </n-form-item>
        <n-form-item v-if="!editingUser" label="密码" path="password">
          <n-input v-model:value="userForm.password" type="password" show-password-on="click" />
        </n-form-item>
        <n-form-item label="姓名" path="full_name">
          <n-input v-model:value="userForm.full_name" />
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
      <n-form ref="passwordFormRef" class="form-stack" :model="passwordForm" :rules="passwordRules" label-placement="top">
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
import { h, onMounted, reactive, ref } from "vue";
import {
  NButton,
  NCheckbox,
  NCheckboxGroup,
  NDataTable,
  NForm,
  NFormItem,
  NInput,
  NModal,
  NSelect,
  NSpace,
  useDialog,
  useMessage
} from "naive-ui";
import type { DataTableColumns, FormInst, FormRules } from "naive-ui";

import { assignRoles, createUser, deleteUser, disableUser, enableUser, listUsers, resetPassword, updateUser } from "../api/users";
import { listRoles } from "../api/roles";
import type { RoleItem, UserListItem } from "../api/types";
import PermissionButton from "../components/PermissionButton.vue";
import StatusTag from "../components/StatusTag.vue";
import { authStore } from "../stores/auth";
import { maxLengthRule, minLengthRule, requiredRule, validateForm } from "../utils/validation";

const message = useMessage();
const dialog = useDialog();
const loading = ref(false);
const userFormRef = ref<FormInst | null>(null);
const passwordFormRef = ref<FormInst | null>(null);
const users = ref<UserListItem[]>([]);
const roles = ref<RoleItem[]>([]);
const showUserModal = ref(false);
const showRoleModal = ref(false);
const showPasswordModal = ref(false);
const editingUser = ref<UserListItem | null>(null);
const roleTarget = ref<UserListItem | null>(null);
const passwordTarget = ref<UserListItem | null>(null);
const roleIds = ref<number[]>([]);
const passwordForm = reactive({ password: "" });
const filters = reactive<{ keyword: string; approval_status: string | null; is_active: string | null }>({
  keyword: "",
  approval_status: null,
  is_active: null
});
const userForm = reactive({
  username: "",
  password: "",
  full_name: "",
  company: "",
  department: ""
});
const userRules: FormRules = {
  username: [requiredRule("账号"), minLengthRule("账号", 3), maxLengthRule("账号", 64)],
  password: [requiredRule("密码"), minLengthRule("密码", 6), maxLengthRule("密码", 128)],
  full_name: [requiredRule("姓名"), maxLengthRule("姓名", 80)],
  company: maxLengthRule("公司", 120),
  department: maxLengthRule("部门", 120)
};
const passwordRules: FormRules = {
  password: [requiredRule("新密码"), minLengthRule("新密码", 6), maxLengthRule("新密码", 128)]
};

const approvalOptions = [
  { label: "待审核", value: "pending" },
  { label: "已通过", value: "approved" },
  { label: "已驳回", value: "rejected" }
];
const activeOptions = [
  { label: "启用", value: "true" },
  { label: "禁用", value: "false" }
];

const columns: DataTableColumns<UserListItem> = [
  { title: "账号", key: "username", width: 130 },
  { title: "姓名", key: "full_name", width: 120 },
  { title: "公司", key: "company", width: 140 },
  { title: "部门", key: "department", width: 120 },
  { title: "审核", key: "approval_status", width: 100, render: (row) => h(StatusTag, { status: row.approval_status, labels: approvalLabels }) },
  { title: "状态", key: "is_active", width: 90, render: (row) => h(StatusTag, { status: row.is_active }) },
  { title: "角色", key: "roles", width: 160, render: (row) => row.roles.map((role) => role.name).join("、") || "-" },
  {
    title: "操作",
    key: "actions",
    width: 330,
    render: (row) =>
      h("div", { class: "toolbar-group" }, [
        authStore.has("action:user:update") ? h(NButton, { size: "small", onClick: () => openEdit(row) }, { default: () => "编辑" }) : null,
        authStore.has("action:user:operate")
          ? h(NButton, { size: "small", onClick: () => toggleActive(row) }, { default: () => (row.is_active ? "禁用" : "启用") })
          : null,
        authStore.has("action:user:operate") ? h(NButton, { size: "small", onClick: () => openRoles(row) }, { default: () => "角色" }) : null,
        authStore.has("action:user:operate") ? h(NButton, { size: "small", onClick: () => openPassword(row) }, { default: () => "密码" }) : null,
        authStore.has("action:user:delete")
          ? h(NButton, { size: "small", type: "error", onClick: () => confirmDelete(row) }, { default: () => "删除" })
          : null
      ])
  }
];

const approvalLabels = { pending: "待审核", approved: "已通过", rejected: "已驳回" };

onMounted(async () => {
  await Promise.all([loadUsers(), loadRoles()]);
});

async function loadUsers() {
  loading.value = true;
  try {
    users.value = await listUsers({
      keyword: filters.keyword,
      approval_status: filters.approval_status || undefined,
      is_active: filters.is_active ? filters.is_active === "true" : null
    });
  } catch (error) {
    message.error((error as Error).message);
  } finally {
    loading.value = false;
  }
}

async function loadRoles() {
  roles.value = await listRoles();
}

function openCreate() {
  editingUser.value = null;
  Object.assign(userForm, { username: "", password: "", full_name: "", company: "", department: "" });
  roleIds.value = [];
  showUserModal.value = true;
}

function openEdit(user: UserListItem) {
  editingUser.value = user;
  Object.assign(userForm, {
    username: user.username,
    password: "",
    full_name: user.full_name,
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
    message.error((error as Error).message);
  }
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
    message.error((error as Error).message);
  }
}

function openRoles(user: UserListItem) {
  roleTarget.value = user;
  roleIds.value = user.roles.map((role) => role.id);
  showRoleModal.value = true;
}

async function saveRoles() {
  if (!roleTarget.value) return;
  try {
    await assignRoles(roleTarget.value.id, roleIds.value);
    showRoleModal.value = false;
    await loadUsers();
    message.success("角色已更新");
  } catch (error) {
    message.error((error as Error).message);
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
    message.error((error as Error).message);
  }
}

function confirmDelete(user: UserListItem) {
  dialog.warning({
    title: "删除用户",
    content: `确认删除 ${user.username}？`,
    positiveText: "删除",
    negativeText: "取消",
    onPositiveClick: async () => {
      await deleteUser(user.id);
      await loadUsers();
    }
  });
}
</script>
