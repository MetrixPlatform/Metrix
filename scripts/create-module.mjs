import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const [rawName, zhTitleArg, enTitleArg] = process.argv.slice(2);

if (!rawName) {
  fail('Usage: node scripts/create-module.mjs <module-name> ["Chinese title"] ["English title"]');
}

const kebab = toKebab(rawName);
if (!/^[a-z][a-z0-9-]*$/.test(kebab)) {
  fail("Module name must start with a letter and contain only letters, numbers, dashes or underscores.");
}

const snake = kebab.replaceAll("-", "_");
const camel = toCamel(kebab);
const pascal = toPascal(kebab);
const constant = snake.toUpperCase();
const pluralKebab = pluralizeKebab(kebab);
const pluralSnake = pluralKebab.replaceAll("-", "_");
const pluralPascal = toPascal(pluralKebab);
const zhTitle = zhTitleArg || kebab;
const enTitle = enTitleArg || toTitle(kebab);
const replacements = {
  __KEBAB__: kebab,
  __SNAKE__: snake,
  __CAMEL__: camel,
  __PASCAL__: pascal,
  __CONSTANT__: constant,
  __PLURAL_KEBAB__: pluralKebab,
  __PLURAL_SNAKE__: pluralSnake,
  __PLURAL_PASCAL__: pluralPascal,
  __TABLE_NAME__: pluralSnake,
  __ZH_TITLE__: zhTitle,
  __EN_TITLE__: enTitle
};

const targets = [
  ["web module", path.join(rootDir, "web", "src", "modules", kebab)],
  ["server module", path.join(rootDir, "server", "app", "modules", snake)],
  ["server module test", path.join(rootDir, "server", "tests", `test_${snake}_module.py`)]
];

for (const [label, target] of targets) {
  if (existsSync(target)) {
    fail(`${label} already exists: ${target}`);
  }
}

write(path.join(rootDir, "web", "src", "modules", kebab, "index.ts"), webIndexTemplate());
write(path.join(rootDir, "web", "src", "modules", kebab, "api.ts"), webApiTemplate());
write(path.join(rootDir, "web", "src", "modules", kebab, "permissions.ts"), webPermissionsTemplate());
write(path.join(rootDir, "web", "src", "modules", kebab, "views", `${pascal}View.vue`), webViewTemplate());
write(path.join(rootDir, "web", "src", "modules", kebab, "i18n", "zh-CN.json"), jsonTemplate(zhLocale()));
write(path.join(rootDir, "web", "src", "modules", kebab, "i18n", "en-US.json"), jsonTemplate(enLocale()));
write(path.join(rootDir, "server", "app", "modules", snake, "__init__.py"), serverInitTemplate());
write(path.join(rootDir, "server", "app", "modules", snake, "api.py"), serverApiTemplate());
write(path.join(rootDir, "server", "app", "modules", snake, "models.py"), serverModelsTemplate());
write(path.join(rootDir, "server", "app", "modules", snake, "schemas.py"), serverSchemasTemplate());
write(path.join(rootDir, "server", "app", "modules", snake, "repositories.py"), serverRepositoriesTemplate());
write(path.join(rootDir, "server", "app", "modules", snake, "services.py"), serverServicesTemplate());
write(path.join(rootDir, "server", "tests", `test_${snake}_module.py`), serverTestTemplate());

console.log(`Created module ${kebab}`);
console.log(`Web:    web/src/modules/${kebab}`);
console.log(`Server: server/app/modules/${snake}`);
console.log(`Test:   server/tests/test_${snake}_module.py`);

function write(filePath, content) {
  mkdirSync(path.dirname(filePath), { recursive: true });
  writeFileSync(filePath, `${content.trimEnd()}\n`, "utf-8");
}

function webIndexTemplate() {
  return render(`import { Database20Regular } from "@vicons/fluent";

import { defineMenuGroup, defineModule, definePage, routePermission } from "../types";

export default defineModule({
  key: "__KEBAB__",
  version: "0.1.0",
  order: 100,
  dependencies: ["core"],
  menuGroups: [
    defineMenuGroup({ key: "__CAMEL__Group", labelKey: "route.group.__CAMEL__", icon: Database20Regular, order: 100 })
  ],
  pages: [
    definePage({
      key: "__CAMEL__",
      path: "/__KEBAB__",
      titleKey: "route.__CAMEL__",
      component: () => import("./views/__PASCAL__View.vue"),
      permission: routePermission("__SNAKE__"),
      fallbackOrder: 100,
      menu: { group: "__CAMEL__Group", icon: Database20Regular, order: 10 }
    })
  ]
});`);
}

function webApiTemplate() {
  return render(`import { del, post, put, queryString, request } from "../../api/client";
import type { PageResult, ServerMessage } from "../../api/types";

export interface __PASCAL__ {
  id: number;
  name: string;
  category: string;
  description: string;
  is_active: boolean;
  created_by: number | null;
  created_by_username: string;
  created_at: string;
  updated_at: string;
}

export interface __PASCAL__Payload {
  name: string;
  category: string;
  description: string;
  is_active: boolean;
}

export interface __PASCAL__Filters {
  keyword?: string;
  category?: string;
  is_active?: boolean | null;
  created_by?: "all" | "me" | "";
  sort_order?: "ascend" | "descend";
  page?: number;
  page_size?: number;
}

export function list__PLURAL_PASCAL__(filters: __PASCAL__Filters = {}) {
  return request<PageResult<__PASCAL__>>("/__PLURAL_KEBAB__" + queryString(filters));
}

export function create__PASCAL__(payload: __PASCAL__Payload) {
  return post<__PASCAL__>("/__PLURAL_KEBAB__", payload);
}

export function update__PASCAL__(itemId: number, payload: __PASCAL__Payload) {
  return put<__PASCAL__>("/__PLURAL_KEBAB__/" + itemId, payload);
}

export function delete__PASCAL__(itemId: number) {
  return del<ServerMessage>("/__PLURAL_KEBAB__/" + itemId);
}`);
}

function webPermissionsTemplate() {
  return render(`import { actionPermission } from "../types";

export const __CONSTANT___CREATE = actionPermission("__SNAKE__", "create");
export const __CONSTANT___UPDATE = actionPermission("__SNAKE__", "update");
export const __CONSTANT___DELETE = actionPermission("__SNAKE__", "delete");
export const __CONSTANT___MANAGE_OTHERS = actionPermission("__SNAKE__", "manage_others");
`);
}

function webViewTemplate() {
  return render(`<template>
  <section class="work-card table-page-card">
    <div class="toolbar">
      <div class="toolbar-group">
        <n-input v-model:value="filters.keyword" class="filter-keyword" :placeholder="t('__CAMEL__.searchPlaceholder')" clearable />
        <n-input v-model:value="filters.category" :placeholder="t('__CAMEL__.categoryPlaceholder')" clearable />
        <n-button @click="searchItems">{{ t("common.search") }}</n-button>
      </div>
      <permission-button :permission="__CONSTANT___CREATE" type="primary" @click="openCreate">{{ t("__CAMEL__.add") }}</permission-button>
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

    <n-modal v-model:show="showModal" preset="card" class="modal-card" :title="editingItem ? t('__CAMEL__.edit') : t('__CAMEL__.add')">
      <n-form ref="formRef" class="form-stack inline-form" :model="form" :rules="rules" label-placement="left" label-width="auto">
        <n-form-item :label="t('__CAMEL__.field.name')" path="name">
          <n-input v-model:value="form.name" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('__CAMEL__.field.category')" path="category">
          <n-input v-model:value="form.category" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('__CAMEL__.field.description')" path="description">
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
import { create__PASCAL__, delete__PASCAL__, list__PLURAL_PASCAL__, update__PASCAL__, type __PASCAL__, type __PASCAL__Payload } from "../api";
import { __CONSTANT___CREATE, __CONSTANT___DELETE, __CONSTANT___MANAGE_OTHERS, __CONSTANT___UPDATE } from "../permissions";

type ActiveFilter = "true" | "false";
type CreatorFilter = "all" | "me";

const message = useMessage();
const dialog = useDialog();
const loading = ref(false);
const showModal = ref(false);
const formRef = ref<FormInst | null>(null);
const editingItem = ref<__PASCAL__ | null>(null);
const items = ref<__PASCAL__[]>([]);
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
const form = reactive<__PASCAL__Payload>({
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
  name: [requiredRule(t("__CAMEL__.field.name")), maxLengthRule(t("__CAMEL__.field.name"), 120)],
  category: maxLengthRule(t("__CAMEL__.field.category"), 80),
  description: maxLengthRule(t("__CAMEL__.field.description"), 1000)
}));
const activeOptions = computed(() => [
  { label: t("common.enabled"), value: "true" },
  { label: t("common.disabled"), value: "false" }
]);
const creatorOptions = computed(() => [
  { label: t("__CAMEL__.creatorAll"), value: "all" },
  { label: t("__CAMEL__.creatorMe"), value: "me" }
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
const columns = computed<DataTableColumns<__PASCAL__>>(() =>
  withResizableColumns([
    { title: t("__CAMEL__.field.name"), key: "name", width: columnWidths.name },
    { title: t("__CAMEL__.field.category"), key: "category", width: columnWidths.category },
    { title: t("__CAMEL__.field.description"), key: "description", ellipsis: { tooltip: true }, width: columnWidths.description },
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
          authStore.has(__CONSTANT___UPDATE) && canManage(row)
            ? h(NButton, { size: "small", quaternary: true, onClick: () => openEdit(row) }, () => t("common.edit"))
            : null,
          authStore.has(__CONSTANT___DELETE) && canManage(row)
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
    const result = await list__PLURAL_PASCAL__({
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

function openEdit(item: __PASCAL__) {
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
      await update__PASCAL__(editingItem.value.id, form);
    } else {
      await create__PASCAL__(form);
    }
    showModal.value = false;
    await loadItems();
    message.success(t("__CAMEL__.saved"));
  } catch (error) {
    showError(message, error);
  }
}

function confirmDelete(item: __PASCAL__) {
  dialog.warning({
    title: t("__CAMEL__.deleteTitle"),
    content: t("__CAMEL__.deleteConfirm", { name: item.name }),
    positiveText: t("common.delete"),
    negativeText: t("common.cancel"),
    onPositiveClick: () => void removeItem(item)
  });
}

async function removeItem(item: __PASCAL__) {
  try {
    const result = await delete__PASCAL__(item.id);
    await loadItems();
    message.success(messageText(result, "__CAMEL__.deleted"));
  } catch (error) {
    showError(message, error);
  }
}

function canManage(item: __PASCAL__) {
  return item.created_by === authStore.user?.id || authStore.has(__CONSTANT___MANAGE_OTHERS);
}

function isActiveFilter(value: unknown): value is ActiveFilter {
  return value === "true" || value === "false";
}

function isCreatorFilter(value: unknown): value is CreatorFilter {
  return value === "all" || value === "me";
}
</script>`);
}

function serverInitTemplate() {
  return render(`from app.core.module import AppModule, action_code, define_module, page_permission, resource_action, resource_permissions

__CONSTANT___CREATE = action_code("__SNAKE__", "create")
__CONSTANT___READ = action_code("__SNAKE__", "read")
__CONSTANT___UPDATE = action_code("__SNAKE__", "update")
__CONSTANT___DELETE = action_code("__SNAKE__", "delete")
__CONSTANT___MANAGE_OTHERS = action_code("__SNAKE__", "manage_others")

APP_MODULE = define_module(
    AppModule(
        key="__SNAKE__",
        version="0.1.0",
        order=100,
        dependencies=("core",),
        router_paths=("app.modules.__SNAKE__.api:router",),
        model_paths=("app.modules.__SNAKE__.models",),
        page_permissions=(
            page_permission("__SNAKE__", "__SNAKE__", 1000, __CONSTANT___READ),
        ),
        resource_permissions=(
            resource_permissions(
                "__SNAKE__",
                "__CAMEL__",
                1010,
                (
                    resource_action("create", 10),
                    resource_action("read", 20),
                    resource_action("update", 30),
                    resource_action("delete", 40),
                    resource_action("manage_others", 50),
                ),
            ),
        ),
    )
)`);
}

function serverApiTemplate() {
  return render(`from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.db.session import get_db
from app.models import User
from app.modules.__SNAKE__ import __CONSTANT___CREATE, __CONSTANT___DELETE, __CONSTANT___READ, __CONSTANT___UPDATE
from app.modules.__SNAKE__.schemas import __PASCAL__Item, __PASCAL__ListResponse, __PASCAL__Payload
from app.modules.__SNAKE__.services import __PASCAL__Service
from app.schemas.common import MessageResponse, message_response

router = APIRouter(prefix="/api/__PLURAL_KEBAB__", tags=["__PLURAL_KEBAB__"])


@router.get("", response_model=__PASCAL__ListResponse)
def list___PLURAL_SNAKE__(
    keyword: str = "",
    category: str = "",
    is_active: bool | None = None,
    created_by: str = "",
    sort_order: str = "descend",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(__CONSTANT___READ)),
) -> __PASCAL__ListResponse:
    return __PASCAL__Service(db).list_items(actor, keyword, category, is_active, created_by, sort_order, page, page_size)


@router.post("", response_model=__PASCAL__Item)
def create___SNAKE__(
    payload: __PASCAL__Payload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(__CONSTANT___CREATE)),
) -> __PASCAL__Item:
    return __PASCAL__Service(db).create(actor, payload)


@router.put("/{item_id}", response_model=__PASCAL__Item)
def update___SNAKE__(
    item_id: int,
    payload: __PASCAL__Payload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(__CONSTANT___UPDATE)),
) -> __PASCAL__Item:
    return __PASCAL__Service(db).update(actor, item_id, payload)


@router.delete("/{item_id}", response_model=MessageResponse)
def delete___SNAKE__(
    item_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(__CONSTANT___DELETE)),
) -> MessageResponse:
    __PASCAL__Service(db).delete(actor, item_id)
    return message_response("__CAMEL__.deleted", "__EN_TITLE__ deleted")`);
}

function serverModelsTemplate() {
  return render(`from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now
from app.db.base import Base


class __PASCAL__(Base):
    __tablename__ = "__TABLE_NAME__"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str] = mapped_column(String(80), default="", index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)`);
}

function serverSchemasTemplate() {
  return render(`from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class __PASCAL__Payload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(default="", max_length=80)
    description: str = Field(default="", max_length=1000)
    is_active: bool = True

    @field_validator("name", "category", "description")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()


class __PASCAL__Item(__PASCAL__Payload):
    id: int
    created_by: int | None
    created_by_username: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class __PASCAL__ListResponse(BaseModel):
    items: list[__PASCAL__Item]
    total: int
    page: int
    page_size: int`);
}

function serverRepositoriesTemplate() {
  return render(`from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import User
from app.modules.__SNAKE__.models import __PASCAL__


class __PASCAL__Repository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, item_id: int) -> __PASCAL__ | None:
        return self.db.get(__PASCAL__, item_id)

    def list(
        self,
        keyword: str = "",
        category: str = "",
        is_active: bool | None = None,
        created_by_user_id: int | None = None,
        created_at_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[__PASCAL__], int]:
        query = self.db.query(__PASCAL__)
        if keyword:
            pattern = f"%{keyword}%"
            query = query.filter(or_(__PASCAL__.name.ilike(pattern), __PASCAL__.description.ilike(pattern)))
        if category:
            query = query.filter(__PASCAL__.category == category)
        if is_active is not None:
            query = query.filter(__PASCAL__.is_active == is_active)
        if created_by_user_id is not None:
            query = query.filter(__PASCAL__.created_by == created_by_user_id)
        total = query.count()
        if created_at_order == "ascend":
            query = query.order_by(__PASCAL__.created_at.asc(), __PASCAL__.id.asc())
        else:
            query = query.order_by(__PASCAL__.created_at.desc(), __PASCAL__.id.desc())
        return query.offset((page - 1) * page_size).limit(page_size).all(), total

    def create(self, item: __PASCAL__) -> __PASCAL__:
        self.db.add(item)
        self.db.flush()
        return item

    def delete(self, item: __PASCAL__) -> None:
        self.db.delete(item)
        self.db.flush()

    def creator_usernames(self, user_ids: set[int]) -> dict[int, str]:
        if not user_ids:
            return {}
        rows = self.db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
        return {user_id: username for user_id, username in rows}`);
}

function serverServicesTemplate() {
  return render(`from sqlalchemy.orm import Session

from app.core.exceptions import forbidden, not_found
from app.models import User
from app.modules.__SNAKE__ import __CONSTANT___MANAGE_OTHERS
from app.modules.__SNAKE__.models import __PASCAL__
from app.modules.__SNAKE__.repositories import __PASCAL__Repository
from app.modules.__SNAKE__.schemas import __PASCAL__Item, __PASCAL__ListResponse, __PASCAL__Payload
from app.services.audit import audit_changes, audit_detail, record_audit
from app.services.permissions import has_permission


class __PASCAL__Service:
    def __init__(self, db: Session):
        self.db = db
        self.items = __PASCAL__Repository(db)

    def list_items(
        self,
        actor: User,
        keyword: str = "",
        category: str = "",
        is_active: bool | None = None,
        created_by: str = "",
        sort_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> __PASCAL__ListResponse:
        created_by_user_id = actor.id if created_by == "me" else None
        created_at_order = "ascend" if sort_order == "ascend" else "descend"
        items, total = self.items.list(
            keyword,
            category,
            is_active,
            created_by_user_id,
            created_at_order,
            page,
            page_size,
        )
        return __PASCAL__ListResponse(
            items=self._with_creator_usernames(items),
            total=total,
            page=page,
            page_size=page_size,
        )

    def create(self, actor: User, payload: __PASCAL__Payload) -> __PASCAL__Item:
        item = self.items.create(
            __PASCAL__(
                name=payload.name,
                category=payload.category,
                description=payload.description,
                is_active=payload.is_active,
                created_by=actor.id,
            )
        )
        record_audit(
            self.db,
            actor.id,
            "__SNAKE__.create",
            "__SNAKE__",
            str(item.id),
            item.name,
            audit_detail(item.name, meta=___SNAKE___snapshot(item)),
        )
        self.db.commit()
        return self._with_creator_username(item, actor.username)

    def update(self, actor: User, item_id: int, payload: __PASCAL__Payload) -> __PASCAL__Item:
        item = self._get(item_id)
        self._ensure_can_manage(actor, item)
        before = ___SNAKE___snapshot(item)
        item.name = payload.name
        item.category = payload.category
        item.description = payload.description
        item.is_active = payload.is_active
        record_audit(
            self.db,
            actor.id,
            "__SNAKE__.update",
            "__SNAKE__",
            str(item.id),
            item.name,
            audit_detail(item.name, audit_changes(before, ___SNAKE___snapshot(item))),
        )
        self.db.commit()
        creator_name = actor.username if item.created_by == actor.id else self._creator_username(item)
        return self._with_creator_username(item, creator_name)

    def delete(self, actor: User, item_id: int) -> None:
        item = self._get(item_id)
        self._ensure_can_manage(actor, item)
        record_audit(
            self.db,
            actor.id,
            "__SNAKE__.delete",
            "__SNAKE__",
            str(item.id),
            item.name,
            audit_detail(item.name, meta=___SNAKE___snapshot(item)),
        )
        self.items.delete(item)
        self.db.commit()

    def _get(self, item_id: int) -> __PASCAL__:
        item = self.items.get(item_id)
        if item is None:
            raise not_found("error.__CAMEL__NotFound", "__EN_TITLE__ not found")
        return item

    def _ensure_can_manage(self, actor: User, item: __PASCAL__) -> None:
        if item.created_by == actor.id:
            return
        if has_permission(actor, __CONSTANT___MANAGE_OTHERS):
            return
        raise forbidden("error.__CAMEL__ManageOthersDenied", "You cannot manage __EN_TITLE__ records created by others")

    def _with_creator_usernames(self, items: list[__PASCAL__]) -> list[__PASCAL__Item]:
        user_ids = {item.created_by for item in items if item.created_by is not None}
        usernames = self.items.creator_usernames(user_ids)
        return [self._with_creator_username(item, usernames.get(item.created_by, "")) for item in items]

    def _with_creator_username(self, item: __PASCAL__, username: str) -> __PASCAL__Item:
        return __PASCAL__Item.model_validate(item).model_copy(update={"created_by_username": username})

    def _creator_username(self, item: __PASCAL__) -> str:
        if item.created_by is None:
            return ""
        return self.items.creator_usernames({item.created_by}).get(item.created_by, "")


def ___SNAKE___snapshot(item: __PASCAL__) -> dict[str, object]:
    return {
        "name": item.name,
        "category": item.category,
        "description": item.description,
        "is_active": item.is_active,
    }`);
}

function serverTestTemplate() {
  return render(`from test_auth_rbac import install_sqlite, login, create_client


def test___SNAKE___crud_module(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    headers = login(client, payload["admin_username"], payload["admin_password"])

    permissions = client.get("/api/permissions", headers=headers).json()
    codes = {item["code"] for item in permissions}
    assert {
        "route:__SNAKE__",
        "action:__SNAKE__:create",
        "action:__SNAKE__:read",
        "action:__SNAKE__:update",
        "action:__SNAKE__:delete",
        "action:__SNAKE__:manage_others",
    }.issubset(codes)

    created = client.post(
        "/api/__PLURAL_KEBAB__",
        json={"name": "First", "category": "General", "description": "Created by generated module test", "is_active": True},
        headers=headers,
    )
    assert created.status_code == 200
    item_id = created.json()["id"]

    listed = client.get("/api/__PLURAL_KEBAB__?keyword=First&page=1&page_size=20", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    updated = client.put(
        f"/api/__PLURAL_KEBAB__/{item_id}",
        json={"name": "Updated", "category": "General", "description": "Updated by generated module test", "is_active": False},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated"

    deleted = client.delete(f"/api/__PLURAL_KEBAB__/{item_id}", headers=headers)
    assert deleted.status_code == 200

    audit_logs = client.get("/api/audit-logs?target_type=__SNAKE__", headers=headers)
    assert audit_logs.status_code == 200
    assert {item["action"] for item in audit_logs.json()["items"]} >= {"__SNAKE__.create", "__SNAKE__.update", "__SNAKE__.delete"}`);
}

function zhLocale() {
  return {
    route: {
      [camel]: zhTitle,
      group: {
        [camel]: zhTitle
      }
    },
    permission: {
      group: {
        [camel]: zhTitle
      },
      [`route:${snake}`]: zhTitle,
      [`action:${snake}:create`]: `新增${zhTitle}`,
      [`action:${snake}:read`]: `查询${zhTitle}`,
      [`action:${snake}:update`]: `修改${zhTitle}`,
      [`action:${snake}:delete`]: `删除${zhTitle}`,
      [`action:${snake}:manage_others`]: `操作他人${zhTitle}`
    },
    error: {
      [`${camel}NotFound`]: `${zhTitle}不存在`,
      [`${camel}ManageOthersDenied`]: `无权限操作他人${zhTitle}`
    },
    [camel]: {
      searchPlaceholder: "搜索名称、说明",
      categoryPlaceholder: "筛选分类",
      add: `新增${zhTitle}`,
      edit: `编辑${zhTitle}`,
      saved: `${zhTitle}已保存`,
      deleted: `${zhTitle}已删除`,
      deleteTitle: `删除${zhTitle}`,
      deleteConfirm: `确认删除${zhTitle} {name}？`,
      creatorAll: "全部人",
      creatorMe: "仅自己",
      field: {
        name: "名称",
        category: "分类",
        description: "说明"
      }
    },
    auditLog: {
      action: {
        [snake]: {
          create: `新增${zhTitle}`,
          update: `修改${zhTitle}`,
          delete: `删除${zhTitle}`
        }
      },
      target: {
        [snake]: zhTitle
      },
      field: {
        name: "名称",
        category: "分类",
        description: "说明"
      }
    }
  };
}

function enLocale() {
  return {
    route: {
      [camel]: enTitle,
      group: {
        [camel]: enTitle
      }
    },
    permission: {
      group: {
        [camel]: enTitle
      },
      [`route:${snake}`]: enTitle,
      [`action:${snake}:create`]: `Create ${enTitle}`,
      [`action:${snake}:read`]: `Read ${enTitle}`,
      [`action:${snake}:update`]: `Update ${enTitle}`,
      [`action:${snake}:delete`]: `Delete ${enTitle}`,
      [`action:${snake}:manage_others`]: `Manage others' ${enTitle}`
    },
    error: {
      [`${camel}NotFound`]: `${enTitle} not found`,
      [`${camel}ManageOthersDenied`]: `You cannot manage ${enTitle} records created by others`
    },
    [camel]: {
      searchPlaceholder: "Search name or description",
      categoryPlaceholder: "Filter category",
      add: `New ${enTitle}`,
      edit: `Edit ${enTitle}`,
      saved: `${enTitle} saved`,
      deleted: `${enTitle} deleted`,
      deleteTitle: `Delete ${enTitle}`,
      deleteConfirm: `Delete ${enTitle} {name}?`,
      creatorAll: "All users",
      creatorMe: "Only mine",
      field: {
        name: "Name",
        category: "Category",
        description: "Description"
      }
    },
    auditLog: {
      action: {
        [snake]: {
          create: `Create ${enTitle}`,
          update: `Update ${enTitle}`,
          delete: `Delete ${enTitle}`
        }
      },
      target: {
        [snake]: enTitle
      },
      field: {
        name: "Name",
        category: "Category",
        description: "Description"
      }
    }
  };
}

function render(template) {
  return Object.entries(replacements).reduce((output, [key, value]) => output.replaceAll(key, value), template);
}

function jsonTemplate(data) {
  return JSON.stringify(data, null, 2);
}

function pluralizeKebab(value) {
  const parts = value.split("-");
  const last = parts.pop();
  parts.push(pluralizeWord(last || value));
  return parts.join("-");
}

function pluralizeWord(value) {
  if (value.endsWith("y") && !/[aeiou]y$/.test(value)) {
    return `${value.slice(0, -1)}ies`;
  }
  if (/(s|x|z|ch|sh)$/.test(value)) {
    return `${value}es`;
  }
  return `${value}s`;
}

function toKebab(value) {
  return value
    .trim()
    .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
    .replace(/_/g, "-")
    .replace(/[^a-zA-Z0-9-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .replace(/-+/g, "-")
    .toLowerCase();
}

function toCamel(value) {
  return value.replace(/-([a-z0-9])/g, (_, char) => char.toUpperCase());
}

function toPascal(value) {
  const camelValue = toCamel(value);
  return camelValue.charAt(0).toUpperCase() + camelValue.slice(1);
}

function toTitle(value) {
  return value
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
