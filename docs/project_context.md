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
