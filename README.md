# Metrix

Metrix 是一个轻量后台 Web 框架，当前提供登录、注册、RBAC 权限、用户管理、公告、操作日志、系统设置、API Token、API 文档和标准 CRUD 示例模块。项目默认面向内网部署，所有 UI、图标、API 文档资源和运行依赖都需要本地安装或随构建产物提供，不依赖运行时外网资源。

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Naive UI、vue-i18n
- 后端：Python、FastAPI、SQLAlchemy、Pydantic
- 数据库：SQLite 或 MySQL
- 权限：账号密码登录、RBAC 路由权限、功能权限、本人/他人数据范围权限

## 目录结构

```text
web/                         前端应用
  src/modules/               前端业务模块自动发现入口
  src/i18n/locales/          公共语言包
server/                      Python 后端
  app/modules/               后端业务模块自动发现入口
  app/api/                   内置 Web/API 接口
  app/db/                    数据库连接、建表和同步
docs/                        设计、开发指南和项目记忆
runtime/                     本地运行时目录，默认不提交
```

标准示例模块：

- 前端：`web/src/modules/demo-crud`
- 后端：`server/app/modules/demo_crud`
- 测试：`server/tests/test_auth_rbac.py` 中的 demo CRUD 用例

## 环境要求

- Windows 开发环境
- Python 3.11 或兼容版本
- Node.js 20 或兼容版本
- 可选：MySQL 8.x

## 快速启动

后端：

```powershell
cd server
python -m venv ..\.venv
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
python main.py
```

前端：

```powershell
cd web
npm install
npm run dev
```

访问 `http://127.0.0.1:5173/install` 初始化系统。安装页会选择 SQLite 或 MySQL，并创建第一个管理员账号；项目没有硬编码默认管理员账号。

SQLite 路径留空时使用 `runtime/metrix.db`。如果从 `server/` 执行 `python main.py`，启动入口会默认把 `METRIX_RUNTIME_DIR` 指向项目根目录下的 `runtime/`，避免写入 `server/runtime/`。

## 常用配置

| 配置 | 说明 | 默认值 |
| --- | --- | --- |
| `APP_NAME` / `METRIX_APP_NAME` | 应用显示名称 | `app.config.json` 中的 `appName` |
| `APP_SLUG` / `METRIX_APP_SLUG` | 本地存储 key 前缀 | 由应用名称生成 |
| `METRIX_RUNTIME_DIR` | 运行时目录 | `runtime` |
| `METRIX_HOST` | 后端监听地址 | `127.0.0.1` |
| `METRIX_PORT` | 后端监听端口 | `8000` |
| `METRIX_RELOAD` | 是否启用后端热重载 | `0` |
| `METRIX_ENABLED_MODULES` | 后端只启用指定模块，逗号分隔，`core` 自动保留 | 空 |
| `METRIX_DISABLED_MODULES` | 后端禁用指定模块，逗号分隔，不能禁用 `core` | 空 |

前端开发代理只代理 `/api/` 和 `/openapi.json` 到 `http://127.0.0.1:8000`。不要把代理前缀改成宽泛的 `/api`，否则 `/api-docs` 页面刷新会被误转发到后端。

## 初始化与数据库

- 开发期允许后端启动时自动建表、同步字段和同步权限种子。
- 后端模块可在 `APP_MODULE` 中声明 `model_paths`，框架建表前会自动导入模块模型。
- 后端模块可在 `APP_MODULE` 中声明 `table_syncs`，用于开发期轻量字段同步。
- 后端模块可声明 `migrations`，用于执行稳定、一次性的 SQL 迁移步骤；执行记录写入 `migration_records`。
- 生产结构变更可使用显式 schema migration，修订文件位于 `server/app/migrations/versions/`，执行历史同样写入 `migration_records`。
- 后端模块可声明轻量生命周期钩子 `lifecycle_hooks`，用于安装、升级、禁用和卸载时执行小型 SQL 步骤；模块状态记录写入 `module_states`。
- 开发期字段同步也会写入 `migration_records`，用于追踪框架自动补齐过哪些字段。
- 生产部署前必须先备份数据库；结构变更应形成可追踪升级记录，不要直接在生产库手工改表。
- SQLite 与 MySQL 切换使用便携数据包迁移；迁移前先备份，迁移失败时使用保留的 zip 包重新导入回滚。

数据迁移辅助脚本：

```powershell
cd server
..\.venv\Scripts\python.exe tools\migrate_database.py export --url "sqlite:///../runtime/metrix.db" --out "..\runtime\backup.zip"
..\.venv\Scripts\python.exe tools\migrate_database.py import --url "sqlite:///../runtime/metrix-new.db" --in "..\runtime\backup.zip"
..\.venv\Scripts\python.exe tools\migrate_database.py copy --from-url "sqlite:///../runtime/metrix.db" --to-url "sqlite:///../runtime/metrix-new.db" --backup "..\runtime\rollback.zip"
..\.venv\Scripts\python.exe tools\migrate_database.py schema-status --url "sqlite:///../runtime/metrix.db"
..\.venv\Scripts\python.exe tools\migrate_database.py schema-new "add task indexes"
..\.venv\Scripts\python.exe tools\migrate_database.py schema-apply --url "sqlite:///../runtime/metrix.db"
..\.venv\Scripts\python.exe tools\migrate_database.py schema-rollback --url "sqlite:///../runtime/metrix.db"
..\.venv\Scripts\python.exe tools\migrate_database.py module-uninstall --url "sqlite:///../runtime/metrix.db" --module demo_crud --backup "..\runtime\before-demo-uninstall.zip"
```

`copy` 会先导出源库并保留 `--backup` 指定的便携包，再导入目标库；如果目标库迁移失败，保留的 zip 就是回滚依据。MySQL URL 使用 SQLAlchemy 格式，例如 `mysql+pymysql://user:pass@127.0.0.1:3306/metrix?charset=utf8mb4`。

## 部署建议

1. 后端安装 Python 依赖并设置运行时目录。
2. 前端执行 `npm run build` 生成 `web/dist`。
3. 内网 Web 服务器部署 `web/dist` 静态文件。
4. 反向代理 `/api/`、`/openapi.json` 和 `/docs` 到后端服务。
5. 备份 `runtime/` 中的安装配置、SQLite 数据库和日志；MySQL 部署则按数据库规范备份。
6. 确认服务器运行时不需要访问外网资源。

后端可以继续用 `python main.py` 启动，也可以用进程管理器托管 `uvicorn app.main:app`。生产环境不要开启热重载。

## 模块开发

新增业务优先按模块目录开发，不要分散修改框架核心文件。

生成完整 CRUD 模块骨架：

```powershell
node scripts/create-module.mjs task "任务管理" "Tasks"
```

前端模块：

```text
web/src/modules/<module>/
  index.ts
  api.ts
  views/
  i18n/zh-CN.json
  i18n/en-US.json
```

后端模块：

```text
server/app/modules/<module>/
  __init__.py
  api.py
  models.py
  schemas.py
  repositories.py
  services.py
```

模块入口负责声明版本、依赖、页面、菜单、权限、API router、模型、迁移脚本、生命周期钩子和开发期字段同步。依赖可以写 `core`，也可以写 `core>=0.1.0` 这类版本约束。权限 code 统一使用 `route:<page>` 和 `action:<resource>:<action>`。如果涉及本人/他人数据边界，默认只能操作本人数据，需要额外声明 `action:<resource>:manage_others`。

脚手架会生成前端 API/权限/CRUD 页面/i18n、后端 API/model/schema/repository/service/权限/审计和 pytest 模板；复杂业务字段继续在生成骨架上扩展。标准实现参考 `demo-crud`，开发规范见 `docs/development_page_guide.md`。

模块启停保持轻量：后端通过 `METRIX_ENABLED_MODULES` / `METRIX_DISABLED_MODULES` 控制，前端通过 `app.config.json` 的 `enabledModules` / `disabledModules` 或 `VITE_ENABLED_MODULES` / `VITE_DISABLED_MODULES` 控制。前端模块 key 使用短横线，后端模块 key 使用下划线。

后端会把已发现模块的版本、依赖和启用状态写入 `module_states`。禁用模块不会删除历史数据或权限；如果模块需要在禁用或卸载时执行归档/清理动作，应通过 `lifecycle_hooks` 显式声明，并通过 `module-uninstall` 命令执行卸载钩子。

## 测试与构建

后端：

```powershell
cd server
..\.venv\Scripts\python.exe -m compileall -q app tests
..\.venv\Scripts\python.exe -m pytest tests -q --basetemp .pytest-temp
```

前端：

```powershell
cd web
npm run test:smoke
npm run test:regression
npx vue-tsc --noEmit --noUnusedLocals --noUnusedParameters
npm run build
```

如果 Windows 用户临时目录没有访问权限，pytest 使用 `--basetemp .pytest-temp`。

前端 smoke 会校验模块入口、模块 key、版本格式、依赖、菜单分组引用、页面路径、路由权限和模块语言包 key。Playwright 回归会覆盖安装守卫、匿名登录页、登录态恢复、权限菜单和模块页面。新增模块后先跑 smoke 和回归测试，再做类型检查和构建。

## License

PolyForm Noncommercial License 1.0.0

SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
