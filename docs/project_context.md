# 项目上下文记录

## 2026-06-02：建立 Metrix 平台总体设计

- 新增 `docs/design/platform_architecture_design.md`，记录 Metrix Web 数据处理平台的总体定位、技术选型、开发规范、代码风格、主仓库结构、submodule 结构、模块职责边界、数据流、调度、脚本、存储、安全、部署和阶段路线。
- 平台设计明确后端使用 Python，前端只做 Web，不引入 Tauri 或桌面壳。
- 模块拆分建议使用独立 Git 仓库并通过主仓库 submodule 组合，核心模块包括 `web-ui`、`core`、`source-remote`、`file-processing`、`database`、`job-runner`、`contracts` 和 `templates`。
- 文件处理模块和数据库模块职责已明确拆分：文件处理模块负责解压、识别、读取、映射、标准化和输出数据批次；数据库模块负责连接、库表、入库、SQL 执行、查询和导出。
- 当前变更只新增设计与项目记忆文档，没有引入代码、依赖、运行配置或业务实现。

## 2026-06-02：初始化 README 与许可证

- 新增 `README.md` 作为项目占位文档，并标注项目使用 PolyForm Noncommercial License 1.0.0。
- 新增 `LICENSE.md`，使用 PolyForm Noncommercial License 1.0.0 官方文本。
- 当前变更仍只涉及文档和许可证，不引入代码、依赖或运行时配置。

## 2026-06-02：调整平台目录与 submodule 命名约定

- 平台设计文档改为以 `web/` 和 `server/` 作为前后端根目录，不再建议使用统一的 `modules/` 目录集中存放 submodule。
- 建议基础目录风格为 `web/src/api`、`web/src/components`、`server/app/api`；前端 submodule 归属 `web/`，后端模块按职责放入 `server/app/` 下。
- Submodule 仓库命名去掉 `metrix-` 前缀，改为 `web-ui`、`core`、`source-remote`、`file-processing`、`database`、`job-runner`、`contracts`、`templates`。
- `.gitignore` 补充 `web/node_modules/` 和 `web/dist/`，匹配新的前端目录风格。

## 2026-06-03：新增登录与 RBAC 框架设计

- 新增 `docs/design/auth_rbac_framework_design.md`，设计第一阶段轻量 Web 登录、Python 后端、SQLite 网站库和 RBAC 权限管理框架。
- 设计明确第一版只做平台框架，不接入文件处理、FTP/SFTP、数据库处理和任务调度等业务模块。
- RBAC 权限拆分为路由权限和功能权限：路由权限控制页面访问，功能权限控制按钮、操作和 API 动作。
- 建议 SQLite 表包括 `users`、`roles`、`permissions`、`user_roles`、`role_permissions` 和 `audit_logs`。
- 当前变更只新增设计文档和项目记忆，不创建前后端代码、不引入依赖。

## 2026-06-03：完善注册审核与权限规则设计

- `docs/design/auth_rbac_framework_design.md` 补充内网账号密码登录策略：修改密码必须校验旧密码，忘记密码由用户联系管理员重置，不做自助找回。
- 注册流程调整为用户提交账号、密码、公司、部门和姓名，默认待审核，必须管理员审核通过后才能登录；这些注册信息同时作为用户资料保存，登录后允许用户自行修改资料。
- 功能权限统一为增、删、改、查、操作五类，对应 `create`、`delete`、`update`、`read`、`operate`。
- 路由权限用于控制导航显示和页面进入；未授权路由不显示且不可进入。授予路由权限时，对应资源的查询权限默认生效，管理员授权界面不需要单独勾选查询权限。

## 2026-06-03：补充内网离线资源规则

- `docs/design/platform_architecture_design.md` 新增平台级离线资源规则，要求 UI 组件、图标、字体、图片、API 文档 UI、脚本和样式都必须本地化或随构建产物打包。
- `docs/design/auth_rbac_framework_design.md` 同步补充登录、注册、权限管理页面的离线资源约束。
- 系统运行期不得为了加载 UI、图标、字体、文档或静态资源访问外网；服务器断开外网后页面和 API 文档仍应可用。

## 2026-06-03：合并初版 Web 与后端详细设计稿

- 新增 `docs/design/initial_web_server_design.md`，汇总并替代原登录与 RBAC 设计文档。
- 新设计稿明确初版需要实现登录、注册、用户管理、注册审批、个人信息管理、退出登录、首页和权限管理。
- 页面框架参考 CapaReport 的 Web 后台工具风格：左侧可折叠菜单、顶部页头、内容区工作卡片、居中登录卡片、蓝色主色和明暗主题。
- 新设计稿保留并整合 SQLite 网站库、RBAC 路由权限与功能权限、注册审核、离线资源、API、数据表、初始化策略和实现顺序。
- 删除 `docs/design/auth_rbac_framework_design.md`，避免两份认证权限设计文档并行造成歧义。

## 2026-06-03：补充初版实现质量约束

- `docs/design/initial_web_server_design.md` 新增实现质量规则，要求代码轻便、简洁、优雅，避免冗余实现和不必要复杂抽象。
- 数据库访问要求通过统一数据访问层和 repository 边界，便于后续在 SQLite 和 MySQL 之间切换。
- 前端规则补充按需导入、路由懒加载、避免大 chunk、CSS 与 Vue 分离、公共样式复用和组件抽离。
- Python 规则补充按资源和职责拆分 API、service、repository、model、schema、core、db，避免单文件过大过长。
- 每个功能完成后需要清理未使用导入、函数、变量、常量、方法、组件、样式、依赖和调试日志。

## 2026-06-03：强化初版代码质量执行规则

- `docs/design/initial_web_server_design.md` 继续强化轻便、简洁、优雅的实现约束，明确遵循 KISS 和 YAGNI，不保留空方法、占位函数、未接入常量或未使用配置。
- 数据库访问层进一步明确 `server/app/db` 作为数据库中间件和适配入口，统一处理 SQLite/MySQL 的连接配置、engine、session 和初始化流程，业务代码只依赖 session、repository 和 service。
- 前端规则进一步明确 CSS 与 Vue 分离，可复用样式放入 `web/src/styles`，组件复用时抽离公共组件或公共样式，禁止整包导入 UI 库、图标库或工具库。
- Python 规则进一步明确文件过长、逻辑过密或职责混杂时按资源、流程或职责拆分，不让单个文件承担多个资源的完整业务流程。
- 收尾检查新增数据库连接细节不得散落到 `db` 层之外，以及公共组件、公共样式和 API 封装不得散落在页面文件中的验收项。

## 2026-06-03：实现初版 Web 与后端框架

- 新增 `server/` FastAPI 后端框架，按 `api`、`core`、`db`、`models`、`repositories`、`schemas`、`services` 分层实现登录、注册、退出、当前用户、首页摘要、用户管理、注册审批、角色权限管理和健康检查。
- 新增首次安装流程：未安装时 Web 自动进入安装页；后端通过 `runtime/install.json` 记录安装配置和系统密钥；SQLite 自动创建 db 文件和库表，MySQL 通过 `pymysql` 支持自动建库和建表。
- 数据库访问通过 `server/app/db/session.py` 懒加载 engine/session，并由 repository/service 处理业务访问，避免 API 层直接操作数据库。
- 密码使用 PBKDF2 哈希保存，Token 使用安装后生成的本地系统密钥签名；不在代码中保存默认管理员账号密码。
- 新增 `web/` Vue 3 + TypeScript + Vite + Naive UI 前端框架，包含安装、登录、注册、首页、用户管理、注册审批、个人信息和权限管理页面；路由按权限守卫，菜单按路由权限过滤。
- 前端公共布局、状态标签、权限按钮和样式已抽离，页面使用懒加载，生产构建已验证 chunk 拆分正常；管理表格在窄屏下使用固定列宽和横向滚动避免文字挤压。
- API 文档页改为使用 `swagger-ui-bundle` 本地静态资源，不依赖 CDN 或外网 favicon。
- 新增后端测试 `server/tests/test_auth_rbac.py`，覆盖 SQLite 安装、MySQL 安装建库建表路径、管理员登录、注册审批、普通用户权限拦截、个人信息修改、旧密码校验、路由授权默认查询权限和 API 文档离线资源。

## 2026-06-03：新增后端直接启动入口

- 新增 `server/main.py` 作为轻量启动入口，进入 `server/` 后可直接执行 `python main.py` 启动 FastAPI 后端。
- 启动入口仍加载 `app.main:app`，不复制 FastAPI 应用创建逻辑，避免形成并行入口。
- `server/main.py` 默认将 `METRIX_RUNTIME_DIR` 指向项目根目录 `runtime/`，避免从 `server/` 启动时把 SQLite 数据库和安装配置写入 `server/runtime/`。
- 启动参数可通过环境变量覆盖：`METRIX_HOST` 控制监听地址，`METRIX_PORT` 控制端口，`METRIX_RELOAD=1` 开启开发热重载。

## 2026-06-03：完善表单校验和接口错误提示

- 新增 `web/src/utils/validation.ts`，统一封装必填、最小长度、最大长度、数字必填和表单校验执行，避免各页面重复写散乱规则。
- 安装、登录、注册、个人信息、修改密码、用户管理、重置密码、注册审批驳回和角色管理表单已补充 `path`、`rules` 和提交前校验；未填或长度不符合要求时在字段下方展示中文提示。
- 注册页确认密码改为表单规则校验，提交接口时只发送后端需要的注册字段，不携带确认密码。
- `web/src/api/client.ts` 已支持 FastAPI/Pydantic 数组型 `detail` 错误，能把后端字段校验错误转换为中文提示，不再统一显示“请求失败”。
- 请求层 JSON 解析增加容错，非 JSON 错误响应不会导致前端抛出解析异常。
