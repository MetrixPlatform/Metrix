<template>
  <section class="work-card">
    <div class="toolbar">
      <strong>待审核用户</strong>
      <n-button @click="loadData">刷新</n-button>
    </div>
    <n-data-table :columns="columns" :data="users" :loading="loading" :row-key="(row) => row.id" :scroll-x="820" />
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
  </section>
</template>

<script setup lang="ts">
import { h, onMounted, reactive, ref } from "vue";
import { NButton, NCheckbox, NCheckboxGroup, NDataTable, NForm, NFormItem, NInput, NModal, NSpace, useMessage } from "naive-ui";
import type { DataTableColumns, FormInst, FormRules } from "naive-ui";

import { approveUser, listPendingUsers, rejectUser } from "../api/approvals";
import { listRoles } from "../api/roles";
import type { RoleItem, UserListItem } from "../api/types";
import { maxLengthRule, validateForm } from "../utils/validation";

const message = useMessage();
const loading = ref(false);
const users = ref<UserListItem[]>([]);
const roles = ref<RoleItem[]>([]);
const current = ref<UserListItem | null>(null);
const rejectFormRef = ref<FormInst | null>(null);
const roleIds = ref<number[]>([]);
const rejectForm = reactive({ reason: "" });
const showApproveModal = ref(false);
const showRejectModal = ref(false);
const rejectRules: FormRules = {
  reason: maxLengthRule("驳回原因", 500)
};

const columns: DataTableColumns<UserListItem> = [
  { title: "账号", key: "username", width: 130 },
  { title: "姓名", key: "full_name", width: 120 },
  { title: "公司", key: "company", width: 140 },
  { title: "部门", key: "department", width: 120 },
  { title: "提交时间", key: "created_at", width: 180 },
  {
    title: "操作",
    key: "actions",
    width: 160,
    render: (row) =>
      h("div", { class: "toolbar-group" }, [
        h(NButton, { size: "small", type: "primary", onClick: () => openApprove(row) }, { default: () => "通过" }),
        h(NButton, { size: "small", type: "error", onClick: () => openReject(row) }, { default: () => "驳回" })
      ])
  }
];

onMounted(async () => {
  await Promise.all([loadData(), loadRoles()]);
});

async function loadData() {
  loading.value = true;
  try {
    users.value = await listPendingUsers();
  } catch (error) {
    message.error((error as Error).message);
  } finally {
    loading.value = false;
  }
}

async function loadRoles() {
  roles.value = await listRoles();
}

function openApprove(user: UserListItem) {
  current.value = user;
  roleIds.value = [];
  showApproveModal.value = true;
}

async function saveApprove() {
  if (!current.value) return;
  try {
    await approveUser(current.value.id, roleIds.value);
    showApproveModal.value = false;
    await loadData();
    message.success("已审核通过");
  } catch (error) {
    message.error((error as Error).message);
  }
}

function openReject(user: UserListItem) {
  current.value = user;
  rejectForm.reason = "";
  showRejectModal.value = true;
}

async function saveReject() {
  if (!current.value) return;
  if (!(await validateForm(rejectFormRef.value))) return;
  try {
    await rejectUser(current.value.id, rejectForm.reason);
    showRejectModal.value = false;
    await loadData();
    message.success("已驳回");
  } catch (error) {
    message.error((error as Error).message);
  }
}
</script>
