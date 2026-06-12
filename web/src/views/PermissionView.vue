<template>
  <div class="permission-layout">
    <section class="work-card list-page-card permission-role-card">
      <div class="toolbar">
        <strong>{{ t("permission.roles") }}</strong>
        <div class="toolbar-group">
          <permission-button permission="action:role:create" size="small" type="primary" @click="openCreate">{{ t("common.create") }}</permission-button>
          <permission-button
            permission="action:role:update"
            size="small"
            :disabled="!selectedRole"
            @click="openEdit"
          >
            {{ t("common.edit") }}
          </permission-button>
          <permission-button
            permission="action:role:delete"
            size="small"
            type="error"
            :disabled="!selectedRole || selectedRole.is_builtin"
            @click="removeRole"
          >
            {{ t("common.delete") }}
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
            <strong>{{ roleName(role) }}</strong>
            <div class="role-row-description">{{ role.code }} · {{ roleDescription(role) || t("common.noDescription") }}</div>
          </div>
          <status-tag :status="role.is_builtin ? 'builtin' : 'custom'" :labels="roleTypeLabels" />
        </div>
      </div>
    </section>

    <section class="work-card list-page-card permission-assign-card">
      <div class="toolbar">
        <strong>{{ t("permission.assignment") }}</strong>
        <div class="toolbar-group">
          <n-button size="small" quaternary :disabled="!selectedRole" :title="t('common.expandAll')" @click="expandAllGroups">
            <template #icon><n-icon :component="ChevronDoubleDown20Regular" /></template>
          </n-button>
          <n-button size="small" quaternary :disabled="!selectedRole" :title="t('common.collapseAll')" @click="collapseAllGroups">
            <template #icon><n-icon :component="ChevronDoubleUp20Regular" /></template>
          </n-button>
          <permission-button
            permission="action:role:operate"
            size="small"
            type="primary"
            :disabled="!selectedRole"
            @click="savePermissions"
          >
            {{ t("permission.savePermissions") }}
          </permission-button>
        </div>
      </div>
      <n-empty v-if="!selectedRole" :description="t('permission.selectRole')" />
      <div v-else class="permission-tree">
        <div v-for="group in permissionTreeGroups" :key="group.key" class="permission-tree-group">
          <div class="permission-tree-parent">
            <button
              class="permission-tree-toggle"
              type="button"
              :aria-expanded="isGroupExpanded(group.key)"
              @click="toggleGroup(group.key)"
            >
              <n-icon :component="isGroupExpanded(group.key) ? ChevronDown20Regular : ChevronRight20Regular" />
            </button>
            <n-checkbox
              class="permission-tree-checkbox"
              :checked="isGroupChecked(group)"
              :indeterminate="isGroupIndeterminate(group)"
              :disabled="isPermissionReadonly"
              @update:checked="(checked) => setGroupChecked(group, checked)"
            >
              <span class="permission-tree-title">{{ group.name }}</span>
            </n-checkbox>
            <span class="permission-tree-count">{{ groupCheckedCount(group) }}/{{ group.items.length }}</span>
          </div>
          <div v-if="isGroupExpanded(group.key)" class="permission-tree-children">
            <n-checkbox
              v-for="permission in group.items"
              :key="permission.id"
              class="permission-tree-leaf"
              :checked="isPermissionChecked(permission.id)"
              :disabled="isPermissionReadonly"
              @update:checked="(checked) => setPermissionChecked(permission.id, checked)"
            >
              <span class="permission-tree-leaf-text">{{ permissionName(permission) }}</span>
            </n-checkbox>
          </div>
        </div>
      </div>
    </section>

    <n-modal v-model:show="showRoleModal" preset="card" class="modal-card" :title="editingRole ? t('permission.editRole') : t('permission.addRole')">
      <n-form ref="roleFormRef" class="form-stack inline-form" :model="roleForm" :rules="roleRules" label-placement="left" label-width="auto">
        <n-form-item v-if="!editingRole" :label="t('field.roleCode')" path="code">
          <n-input v-model:value="roleForm.code" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('field.roleName')" path="name">
          <n-input v-model:value="roleForm.name" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('field.description')" path="description">
          <n-input v-model:value="roleForm.description" type="textarea" placeholder="" />
        </n-form-item>
        <div class="form-actions">
          <n-button @click="showRoleModal = false">{{ t("common.cancel") }}</n-button>
          <n-button type="primary" @click="saveRole">{{ t("common.save") }}</n-button>
        </div>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ChevronDoubleDown20Regular, ChevronDoubleUp20Regular, ChevronDown20Regular, ChevronRight20Regular } from "@vicons/fluent";
import { computed, onMounted, reactive, ref, watch } from "vue";
import { NButton, NCheckbox, NEmpty, NForm, NFormItem, NIcon, NInput, NModal, useDialog, useMessage } from "naive-ui";
import type { FormInst, FormRules } from "naive-ui";

import { assignPermissions, createRole, deleteRole, listPermissions, listRoles, updateRole } from "../api/roles";
import type { PermissionItem, RoleItem } from "../api/types";
import PermissionButton from "../components/PermissionButton.vue";
import StatusTag from "../components/StatusTag.vue";
import { isActivePermissionCode } from "../config/permissions";
import { t } from "../i18n";
import { permissionGroupName, permissionName, roleDescription, roleName } from "../i18n/builtins";
import { messageText, showError } from "../utils/message";
import { maxLengthRule, minLengthRule, requiredRule, validateForm } from "../utils/validation";

const message = useMessage();
const dialog = useDialog();
const roles = ref<RoleItem[]>([]);
const permissions = ref<PermissionItem[]>([]);
const selectedRole = ref<RoleItem | null>(null);
const checkedPermissionIds = ref<number[]>([]);
const expandedGroupKeys = ref<Set<string>>(new Set());
const showRoleModal = ref(false);
const roleFormRef = ref<FormInst | null>(null);
const editingRole = ref<RoleItem | null>(null);
const roleForm = reactive({ code: "", name: "", description: "" });
const roleRules = computed<FormRules>(() => ({
  code: [requiredRule(t("field.roleCode")), minLengthRule(t("field.roleCode"), 2), maxLengthRule(t("field.roleCode"), 64)],
  name: [requiredRule(t("field.roleName")), maxLengthRule(t("field.roleName"), 80)],
  description: maxLengthRule(t("field.description"), 500)
}));
const roleTypeLabels = computed(() => ({ builtin: t("common.builtin"), custom: t("common.custom") }));
const isPermissionReadonly = computed(() => selectedRole.value?.code === "admin");

interface PermissionTreeGroup {
  key: string;
  name: string;
  items: PermissionItem[];
}

const permissionTreeGroups = computed<PermissionTreeGroup[]>(() => {
  const groups = new Map<string, PermissionItem[]>();
  permissions.value
    .filter((permission) => isActivePermissionCode(permission.code))
    .filter((permission) => permission.type === "route" || (permission.type === "action" && !permission.code.endsWith(":read")))
    .forEach((permission) => {
      const group = permission.group_name || "";
      groups.set(group, [...(groups.get(group) || []), permission]);
    });
  return Array.from(groups.entries())
    .map(([name, items]) => ({
      key: name || "other",
      name: name ? permissionGroupName(name) : t("permission.otherGroup"),
      items: [...items].sort((left, right) => left.sort_order - right.sort_order)
    }))
    .sort((left, right) => firstSortOrder(left) - firstSortOrder(right));
});

watch(selectedRole, (role) => {
  checkedPermissionIds.value = role?.permissions.filter((permission) => isActivePermissionCode(permission.code)).map((permission) => permission.id) || [];
});

onMounted(async () => {
  await loadData();
});

async function loadData() {
  try {
    [roles.value, permissions.value] = await Promise.all([listRoles(), listPermissions()]);
  } catch (error) {
    showError(message, error);
    return;
  }
  permissions.value = permissions.value.filter((permission) => isActivePermissionCode(permission.code));
  roles.value = roles.value.map((role) => ({
    ...role,
    permissions: role.permissions.filter((permission) => isActivePermissionCode(permission.code))
  }));
  if (!selectedRole.value && roles.value.length > 0) {
    selectedRole.value = roles.value[0];
  } else if (selectedRole.value) {
    selectedRole.value = roles.value.find((role) => role.id === selectedRole.value?.id) || roles.value[0] || null;
  }
  syncExpandedGroups();
}

function syncExpandedGroups() {
  const groups = permissionTreeGroups.value;
  const existingKeys = new Set(groups.map((group) => group.key));
  expandedGroupKeys.value = new Set([...expandedGroupKeys.value].filter((key) => existingKeys.has(key)));
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
    message.success(t("permission.roleSaved"));
  } catch (error) {
    showError(message, error);
  }
}

function removeRole() {
  const role = selectedRole.value;
  if (!role) return;
  dialog.warning({
    title: t("permission.deleteRoleTitle"),
    content: t("permission.deleteRoleConfirm", { name: roleName(role) }),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: async () => {
      try {
        const result = await deleteRole(role.id);
        selectedRole.value = null;
        await loadData();
        message.success(messageText(result, "permission.roleDeleted"));
      } catch (error) {
        showError(message, error);
      }
    }
  });
}

async function savePermissions() {
  if (!selectedRole.value) return;
  try {
    const activePermissionIds = new Set(permissions.value.map((permission) => permission.id));
    await assignPermissions(selectedRole.value.id, checkedPermissionIds.value.filter((id) => activePermissionIds.has(id)));
    await loadData();
    message.success(t("permission.saved"));
  } catch (error) {
    showError(message, error);
  }
}

function firstSortOrder(group: PermissionTreeGroup) {
  return group.items[0]?.sort_order || 0;
}

function isGroupExpanded(groupKey: string) {
  return expandedGroupKeys.value.has(groupKey);
}

function toggleGroup(groupKey: string) {
  const expandedKeys = new Set(expandedGroupKeys.value);
  if (expandedKeys.has(groupKey)) {
    expandedKeys.delete(groupKey);
  } else {
    expandedKeys.add(groupKey);
  }
  expandedGroupKeys.value = expandedKeys;
}

function expandAllGroups() {
  expandedGroupKeys.value = new Set(permissionTreeGroups.value.map((group) => group.key));
}

function collapseAllGroups() {
  expandedGroupKeys.value = new Set();
}

function isPermissionChecked(permissionId: number) {
  return checkedPermissionIds.value.includes(permissionId);
}

function setPermissionChecked(permissionId: number, checked: boolean) {
  if (isPermissionReadonly.value) return;
  const checkedIds = new Set(checkedPermissionIds.value);
  if (checked) {
    checkedIds.add(permissionId);
  } else {
    checkedIds.delete(permissionId);
  }
  checkedPermissionIds.value = [...checkedIds];
}

function groupCheckedCount(group: PermissionTreeGroup) {
  return group.items.filter((permission) => isPermissionChecked(permission.id)).length;
}

function isGroupChecked(group: PermissionTreeGroup) {
  return group.items.length > 0 && groupCheckedCount(group) === group.items.length;
}

function isGroupIndeterminate(group: PermissionTreeGroup) {
  const checkedCount = groupCheckedCount(group);
  return checkedCount > 0 && checkedCount < group.items.length;
}

function setGroupChecked(group: PermissionTreeGroup, checked: boolean) {
  if (isPermissionReadonly.value) return;
  const checkedIds = new Set(checkedPermissionIds.value);
  group.items.forEach((permission) => {
    if (checked) {
      checkedIds.add(permission.id);
    } else {
      checkedIds.delete(permission.id);
    }
  });
  checkedPermissionIds.value = [...checkedIds];
}
</script>
