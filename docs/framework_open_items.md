# 框架产品化待处理清单

本文档记录 Metrix 从内部平台开发底座升级为通用后台 Web 框架的产品化事项。当前产品化基础能力已经落地 README、标准 demo-crud 模块、模块化注册增强、开发期数据库同步规则、轻量迁移记录、便携数据迁移工具、submodule 接入规则、基础模块启停、模块生命周期状态、基础模块脚手架和自动化验证。后续只保留更重的生产级迁移框架、完整浏览器回归和真正插件化加载作为按需增强项。

## 当前状态

| 事项 | 状态 | 说明 |
| --- | --- | --- |
| README、快速启动、初始化与部署说明 | 已完成第一版 | 根目录 `README.md` 已覆盖项目定位、技术栈、目录结构、环境要求、启动、初始化、配置、部署、模块开发和测试命令。 |
| 标准示例模块 | 已完成第一版 | 新增 `demo-crud`，覆盖后端 API/model/schema/repository/service/权限/审计/测试，以及前端 API/页面/分页/筛选/权限/i18n/路由/菜单。 |
| 权限、路由、菜单与 i18n 模块化注册 | 已完成第一版 | 前端 `web/src/modules/*/index.ts` 自动发现；后端 `server/app/modules/*` 自动发现 `APP_MODULE`；模块语言包自动合并。 |
| 模块 manifest 增强 | 已完成第一版 | 后端模块声明支持 `version`、`dependencies`、`router_paths`、`model_paths`、`migrations`、`table_syncs`、页面权限、资源权限和 OpenAPI 过滤规则，并增加重复声明校验。 |
| 数据库迁移策略 | 已完成轻量版 | 开发期继续使用自动建表、一次性迁移、字段同步和权限种子同步；迁移和字段同步会写入 `migration_records`；`server/tools/migrate_database.py` 支持 SQLite/MySQL 间通过便携 zip 导出、导入和 copy。 |
| Submodule 与业务模块接入机制 | 已明确第一版规则 | 前端 submodule 放入 `web/src/modules/<module>`，后端 submodule 放入 `server/app/modules/<module>`，模块自带声明、语言包、API、模型和测试。 |
| 模块启用/禁用配置 | 已完成基础版 | 后端支持 `METRIX_ENABLED_MODULES` / `METRIX_DISABLED_MODULES`；前端支持 `app.config.json` 和 `VITE_*` 模块过滤配置；`core` 不可禁用。 |
| 后端自动化测试 | 已增强 | 后端测试覆盖模块注册、demo CRUD、权限扩展、本人/他人数据边界和审计日志。 |
| 前端自动化测试 | 已完成轻量版 | 当前使用类型检查、构建和 smoke 测试守住模块入口、模块 key、版本格式、依赖、菜单分组、页面路径、权限引用和模块语言包结构；后续可按需引入组件测试或浏览器回归。 |
| 模块脚手架 | 已完成基础版 | 新增 `scripts/create-module.mjs`，可生成前后端模块入口、版本/依赖、页面占位、权限、i18n 和 ping 接口骨架；完整 CRUD 仍参考 `demo-crud`。 |
| 模块生命周期 | 已完成轻量版 | 后端模块支持 `lifecycle_hooks`，安装/升级/禁用时可执行小型 SQL 步骤；`module_states` 记录模块版本、依赖和 enabled/disabled/missing 状态。 |

## 已落地内容

### 1. README 与启动部署说明

- `README.md` 已从占位文档改为正式快速启动文档。
- 说明了后端 `python main.py`、前端 `npm run dev`、安装页初始化、SQLite 默认路径、MySQL 可选配置和内网离线资源约束。
- 说明了常用环境变量、部署建议、反向代理边界、备份重点和测试命令。

### 2. 标准 demo-crud 示例模块

后端：

- `server/app/modules/demo_crud/__init__.py`
- `server/app/modules/demo_crud/api.py`
- `server/app/modules/demo_crud/models.py`
- `server/app/modules/demo_crud/schemas.py`
- `server/app/modules/demo_crud/repositories.py`
- `server/app/modules/demo_crud/services.py`

前端：

- `web/src/modules/demo-crud/index.ts`
- `web/src/modules/demo-crud/api.ts`
- `web/src/modules/demo-crud/views/DemoCrudView.vue`
- `web/src/modules/demo-crud/i18n/zh-CN.json`
- `web/src/modules/demo-crud/i18n/en-US.json`

测试：

- `server/tests/test_auth_rbac.py` 中新增 demo CRUD 接口测试，覆盖创建、查询、筛选、更新、删除、审计和本人/他人数据权限。

### 3. 模块化注册增强

- 后端 `AppModule` 支持 `model_paths`，建表前自动导入模块模型。
- 后端 `AppModule` 支持 `version` 和 `dependencies`，注册器会检查模块依赖是否存在。
- 后端 `AppModule` 支持 `migrations`，安装初始化和已安装库同步时会执行未记录过的一次性 SQL 迁移。
- 后端 `AppModule` 支持 `table_syncs`，开发期字段补齐声明从核心同步函数迁移到模块声明。
- 后端 `AppModule` 支持 `lifecycle_hooks`，安装、升级和禁用时可执行显式声明的小型 SQL 步骤。
- 开发期字段同步写入 `migration_records`，用于追踪框架自动补齐过的字段。
- 模块状态写入 `module_states`，用于追踪已发现模块的版本、依赖和 enabled/disabled/missing 状态。
- `server/app/modules/registry.py` 会校验模块 key、依赖、router path、model path、迁移 key、字段同步声明、页面权限 code 和资源权限 code 的重复项。
- 前端模块继续通过 `import.meta.glob` 自动发现页面、菜单和模块语言包，并校验模块依赖、页面路径、菜单分组和权限声明的重复项。
- 模块启停配置会在注册和构建阶段过滤模块；未知模块或禁用 `core` 会直接失败。

### 4. 数据库迁移边界

当前策略：

- 开发期：自动建表、模块一次性迁移、模块字段同步、权限种子同步。
- 一次性迁移和字段同步记录到 `migration_records`，便于排查开发库结构变化，并避免重复执行同一迁移 key。
- 生产期：必须先备份；涉及删字段、改类型、拆表、跨库迁移时不依赖自动同步。
- `server/tools/migrate_database.py` 提供 `export`、`import`、`copy` 三个命令，用便携 zip 在 SQLite/MySQL 间迁移数据；`copy` 保留 `--backup` 文件作为失败回滚依据。
- 暂不引入复杂迁移框架，等生产升级频率和多人协作规模增加后再评估 Alembic 等正式方案。

### 5. Submodule 接入规则

- 前端业务仓库作为 submodule 时，放入 `web/src/modules/<module>`。
- 后端业务仓库作为 submodule 时，放入 `server/app/modules/<module>`。
- 模块必须自带入口声明、语言包、权限声明、API router、模型和测试。
- 主项目不再为了业务模块修改 `router/index.ts`、`AppShell.vue`、`server/app/main.py` 等核心注册文件。

### 6. 基础模块脚手架

- `scripts/create-module.mjs` 可生成一个最小模块骨架：

```powershell
node scripts/create-module.mjs task "任务管理" "Tasks"
```

- 脚手架生成前端模块入口、页面占位、模块语言包、后端模块入口和受权限保护的 ping 接口。
- 脚手架默认声明 `version="0.1.0"` 和依赖 `core`，便于注册器做基础生命周期校验。
- 脚手架只负责减少注册、权限和 i18n 漏项；涉及列表、表单、审计、模型、本人/他人权限和测试时继续参考 `demo-crud`。

## 后续增强项

### 1. 正式迁移体系

当前已有开发期字段同步记录、一次性迁移记录和便携数据迁移工具。后续只有进入更严格生产升级场景时，再补：

- 更细粒度的结构迁移回滚。
- 迁移日志归档和升级审批流程。
- 是否引入 Alembic 等正式迁移框架。

### 2. 前端测试体系

当前已有类型检查、构建和增强 smoke 测试。后续如前端变更频率继续增加，再补：

- 工具函数和 store 单元测试。
- 权限按钮、路由守卫、i18n 合并逻辑测试。
- 关键页面组件测试。
- 最小浏览器回归，覆盖登录、权限菜单、表格分页筛选、表单校验、语言切换和 404。

是否引入 Vitest、Playwright 等测试依赖，等前端测试范围明确后再决定，避免当前阶段过早增加复杂度。

### 3. 模块生命周期进阶

当前已有最小脚手架、模块版本和依赖校验、基础启用/禁用配置、`module_states` 状态记录、轻量生命周期钩子和 `demo-crud` 标准模板。后续模块数量明显增加后，再评估：

- 模块版本兼容范围，例如 `requires >=1.2.0`。
- 模块卸载前的数据归档和权限清理策略。

### 4. 插件化加载

当前不引入复杂插件系统。只有当 submodule 数量、启用配置、依赖隔离和升级流程明显复杂后，再考虑真正插件化。

## 当前建议

短期继续保持轻量：新增业务可以先用 `scripts/create-module.mjs` 生成最小骨架，再参考 `demo-crud` 补齐页面、API、权限、i18n、数据库模型和测试。需要迁移数据时使用 `server/tools/migrate_database.py` 生成便携备份包。只有当模块启停、版本、依赖和升级流程明显复杂时，再考虑真正插件化。
