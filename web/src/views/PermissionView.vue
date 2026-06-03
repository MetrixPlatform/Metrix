<template>
  <div class="permission-layout">
    <section class="work-card permission-role-card">
      <div class="toolbar">
        <strong>角色</strong>
        <div class="toolbar-group">
          <permission-button permission="action:role:create" type="primary" @click="openCreate">新增</permission-button>
          <permission-button
            permission="action:role:update"
            :disabled="!selectedRole"
            @click="openEdit"
          >
            编辑
          </permission-button>
          <permission-button
            permission="action:role:delete"
            type="error"
            :disabled="!selectedRole || selectedRole.is_builtin"
            @click="removeRole"
          >
            删除
          </permission-button>
        </div>
      </div>
      <div class="role-list">
        <div
          v-for="role in roles"
          :key="role.id"
          class="role-row"
          :class="{ active: selectedRole?.id === role.id }"
          @click="selectedRole = role"
        >
          <div class="role-row-info">
            <strong>{{ role.name }}</strong>
            <div class="role-row-description">{{ role.code }} · {{ role.description || "无说明" }}</div>
          </div>
          <status-tag :status="role.is_builtin ? 'builtin' : 'custom'" :labels="{ builtin: '内置', custom: '自定义' }" />
        </div>
      </div>
    </section>

    <section class="work-card permission-assign-card">
      <div class="toolbar">
        <strong>权限分配</strong>
        <permission-button
          permission="action:role:operate"
          type="primary"
          :disabled="!selectedRole"
          @click="savePermissions"
        >
          保存权限
        </permission-button>
      </div>
      <n-empty v-if="!selectedRole" description="请选择角色" />
      <div v-else class="permission-grid">
        <div v-for="group in groupedPermissions" :key="group.name" class="permission-group">
          <div class="permission-group-title">{{ group.name }}</div>
          <n-checkbox-group v-model:value="checkedPermissionIds">
            <n-space vertical>
              <n-checkbox
                v-for="permission in group.items"
                :key="permission.id"
                :value="permission.id"
                :disabled="selectedRole.code === 'admin'"
              >
                {{ permission.name }}
              </n-checkbox>
            </n-space>
          </n-checkbox-group>
        </div>
      </div>
    </section>

    <n-modal v-model:show="showRoleModal" preset="card" class="modal-card" :title="editingRole ? '编辑角色' : '新增角色'">
      <n-form ref="roleFormRef" class="form-stack inline-form" :model="roleForm" :rules="roleRules" label-placement="left" label-width="92">
        <n-form-item v-if="!editingRole" label="角色编码" path="code">
          <n-input v-model:value="roleForm.code" />
        </n-form-item>
        <n-form-item label="角色名称" path="name">
          <n-input v-model:value="roleForm.name" />
        </n-form-item>
        <n-form-item label="说明" path="description">
          <n-input v-model:value="roleForm.description" type="textarea" />
        </n-form-item>
        <div class="form-actions">
          <n-button @click="showRoleModal = false">取消</n-button>
          <n-button type="primary" @click="saveRole">保存</n-button>
        </div>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { NButton, NCheckbox, NCheckboxGroup, NEmpty, NForm, NFormItem, NInput, NModal, NSpace, useDialog, useMessage } from "naive-ui";
import type { FormInst, FormRules } from "naive-ui";

import { assignPermissions, createRole, deleteRole, listPermissions, listRoles, updateRole } from "../api/roles";
import type { PermissionItem, RoleItem } from "../api/types";
import PermissionButton from "../components/PermissionButton.vue";
import StatusTag from "../components/StatusTag.vue";
import { maxLengthRule, minLengthRule, requiredRule, validateForm } from "../utils/validation";

const message = useMessage();
const dialog = useDialog();
const roles = ref<RoleItem[]>([]);
const permissions = ref<PermissionItem[]>([]);
const selectedRole = ref<RoleItem | null>(null);
const checkedPermissionIds = ref<number[]>([]);
const showRoleModal = ref(false);
const roleFormRef = ref<FormInst | null>(null);
const editingRole = ref<RoleItem | null>(null);
const roleForm = reactive({ code: "", name: "", description: "" });
const roleRules: FormRules = {
  code: [requiredRule("角色编码"), minLengthRule("角色编码", 2), maxLengthRule("角色编码", 64)],
  name: [requiredRule("角色名称"), maxLengthRule("角色名称", 80)],
  description: maxLengthRule("说明", 500)
};

const groupedPermissions = computed(() => {
  const groups = new Map<string, PermissionItem[]>();
  permissions.value
    .filter((permission) => permission.type === "route" || permission.code.endsWith(":create") || permission.code.endsWith(":update") || permission.code.endsWith(":delete") || permission.code.endsWith(":operate"))
    .forEach((permission) => {
      const group = permission.group_name || "其他";
      groups.set(group, [...(groups.get(group) || []), permission]);
    });
  return Array.from(groups.entries()).map(([name, items]) => ({ name, items }));
});

watch(selectedRole, (role) => {
  checkedPermissionIds.value = role?.permissions.map((permission) => permission.id) || [];
});

onMounted(async () => {
  await loadData();
});

async function loadData() {
  [roles.value, permissions.value] = await Promise.all([listRoles(), listPermissions()]);
  if (!selectedRole.value && roles.value.length > 0) {
    selectedRole.value = roles.value[0];
  } else if (selectedRole.value) {
    selectedRole.value = roles.value.find((role) => role.id === selectedRole.value?.id) || roles.value[0] || null;
  }
}

function openCreate() {
  editingRole.value = null;
  Object.assign(roleForm, { code: "", name: "", description: "" });
  showRoleModal.value = true;
}

function openEdit() {
  if (!selectedRole.value) return;
  editingRole.value = selectedRole.value;
  Object.assign(roleForm, {
    code: selectedRole.value.code,
    name: selectedRole.value.name,
    description: selectedRole.value.description
  });
  showRoleModal.value = true;
}

async function saveRole() {
  if (!(await validateForm(roleFormRef.value))) return;
  try {
    if (editingRole.value) {
      await updateRole(editingRole.value.id, roleForm);
    } else {
      await createRole(roleForm);
    }
    showRoleModal.value = false;
    await loadData();
    message.success("角色已保存");
  } catch (error) {
    message.error((error as Error).message);
  }
}

function removeRole() {
  const role = selectedRole.value;
  if (!role) return;
  dialog.warning({
    title: "删除角色",
    content: `确认删除角色 ${role.name}？`,
    positiveText: "删除",
    negativeText: "取消",
    onPositiveClick: async () => {
      try {
        await deleteRole(role.id);
        selectedRole.value = null;
        await loadData();
        message.success("角色已删除");
      } catch (error) {
        message.error((error as Error).message);
      }
    }
  });
}

async function savePermissions() {
  if (!selectedRole.value) return;
  try {
    await assignPermissions(selectedRole.value.id, checkedPermissionIds.value);
    await loadData();
    message.success("权限已保存");
  } catch (error) {
    message.error((error as Error).message);
  }
}
</script>
