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

## 2026-06-03：优化初始化页面布局

- `web/src/views/InstallView.vue` 的安装表单改为数据库配置和管理员信息两个区域，管理员账号、密码、姓名、公司、部门从原竖向长表单中独立出来。
- `web/src/styles/main.css` 新增安装页布局样式：桌面宽度使用双栏，MySQL 地址/端口、数据库名/用户名、管理员账号/密码等字段成行排列，减少首屏高度。
- 安装页样式从组件内迁移到全局样式文件，继续保持 Vue 结构和 CSS 分离。
- 浏览器验证 SQLite 和 MySQL 两种状态在约 930px 宽视口下 `scrollHeight` 等于 `innerHeight`，不再需要页面滚动。

## 2026-06-03：替换 Metrix 本地图标

- 新增 `web/public/favicon.svg`，使用渐变大写 M 本地 SVG 作为 Metrix 标识资源，不依赖外网。
- `web/index.html` 增加 SVG favicon 链接，浏览器标签页图标指向 `/favicon.svg`。
- 新增 `web/src/components/BrandMark.vue` 统一渲染品牌图标，登录、注册、初始化页面和主应用侧边栏复用该组件。
- `web/src/styles/main.css` 调整品牌图标尺寸，配合减少透明边距后的 SVG 提升 M 的可视大小；M 使用中等偏粗字重，避免过度加粗。
- 浏览器验证页面图标实际加载 `/favicon.svg`，favicon 链接同样指向该本地 SVG。

## 2026-06-03：调整安装页操作区与数据库连接测试

- 初始化页面的“初始化”按钮移动到管理员信息区域的部门输入框下方，按钮容器保持满宽，按钮独占一行并与输入框同宽，避免切换 SQLite/MySQL 时主操作按钮跟随数据库区域高度跳动。
- 数据库配置区域新增“测试连接”按钮，前端通过 `web/src/api/install.ts` 调用 `/api/install/test-database`。
- 后端新增 `InstallDatabaseTestRequest` 和 `test_database_connection`，测试连接只接收数据库配置，不要求管理员信息。
- SQLite 测试会尝试打开数据库连接；MySQL 测试只连接服务器并执行 `SELECT 1`，不创建数据库，实际初始化时仍由安装流程按需建库。
- 后端测试补充 SQLite 测试接口和 MySQL 测试连接路径，确保 MySQL 测试使用服务器级连接 URL。
## 2026-06-03：修复主框架导航与侧栏
- `web/src/components/AppShell.vue` 改为 Naive UI `n-layout`、`n-layout-sider` 和 `n-menu` 组成的后台壳布局，参考 CapaReport 的单一菜单选中值模式，不再使用 `router-link-active` 判断导航选中。
- 侧栏折叠交给 `n-layout-sider` 原生宽度模式处理，折叠状态写入 `localStorage`，折叠后隐藏品牌文字并保持菜单图标居中。
- 浏览器验证 `/users` 与 `/permissions` 切换时 `.n-menu-item-content--selected` 始终只有 1 个，折叠后侧栏宽度为 64px，当前选中菜单保持正确。
## 2026-06-03：修复主内容区滚动边界
- `web/src/styles/main.css` 将 `html`、`body`、`#app` 固定为 100% 高度，`body` 禁止全局滚动，避免页面内容撑出浏览器级滚动条。
- 主应用壳 `app-layout`、`app-main` 固定在视口内，`app-content` 使用 `height: calc(100vh - 64px)` 和 `overflow: auto` 承担页面内容滚动。
- 登录、注册和安装等独立认证页通过 `.auth-page` 自身滚动，避免全局禁滚后小屏内容被裁切。
- 浏览器验证用户管理、注册审批和权限管理页面的 `body/html` 均不滚动，`.app-content` 保持可滚动容器。
## 2026-06-03：收紧管理弹窗尺寸
- `web/src/styles/main.css` 新增全局 `.modal-card` 规则，统一控制管理弹窗宽度为 `min(460px, calc(100vw - 32px))`，并限制最大高度。
- 弹窗内容区统一设置 `overflow-y: auto`，表单内容较多时在弹窗内部滚动，不撑大页面或弹窗本体。
- 删除用户管理、注册审批和权限管理页面中重复且受 Teleport 影响不稳定的 scoped `.modal-card` 样式，避免多处维护造成尺寸不一致。
- 浏览器验证权限管理角色弹窗和用户管理新增用户弹窗实际宽度均为 460px，内容区保持内部滚动。
## 2026-06-03：优化主框架页头与主题切换
- `web/src/components/AppShell.vue` 去掉页头左侧的收缩按钮和页面副标题，页面顶部只保留主标题、主题切换和用户操作。
- `web/src/stores/app.ts` 将主题状态同步到 `html[data-theme]`，并避免主题切换依赖事件绑定里的 `this`。
- `web/src/styles/main.css` 抽取浅色/深色主题变量，主背景、卡片、边框、文字和菜单选中态都跟随主题变化。
- 折叠侧栏菜单项补充居中样式，确保图标收缩后位于 64px 侧栏中线。
## 2026-06-03：调整暗色主题与滚动条
- 暗色主题变量改回接近 Naive UI 官方暗色风格的中性黑灰背景、半透明边框和绿色主色，不再使用偏蓝的自定义配色。
- 全局补充 `scrollbar-color` 和 WebKit 滚动条样式，明暗主题下滚动条都跟随当前主题变量。
- 浏览器验证暗色模式下 `body`、主布局、侧栏、页头和卡片背景为黑灰体系，选中菜单主色为 `#63e2b7`，页面滚动条颜色随暗色变量生效。
## 2026-06-03：优化登录页布局
- `web/src/views/LoginView.vue` 登录卡片顶部去掉品牌图标和副标题，只保留渐变文字 `Metrix`。
- 登录页新增独立主题切换按钮，未登录状态也可以切换明暗主题。
- 登录表单改为左侧标签的一行式布局，账号和密码标签与输入框在同一行显示。
- `.auth-page` 使用 `100dvh` 居中布局，浏览器验证登录卡片中心点与视口中心一致。
## 2026-06-03：统一表单与页面布局细节
- `web/src/styles/main.css` 新增公共 `.inline-form` 一行式表单规则，字段标签与输入框同排展示，并统一由 CSS 补充冒号，避免页面内重复写样式。
- 安装、注册、用户管理、注册审批驳回、权限管理和个人信息表单统一改为左侧标签布局，保留各页面自身的 `label-width` 以适配字段长度。
- 用户管理筛选条件改为横向网格，关键词、审核状态、启用状态和查询按钮同排展示，窄屏下再降为单列。
- 个人信息页面改为双卡片网格，个人资料和修改密码并排展示，窄屏下自动单列。
- 暗色主题滚动条进一步对齐 Naive UI 官方 common 变量：宽高 5px，暗色 thumb 使用 `rgba(255, 255, 255, 0.20)`，hover 使用 `rgba(255, 255, 255, 0.30)`，并设置 `color-scheme: dark`。
- 暗色认证页移除额外彩色背景层，只保留官方黑灰背景，避免暗色模式出现自定义偏色。
- 注册页卡片改为确定的视口内高度，标题区和底部提交/返回操作区固定显示，中间表单字段区使用内部滚动，窗口高度较小时不滚动整页。
## 2026-06-03：优化权限管理布局与权限粒度规则
- 权限管理页改为左右双栏布局，左侧固定显示角色列表，右侧显示当前角色的权限分配，浏览器宽度不足时自动降为上下布局。
- 角色行增加说明文本截断，避免长角色编码或说明撑乱角色列表。
- 权限粒度继续沿用 `route:*` 和 `action:资源:动作` 两层模型：`route:*` 控制菜单显示和页面进入，`action:*:read/create/update/delete/operate` 控制页面内查询、新增、修改、删除和业务操作。
- 新业务页面新增权限时，需要在后端 `server/app/core/permissions.py` 定义权限常量和种子，接口使用 `require_permission(...)` 做后端强校验，前端按钮和功能入口使用 `authStore.has(...)` 或 `PermissionButton` 做显示控制。
- 授予页面路由权限后，按现有 `ROUTE_READ_PERMISSIONS` 规则默认扩展对应资源的查询权限；新增业务资源也需要同步维护该映射。
- 用户管理补充最后一个启用管理员保护，禁止禁用、删除或移除最后一个管理员角色；删除用户和删除角色操作补充成功/失败提示。
