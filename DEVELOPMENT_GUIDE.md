# 开发指南

这份指南只说明新增页面和业务功能的常用路径。优先使用脚手架生成模块，再按业务需要修改生成代码；不要为了新增业务分散修改框架核心注册文件。

## 1. 生成模块

新增普通业务功能时，先生成一套完整 CRUD 骨架：

```bash
node scripts/create-module.mjs task "任务管理" "Tasks"
```

脚手架会生成：

- 前端：模块入口、API 封装、权限常量、CRUD 页面、`zh-CN` / `en-US` 语言包。
- 后端：模块入口、API、model、schema、repository、service 和 pytest 模板。

标准示例参考：

- 前端：`web/src/modules/demo-crud`
- 后端：`server/app/modules/demo_crud`
- 测试：`server/tests/test_auth_rbac.py` 中的 demo CRUD 用例

## 2. 前端页面

前端业务模块放在 `web/src/modules/<module>`，入口固定为 `index.ts`。页面组件优先放在模块内的 `views` 目录。

模块入口声明页面、菜单、权限和加载组件：

```ts
import { Board20Regular } from "@vicons/fluent";

import { defineModule, definePage, routePermission } from "../types";

export default defineModule({
  key: "task",
  version: "0.1.0",
  order: 30,
  dependencies: ["core"],
  pages: [
    definePage({
      key: "task",
      path: "/task",
      titleKey: "route.task",
      component: () => import("./views/TaskManageView.vue"),
      permission: routePermission("task"),
      fallbackOrder: 100,
      menu: { icon: Board20Regular, order: 10 }
    })
  ]
});
```

注意：

- 新页面不要手工修改 `web/src/router/index.ts`、`AppShell.vue` 或主菜单。
- 需要显示到侧边栏才配置 `menu`；不需要菜单入口的页面可以只声明路由。
- 按钮权限优先复用 `PermissionButton`，不要只靠前端隐藏保护接口。

列表页统一使用以下标准布局（参考 `AnnouncementManageView.vue`、`UserManageView.vue`、`StorageManageView.vue`）：

- 工具栏一行放完：左侧 `<page>-filter-row`（grid 布局）只放关键字输入、可选时间范围和查询按钮；右侧放批量操作和新增按钮。
- 枚举类筛选（状态、类型、范围、创建人等）不放工具栏，统一放列头筛选：受控写法 `filter` + `filterMultiple: false` + `filterOptionValue` + `filterOptions`，在 `@update:filters` 中转成后端查询参数并重新加载。
- 时间列用列头排序：`sorter: true` + 受控 `sortOrder`，在 `@update:sorter` 中转成后端 `sort_order`。
- 表格统一 `remote` + 后端分页（`page`/`page_size`/`total`），`flex-height` + `page-data-table`，列宽可拖拽（`withResizableColumns` + `columnWidths` + `@unstable-column-resize`）。
- 操作列 `fixed: "right"`，使用 `table-action-group` 包裹圆形 `quaternary` 图标按钮（`circle` + `NIcon` + `title` 提示），不用文字按钮。
- 对应后端列表接口要支持这些筛选与排序参数，筛选在数据库层完成，不在前端内存过滤。
- 弹窗表单较长需要滚动时，操作按钮放 `n-modal` 的 `#action` 插槽（`form-actions modal-fixed-actions`），按钮固定在弹窗底部，只有表单内容滚动。

## 3. 后端模块

后端业务模块放在 `server/app/modules/<module>`，模块入口暴露 `APP_MODULE`。框架会自动扫描模块，不要在 `server/app/main.py` 手工注册 router。

常用入口结构：

```python
from app.core.module import AppModule, action_code, define_module, page_permission, resource_action, resource_permissions

TASK_READ = action_code("task", "read")

APP_MODULE = define_module(
    AppModule(
        key="task",
        version="0.1.0",
        order=30,
        dependencies=("core",),
        router_paths=("app.modules.task.api:router",),
        model_paths=("app.modules.task.models",),
        page_permissions=(
            page_permission("task", "task", 100, TASK_READ),
        ),
        resource_permissions=(
            resource_permissions(
                "task",
                "task",
                800,
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
)
```

建议按生成骨架保持分层：

- `api.py`：FastAPI router、权限依赖、请求响应模型绑定。
- `models.py`：SQLAlchemy model。
- `schemas.py`：Pydantic schema。
- `repositories.py`：数据库查询和持久化。
- `services.py`：业务规则、审计、权限范围判断。

## 4. 权限和数据范围

权限 code 使用固定规则：

- 页面权限：`route:<page>`
- 功能权限：`action:<resource>:<action>`
- 操作他人数据：`action:<resource>:manage_others`

后端接口必须做权限校验。前端按钮只负责体验，不能作为唯一保护。

如果业务数据区分本人和他人，默认只能操作本人数据；需要操作他人数据时，同时校验基础动作权限和 `manage_others`。新增业务表建议保留 `created_by` 或类似归属字段，便于后续做范围控制和审计。

## 5. 多语言和提示

页面展示文案不要硬编码。公共文案放在 `web/src/i18n/locales/<locale>.json`，模块文案放在 `web/src/modules/<module>/i18n/<locale>.json`。

基本要求：

- 页面标题、菜单、按钮、表单校验、空状态、确认弹窗和枚举展示都使用语言包。
- 页面中使用 `t("...")`；日期时间使用 `formatDateTime`。
- 后端业务响应返回稳定 `code`、英文 fallback `message` 和插值 `params`，不要返回中文业务提示。
- 新增权限、审计动作、OpenAPI 文案时，同步补齐语言包。

## 6. API、Token 和审计

新增业务 API 时：

- 在 router 上设置清晰的 `tags`、`summary`、响应模型和必要错误响应。
- Web-only 管理接口必须使用 `require_web_session`，不能被 API Token 调用。
- 可开放给外部调用的业务接口使用正常权限依赖，API Token 会复用用户角色权限。
- 写操作和高风险操作使用 `record_audit(...)` 记录审计日志，动作 code 保持稳定，例如 `task.create`、`task.update`、`task.delete`。
- 审计详情不要记录密码、完整 Token、密钥等敏感值。

## 7. 数据库变更

开发期可以通过 model、模块迁移和字段同步快速迭代：

- 新表：在 `models.py` 中定义，并把模块路径写入 `model_paths`。
- 小型一次性 SQL：在模块中声明 `migration_step(...)`。
- 开发期补字段：使用 `table_column_sync(...)`。

生产结构变更使用显式 schema migration：

```bash
cd server
python tools/migrate_database.py schema-new "add task indexes"
python tools/migrate_database.py schema-status --url "sqlite:///../runtime/metrix.db"
python tools/migrate_database.py schema-apply --url "sqlite:///../runtime/metrix.db"
python tools/migrate_database.py schema-rollback --url "sqlite:///../runtime/metrix.db"
```

上线前必须先备份数据库。显式 migration 当前保持单线性链，只允许回滚最新已应用修订。

## 8. 测试和检查

新增或修改功能后至少运行：

```bash
cd server
python -m compileall -q app tests
python -m pytest tests -q --basetemp .pytest-temp
```

```bash
cd web
npm run test:smoke
npx vue-tsc --noEmit --noUnusedLocals --noUnusedParameters
npm run build
```

涉及路由守卫、登录态、页面访问或关键交互时，再运行：

```bash
cd web
npm run test:regression
```

首次运行 Playwright 前先执行：

```bash
cd web
npm run test:regression:install
```

## 9. 提交前自查

- 新功能是否放在模块目录内，而不是修改核心注册文件。
- 前后端权限 code、路由、API 路径和语言包是否一致。
- 后端接口是否有真实权限校验。
- 写操作是否记录审计日志。
- 列表是否使用后端分页，数据量变大时不会一次性加载全部。
- 测试、构建和 smoke 是否通过。
