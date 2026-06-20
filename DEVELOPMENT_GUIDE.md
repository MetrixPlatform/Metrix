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

import { actionPermission, defineModule, definePage } from "../types";

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
      permission: actionPermission("task", "read"),
      fallbackOrder: 100,
      menu: { icon: Board20Regular, order: 10 }
    })
  ]
});
```

注意：

- 新页面不要手工修改 `web/src/router/index.ts`、`AppShell.vue` 或主菜单。
- 需要显示到侧边栏才配置 `menu`；不需要菜单入口的页面可以只声明路由。
- 侧边栏默认顺序约定：`首页`、`储存管理`、`数据库管理`、`容器管理`、业务/模板新建菜单、`系统管理`。`系统管理` 分组固定作为底部管理入口，新增模块或脚手架生成的导航菜单默认放在 `系统管理` 上面。
- 按钮权限优先复用 `PermissionButton`，不要只靠前端隐藏保护接口。

列表页统一使用以下标准布局（参考 `AnnouncementManageView.vue`、`UserManageView.vue`、`StorageManageView.vue`）：

- 工具栏必须一行放完，不允许因为类型、状态、查询按钮等控件换行撑乱页面；左侧 `<page>-filter-row`（grid 布局）只放关键字输入、可选时间范围和查询按钮；右侧放批量操作、新增、刷新等动作按钮。
- 枚举类筛选（状态、类型、范围、创建人等）禁止放工具栏，统一放列头筛选：受控写法 `filter` + `filterMultiple: false` + `filterOptionValue` + `filterOptions`，在 `@update:filters` 中转成后端查询参数并重新加载。
- 时间列用列头排序：`sorter: true` + 受控 `sortOrder`，在 `@update:sorter` 中转成后端 `sort_order`。
- 表格统一 `remote` + 后端分页（`page`/`page_size`/`total`），`flex-height` + `page-data-table`，列宽可拖拽（`withResizableColumns` + 响应式 `columnWidths` + `sumColumnWidths` + `@unstable-column-resize` + `updateColumnWidth`）；操作列不参与拖拽。
- 操作列 `fixed: "right"`，使用 `table-action-group` 包裹圆形 `quaternary` 图标按钮（`circle` + `NIcon` + `title` 提示），不用文字按钮。
- 对应后端列表接口要支持这些筛选与排序参数，筛选在数据库层完成，不在前端内存过滤。
- 弹窗表单较长需要滚动时，操作按钮放 `n-modal` 的 `#action` 插槽（`form-actions modal-fixed-actions`），按钮固定在弹窗底部，只有表单内容滚动。

## 3. 后端模块

后端业务模块放在 `server/app/modules/<module>`，模块入口暴露 `APP_MODULE`。框架会自动扫描模块，不要在 `server/app/main.py` 手工注册 router。

常用入口结构：

```python
from app.core.module import AppModule, action_code, define_module, resource_action, resource_permissions

TASK_READ = action_code("task", "read")

APP_MODULE = define_module(
    AppModule(
        key="task",
        version="0.1.0",
        order=30,
        dependencies=("core",),
        router_paths=("app.modules.task.api:router",),
        model_paths=("app.modules.task.models",),
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

- 功能权限：`action:<resource>:<action>`
- 页面/导航权限：用该资源的查询权限 `action:<resource>:read` 充当；前端页面 `permission` 直接填 `actionPermission("<resource>", "read")`，没有独立的 `route:<page>`。
- 操作他人数据：`action:<resource>:manage_others`

角色编辑器中勾选任意操作会自动补勾同资源的查询权限；后端 `expand_permissions` 也会据此补齐 read，因此「授予了能力即可访问对应页面」。首页是一个特殊的 `action:dashboard:read`，新建角色默认带上它。

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
python -m compileall -q server/app server/tests
python -m pytest
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

## 9. 容器管理开发边界

- 容器管理模块只管理当前部署宿主机 Docker Engine，Docker 连接配置保存在系统设置中，默认自动检测 `DOCKER_HOST`、Linux/macOS socket、Windows named pipe 和本地 TCP，并使用第一个可连接地址；也支持手动填写 Docker Host。
- Linux 容器部署优先挂载 `/var/run/docker.sock`；Windows/macOS Docker Desktop 建议使用 Linux containers 模式，Windows 原生后端开发可手动填写 `npipe:////./pipe/docker_engine`。
- Docker socket 基本等同宿主机 Docker 高权限控制面，容器管理接口必须保持 Web 登录、RBAC 和审计，不要默认给 API Token 或不可信用户开放高危操作。
- 单 Docker daemon 下的用户隔离是平台逻辑隔离：容器使用 `metrix.owner_user_id` labels 过滤，镜像通过平台数据库记录归属和公共/私有状态；不要把它描述成强安全隔离。
- 创建容器默认禁止 `privileged`、宿主网络、Docker socket 挂载和任意宿主目录挂载；如后续要开放，必须先补显式权限、审计和安全提示。

## 10. 脚本管理开发边界

- 脚本以 Docker 容器隔离执行：每个项目一个工作区目录 `runtime/script_workspaces/u<owner>/p<id>/`，bind-mount 到容器 `/workspace`；运行/终端复用容器模块 `clients.create_client()` 解析的 Docker Host，自行 `containers.run(...)`。bind-mount 的是 **Docker daemon 宿主机**路径，后端需与 daemon 同主机（或工作区目录对 daemon 可见）；Windows/macOS Docker Desktop 需该盘已共享。
- 绝不 `pull` 镜像：镜像缺失直接报 `error.scriptImageMissing`，提示去容器管理导入 tar。创建项目时前端只列「本地已存在」的预设镜像与任意本地镜像（也允许手填），运行时再次校验。
- 安全边界沿用容器模块：非 `privileged`、不挂 docker socket、不开 host 网络，只 bind-mount 该项目自己的工作区。网络仅 `none`（断网）/`bridge`（接入网络）；同一 `bridge` 在内网只通内网、迁移到有外网宿主机后自动可访问外网，是「现在离线、将来联网」的统一开关，无需为联网单独写逻辑。
- 包管理兼容离线与迁移联网：系统设置 `script_pip_index_url`/`script_pip_trusted_host`/`script_npm_registry`/`script_go_proxy` 默认全空，运行/终端容器按需注入对应环境变量。留空 + `bridge`：联网走公共源、离线则用 wheel/预装库镜像；配置后走内网源。支持上传 wheel 到工作区 `wheels/`、venv 建在 `/workspace/.venv`。
- 定时调度用 APScheduler（`BackgroundScheduler` + 内存 jobstore，`max_instances=1`），在 `server/app/main.py` 的 `lifespan` 启动/停止，启动时从 `script_schedules` 重新注册 enabled 计划并回写 `next_run_at`；运行执行器并发取系统设置 `script_run_max_workers`，值为 `0` 时不限制平台并发（每次运行独立线程），大于 `0` 时使用固定 `ThreadPoolExecutor`；启动恢复残留运行、周期按 `script_run_retention_hours` 清理，`0` 表示永久保留。`script_workspace_quota_mb=0` 表示不限制工作区大小。`apscheduler` 是该模块唯一新增后端依赖。
- 代码编辑器仅用 Monaco 内置能力（JSON/TS/JS/CSS/HTML 走自带 `?worker`，其余 basic-languages 高亮），**不要引入 `monaco-languageclient` 或外部语言服务器**，也不要修改数据库模块的 `MonacoEditor.vue`；新编辑器在挂载时重写全局 `MonacoEnvironment.getWorker` 以兼容两个编辑器并存。
- 脚本相关接口全部 `require_web_session` 且从 OpenAPI 隐藏（tag `scripts`、path 前缀 `/api/scripts`），v1 不开放 API Token；列表表格不要用 `flex-height`（短视口 tbody 不挂载会空列表）。

## 11. 提交前自查

- 新功能是否放在模块目录内，而不是修改核心注册文件。
- 前后端权限 code、路由、API 路径和语言包是否一致。
- 后端接口是否有真实权限校验。
- 写操作是否记录审计日志。
- 列表是否使用后端分页，数据量变大时不会一次性加载全部。
- 测试、构建和 smoke 是否通过。
