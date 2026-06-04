<template>
  <section class="work-card announcement-manage-card">
    <div class="toolbar">
      <strong>公告管理</strong>
      <permission-button permission="action:announcement:create" type="primary" @click="openCreate">新增公告</permission-button>
    </div>
    <n-data-table :columns="columns" :data="announcements" :loading="loading" :row-key="(row) => row.id" :scroll-x="980" />

    <n-modal v-model:show="showModal" preset="card" class="modal-card announcement-edit-modal" :title="editing ? '编辑公告' : '新增公告'">
      <n-form ref="formRef" class="form-stack inline-form" :model="form" :rules="rules" label-placement="left" label-width="96">
        <n-form-item label="标题" path="title">
          <n-input v-model:value="form.title" placeholder="请输入公告标题" />
        </n-form-item>
        <n-form-item label="内容" path="content">
          <n-input v-model:value="form.content" type="textarea" placeholder="请输入公告内容" />
        </n-form-item>
        <n-form-item label="推送范围">
          <n-select v-model:value="form.target_type" :options="targetTypeOptions" />
        </n-form-item>
        <n-form-item v-if="form.target_type === 'permission'" label="权限编码">
          <n-input v-model:value="form.target_value" placeholder="多个权限用逗号分隔，如 route:users" />
        </n-form-item>
        <n-form-item v-if="form.target_type === 'company'" label="公司">
          <n-input v-model:value="form.target_value" placeholder="请输入公司名称" />
        </n-form-item>
        <template v-if="form.target_type === 'company_department'">
          <n-form-item label="公司">
            <n-input v-model:value="targetCompany" placeholder="请输入公司名称" />
          </n-form-item>
          <n-form-item label="部门/职位">
            <n-input v-model:value="targetDepartment" placeholder="请输入部门或职位" />
          </n-form-item>
        </template>
        <n-form-item v-if="form.target_type === 'user'" label="账号">
          <n-input v-model:value="form.target_value" type="textarea" placeholder="多个账号用逗号或换行分隔" />
        </n-form-item>
        <n-form-item label="展示方式" path="display_modes">
          <n-checkbox-group v-model:value="form.display_modes">
            <n-space>
              <n-checkbox value="popup">弹窗</n-checkbox>
              <n-checkbox value="ticker">滚动条</n-checkbox>
              <n-checkbox value="sidebar">首页侧栏</n-checkbox>
            </n-space>
          </n-checkbox-group>
        </n-form-item>
        <n-form-item label="启用">
          <n-switch v-model:value="form.is_active" />
        </n-form-item>
        <div class="form-actions">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="saveAnnouncement">保存</n-button>
        </div>
      </n-form>
    </n-modal>
  </section>
</template>

<script setup lang="ts">
import { h, onMounted, reactive, ref } from "vue";
import { Delete20Regular, Edit20Regular } from "@vicons/fluent";
import {
  NButton,
  NCheckbox,
  NCheckboxGroup,
  NDataTable,
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
import type { DataTableColumns, FormInst, FormRules } from "naive-ui";

import { createAnnouncement, deleteAnnouncement, listAnnouncements, updateAnnouncement, type AnnouncementPayload } from "../api/announcements";
import type { AnnouncementItem, AnnouncementTargetType } from "../api/types";
import PermissionButton from "../components/PermissionButton.vue";
import StatusTag from "../components/StatusTag.vue";
import { authStore } from "../stores/auth";
import { showError } from "../utils/message";
import { maxLengthRule, requiredRule, validateForm } from "../utils/validation";

const message = useMessage();
const dialog = useDialog();
const loading = ref(false);
const announcements = ref<AnnouncementItem[]>([]);
const showModal = ref(false);
const editing = ref<AnnouncementItem | null>(null);
const formRef = ref<FormInst | null>(null);
const targetCompany = ref("");
const targetDepartment = ref("");
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
const rules: FormRules = {
  title: [requiredRule("标题"), maxLengthRule("标题", 120)],
  content: [requiredRule("内容"), maxLengthRule("内容", 2000)],
  display_modes: {
    validator: () => form.display_modes.length > 0,
    message: "请至少选择一种展示方式",
    trigger: "change"
  }
};

const targetTypeOptions = [
  { label: "全平台", value: "all" },
  { label: "全部用户", value: "authenticated" },
  { label: "指定权限", value: "permission" },
  { label: "指定公司", value: "company" },
  { label: "指定公司-部门/职位", value: "company_department" },
  { label: "指定账号", value: "user" }
];

const columns: DataTableColumns<AnnouncementItem> = [
  { title: "标题", key: "title", width: 180 },
  { title: "推送范围", key: "target_type", width: 180, render: (row) => targetLabel(row) },
  { title: "展示方式", key: "display", width: 150, render: (row) => displayLabel(row) },
  { title: "状态", key: "is_active", width: 90, render: (row) => h(StatusTag, { status: row.is_active }) },
  { title: "创建时间", key: "created_at", width: 170, render: (row) => formatTime(row.created_at) },
  {
    title: "操作",
    key: "actions",
    width: 130,
    render: (row) =>
      h(
        "div",
        { class: "table-action-group" },
        [
          authStore.has("action:announcement:update")
            ? h(
                NButton,
                { size: "small", quaternary: true, circle: true, title: "编辑", onClick: () => openEdit(row) },
                { icon: () => h(NIcon, { component: Edit20Regular }) }
              )
            : null,
          authStore.has("action:announcement:delete")
            ? h(
                NButton,
                { size: "small", quaternary: true, circle: true, title: "删除", type: "error", onClick: () => removeAnnouncement(row) },
                { icon: () => h(NIcon, { component: Delete20Regular }) }
              )
            : null
        ].filter(Boolean)
      )
  }
];

onMounted(async () => {
  await loadAnnouncements();
});

async function loadAnnouncements() {
  loading.value = true;
  try {
    announcements.value = await listAnnouncements();
  } catch (error) {
    showError(message, error);
  } finally {
    loading.value = false;
  }
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
    message.success("公告已保存");
  } catch (error) {
    showError(message, error);
  }
}

function buildPayload(): AnnouncementPayload | null {
  const modes = new Set(form.display_modes);
  const targetValue = normalizedTargetValue();
  if (!["all", "authenticated"].includes(form.target_type) && !targetValue) {
    message.error("请填写推送目标");
    return null;
  }
  if (modes.size === 0) {
    message.error("请至少选择一种展示方式");
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
    title: "删除公告",
    content: `确认删除公告 ${row.title}？`,
    positiveText: "删除",
    negativeText: "取消",
    onPositiveClick: async () => {
      try {
        await deleteAnnouncement(row.id);
        await loadAnnouncements();
        message.success("公告已删除");
      } catch (error) {
        showError(message, error);
      }
    }
  });
}

function targetLabel(row: AnnouncementItem) {
  const labels: Record<AnnouncementTargetType, string> = {
    all: "全平台",
    authenticated: "全部用户",
    permission: "权限",
    company: "公司",
    company_department: "公司-部门/职位",
    user: "账号"
  };
  return ["all", "authenticated"].includes(row.target_type) ? labels[row.target_type] : `${labels[row.target_type]}：${formatTargetValue(row)}`;
}

function displayLabel(row: AnnouncementItem) {
  return [
    row.show_popup ? "弹窗" : "",
    row.show_ticker ? "滚动条" : "",
    row.show_sidebar ? "首页侧栏" : ""
  ].filter(Boolean).join("、");
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
  return new Date(value).toLocaleString();
}
</script>
