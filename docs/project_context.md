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
## 2026-06-03：补充数据级权限预留设计
- `docs/design/initial_web_server_design.md` 新增数据级权限预留规则，明确当前不实现数据级权限，只保留后续接入边界。
- 权限模型分为路由权限、功能权限和数据级权限三层；数据级权限用于后续控制全部、公司、部门、本人、指派和自定义业务范围内的数据访问。
- 后续业务接口需要在后端 service/repository 边界保留当前操作人上下文，列表查询在 repository 阶段过滤数据范围，详情和操作接口按资源 ID 再做范围校验。
- 前端按钮先按功能权限控制，未来接入数据级权限时再叠加后端返回的行级能力，如 `can_download`、`can_start`、`can_stop` 或 `allowed_actions`，页面组件不自行硬编码公司、部门、本人等范围规则。
- 任务类页面的操作权限建议拆细为 `action:task:download`、`action:task:start`、`action:task:stop` 等，避免所有业务动作共用一个过大的 `operate` 权限。
## 2026-06-03：修复用户管理筛选工具栏遮挡
- 用户管理页的新增用户按钮新增 `.user-create-button` 独立布局类，避免和筛选区内的查询按钮争抢空间。
- `.user-filter-row` 调整为更稳的响应式列宽，中等宽度以下筛选区独占一行，新增用户按钮换行并靠右显示。
- 浏览器验证当前用户管理页中查询按钮和新增用户按钮不重叠，筛选区与新增按钮之间保留正常间距。
## 2026-06-03：合并注册审批到用户管理
- 注册审批不再作为独立页面、菜单和路由存在，待审核用户统一在用户管理列表中通过审核状态筛选查看。
- 删除前端 `ApprovalView` 和 `approvals` API 封装，用户管理页直接提供待审核用户的通过、驳回操作；已通过用户才显示启用、禁用、角色和密码操作。
- 后端删除 `/api/approvals` 路由，审核接口归并为 `POST /api/users/{id}/approve` 和 `POST /api/users/{id}/reject`，继续使用 `action:user:operate` 做强校验。
- 废弃旧权限 `route:approvals`，种子数据、权限字典和登录权限返回都会过滤该权限，并在初始化/重新种子时清理旧数据库中的残留权限记录。
- `docs/design/initial_web_server_design.md` 已同步为用户管理内处理注册审核的设计口径，避免后续继续按独立审批模块开发。
## 2026-06-03：优化导航与管理页操作布局
- 主框架侧栏展开时品牌区只显示渐变文字 `Metrix`，收缩时才显示本地图标，减少展开状态下的视觉重复。
- 用户管理列表的行操作改为单个下拉按钮，操作项仍按 `action:user:*` 权限和用户审核/启用状态动态生成，表格横向滚动宽度同步收窄。
- 权限管理页角色区域宽度调整为 400px，角色名称和说明有更充足展示空间；角色操作与保存权限按钮改为小号按钮，页面工具栏更紧凑。
## 2026-06-03：细化用户管理行操作按钮
- 用户管理列表的行操作入口改为 28px 纯图标圆形按钮，只保留三点图标和 `title="更多操作"` 提示，避免文字按钮在表格中显得过重。
- 行操作按钮使用轻量 quaternary 样式，hover 时仅用主色浅底提示可点击状态，禁用状态仍由 Naive UI 处理。
## 2026-06-03：居中侧栏品牌标题
- 主框架侧栏品牌区改为横向居中布局，展开状态下渐变 `Metrix` 标题中心与侧栏中心对齐。
- 浏览器验证 `.brand` 与 `.brand-text` 中心偏差为 0，标题不再靠左显示。
## 2026-06-03：添加主框架版权页脚
- 已登录后的主框架 `AppShell` 新增统一底部页脚，显示 `Copyright © 2025 - 2026 NIXEVOL.All Rights Reserved.`。
- 页脚高度为 36px，内容区高度同步扣除 header 和 footer，继续由 `.app-content` 内部滚动，避免出现 body 级滚动条。
- 浏览器验证页脚位于视口底部、文本准确，`body.scrollHeight` 与 `body.clientHeight` 一致。
## 2026-06-03：统一 Web 版权页脚
- 新增 `web/src/components/CopyrightNotice.vue` 作为版权声明组件，统一维护 `Copyright © 2025 - 2026 NIXEVOL.All Rights Reserved.` 文案。
- 主框架 `AppShell`、登录页、注册页和初始化页均复用该组件，避免版权文本分散在多个页面里重复维护。
- 认证页新增公共 `.auth-footer` 样式，注册页高度同步扣除页脚空间，保持标题和底部操作固定、中间表单内部滚动的布局。
- 验证：前端 `npm run build` 通过；浏览器验证 `/login` 和 `/register` 页脚文本准确、可见且无控制台错误。
## 2026-06-03：第一轮代码清理
- `RoleRepository` 的废弃权限过滤抽为统一查询入口，权限字典、按 ID 取权限和权限数量统计都使用同一口径，避免仪表盘把 `route:approvals` 等废弃权限计入数量。
- `get_user_permission_codes` 去掉管理员和普通角色完全相同的重复计算分支，保留管理员在 `has_permission` 中的全权限判断。
- 删除未使用的后端 `UserQuery` schema 及 `schemas.__init__` 导出，避免保留没有调用方的类型。
- 前端路由守卫新增可访问页面 fallback，当前路由无权限时跳转到第一个有权限页面，避免用户没有首页权限时反复跳回 `/`。
- 验证：后端测试 10 passed，前端 `npm run build` 通过，浏览器验证 `/permissions` 标题、菜单和页脚正常且无控制台错误。
## 2026-06-03：第二轮代码清理
- 角色 ID 批量查询从 `UserRepository` 移到 `RoleRepository.by_ids`，用户服务创建用户、审核通过、分配角色和管理员保护逻辑统一走角色仓库，避免用户仓库承担角色聚合职责。
- Pydantic schema 中的列表默认值改为 `Field(default_factory=list)`，包括用户角色列表、创建用户角色 ID 列表和角色权限列表，消除可变默认值隐患。
- 验证：后端测试 10 passed，前端 `npm run build` 通过，浏览器验证 `/users` 行操作按钮和 `/permissions` 角色卡片正常且无控制台错误。
## 2026-06-03：第三轮代码清理
- 新增 `web/src/utils/message.ts`，统一封装页面请求失败提示，页面 catch 中不再重复书写 `message.error((error as Error).message)`。
- `showError` 接收 `unknown` 错误并对非 `Error` 值给出默认提示，避免异常对象类型不稳定时页面再次抛错。
- 验证：后端测试 10 passed，前端 `npm run build` 通过，浏览器验证 `/users` 和 `/login` 正常且无控制台错误。
## 2026-06-03：第四轮代码清理
- `UserService` 新增 `_roles_or_default`，创建用户和审核通过用户复用同一套默认普通角色选择逻辑，保留用户分配角色时允许空角色列表的原有语义。
- `server/app/db/session.py` 不再通过 SQLAlchemy `sessionmaker.kw["bind"]` 内部属性判断绑定引擎，改为显式记录当前 session 工厂对应的 engine，提高后续 SQLAlchemy 版本兼容性。
- 清理本地生成的 `__pycache__` 缓存目录，保持工作区只保留真实源码和必要配置。
- 验证：后端测试 10 passed，前端 `npm run build` 通过，浏览器验证 `/users` 和 `/permissions` 正常且无控制台错误。
## 2026-06-03：第五轮代码清理
- 用户管理页不再无条件调用角色权限管理接口加载完整角色列表；只有具备 `action:user:create` 或 `action:user:operate` 时才加载用户管理所需的角色候选。
- 后端新增 `require_any_permission` 依赖工具和 `GET /api/users/role-options`，仅返回 `RoleBrief` 基础角色信息，避免为了用户新增、审核或分配角色暴露完整权限字典。
- 后端测试补充验证：拥有用户操作权限的角色可以访问 `/api/users/role-options`，但不能访问 `/api/permissions`。
- 验证：后端测试 10 passed，前端 `npm run build` 通过，浏览器验证 `/users` 和 `/permissions` 正常且无控制台错误。
## 2026-06-03：第六轮代码清理
- `UserRepository.count_admins` 不再硬编码 `"admin"`，改为复用 `app.core.permissions.ADMIN_ROLE`，保持管理员角色编码统一由权限常量维护。
- 本轮重新扫描前后端旧模式、未使用残留和调试代码，未发现新的可确认冗余或死代码。
- 验证：后端测试 10 passed，前端 `npm run build` 通过，浏览器验证 `/users` 和 `/permissions` 正常且无控制台错误。
## 2026-06-03：第七轮代码清理
- 后端 CORS 开发来源补充 `http://localhost:5174` 和 `http://127.0.0.1:5174`，匹配当前前端开发服务端口，避免 5174 端口直接访问后端 API 时被跨域策略拦截。
- 本轮重新扫描前后端旧模式、未使用残留、调试代码和开发端口配置，未发现新的可确认冗余或死代码。
- 验证：后端测试 10 passed，前端 `npm run build` 通过，浏览器验证 `/users` 和 `/permissions` 正常且无控制台错误。
## 2026-06-04：首页粒子视觉改造
- 首页移除用户数、待审批、角色数、权限数、当前用户和可访问页面等信息面板，改为纯视觉入口。
- `web/src/views/DashboardView.vue` 使用本地 Canvas 粒子动画，粒子从随机位置聚合成 `Metrix` 字样，短暂停留后收缩淡出，最终显示动态渐变 `Metrix` 标签；不引入外部资源或新增依赖。
- 清理前端未使用的首页摘要 API 封装 `web/src/api/system.ts`、`DashboardSummary` 类型和旧统计卡片样式；后端 `/api/dashboard/summary` 暂保留，避免扩大对外 API 契约变更。
- 验证：前端 `npm run build` 通过，后端测试 10 passed；浏览器验证首页动画结束后 Canvas 隐藏、渐变 `Metrix` 标签可见、页面不溢出且无控制台错误。
## 2026-06-04：集中应用名称配置
- 新增根目录 `app.config.json` 作为应用默认名称配置入口，默认只需要修改 `appName`；技术前缀、localStorage key、默认 MySQL 数据库名和默认 SQLite 文件名由应用名派生，确需自定义时可补充 `appSlug`。
- 前端通过 `web/vite.config.ts` 将配置注入为 `__APP_CONFIG__`，`web/src/config/app.ts` 统一导出 `APP_NAME`、`APP_SLUG`、`DEFAULT_DATABASE_NAME`、`DEFAULT_SQLITE_PATH` 和 `appKey`；侧栏品牌、登录页标题、首页粒子文字、浏览器标题、安装页默认数据库名和本地存储 key 均改为使用该配置。
- 后端 `server/app/core/config.py` 读取同一份 `app.config.json`，并保留 `APP_NAME`、`APP_SLUG`、`METRIX_APP_NAME`、`METRIX_APP_SLUG` 环境变量覆盖；默认 SQLite 文件名和安装前临时 token 签名 key 改为从 `settings.app_slug` 派生。
- 后端测试新增配置读取与环境变量覆盖验证；验证：前端 `npm run build` 通过，后端测试 11 passed；浏览器验证页面标题、侧栏品牌和首页最终标签均读取到配置中的默认应用名且无控制台错误。
## 2026-06-04：首页粒子自适应与重绘规则
- 首页粒子动画起始阶段改为先从中心轻微聚集状态按当前内容区尺寸扩散，再聚合为应用名称，聚合文字尺寸按容器宽高和设备像素比计算，避免高分屏或大窗口下字样偏小。
- 粒子动画不再监听窗口尺寸变化，只有进入首页并挂载组件时重新绘制；窗口大小变化后仅最终渐变标签通过 CSS `clamp()` 自动适应大小，避免 resize 时动画反复重跑。
- 最终渐变标签字号调整为 `clamp(76px, 14vw, 142px)`，并限制最大宽度与自动换行，保证小窗口不溢出。
- 验证：前端 `npm run build` 通过，后端测试 11 passed；浏览器验证首页动画结束后最终标签为配置应用名、Canvas 隐藏、页面不溢出且无控制台错误。
## 2026-06-04：调整个人信息入口
- 主框架侧边栏不再显示个人信息入口，侧边栏只保留首页、用户管理和权限管理等主功能导航。
- `/profile` 路由仍作为所有登录用户可访问的基础页面保留，并继续通过右上角用户下拉菜单进入。
- `AppShell` 将侧边栏菜单项和页面标题映射拆开，个人信息页进入后顶部标题仍显示“个人信息”，侧边栏不误选中首页或其他主菜单。
- 右上角用户下拉菜单明确使用点击触发，贴合个人信息从用户菜单进入的交互预期。
- 验证：前端 `npm run build` 通过，后端测试 11 passed；浏览器验证侧边栏无“个人信息”、右上角点击菜单可进入 `/profile`、页面标题正确且无控制台错误。
## 2026-06-04：侧边栏支持多级权限菜单
- 主框架侧边栏菜单改为树形配置，用户管理和权限管理收纳到无跳转父级“系统管理”下，作为管理员功能二级菜单展示。
- 菜单过滤改为递归处理权限和子菜单：无跳转父级只在过滤后仍存在可见子菜单时显示，子菜单为空时自动隐藏，不占侧边栏位置。
- 有路由的菜单即使未来带子菜单，也不会因为子菜单被权限过滤为空而误隐藏；父级菜单点击不跳转，只有 `path` 以 `/` 开头的叶子菜单会触发路由跳转。
- 侧边栏展开状态改为受控 `expandedKeys`，直接进入 `/users` 或 `/permissions` 时会自动展开“系统管理”并选中当前子菜单，同时会清理权限过滤后失效的展开键。
- 验证：前端 `npm run build` 通过，后端测试 11 passed；浏览器验证 `/users` 与 `/permissions` 直达时系统管理自动展开、对应子菜单选中、父级点击不跳转且无控制台错误。
## 2026-06-04：集中页面注册和权限模板
- 新增 `web/src/router/page-registry.ts` 作为主框架页面注册入口，统一维护页面路径、标题、懒加载组件、路由权限、菜单分组、菜单图标、排序和无权限 fallback 顺序。
- `web/src/router/index.ts` 改为从页面注册表生成主框架子路由，`AppShell` 改为从同一注册表生成侧边栏菜单、页面标题和父级展开状态，避免新增页面时同时维护路由、导航和标题映射。
- 后端 `server/app/core/permissions.py` 增加 `route_code`、`action_code`、页面权限规格和资源功能权限规格，`PERMISSION_SEEDS` 与 `ROUTE_READ_PERMISSIONS` 由规格自动派生。
- 新增 `docs/development_page_guide.md`，记录新增页面、路由、菜单和权限的最短开发路径，并明确页面内按钮继续复用 `PermissionButton`，为后续数据级权限只预留接入边界、不提前实现。
- 验证：前端 `npm run build` 通过，后端测试 12 passed；浏览器验证 `/permissions` 与 `/users` 均能自动展开“系统管理”并选中当前子菜单，控制台无错误。
## 2026-06-04：新增公告功能和开发库自动同步
- 后端新增公告模型、公告已读模型、公告 API、repository 和 service，支持全平台公告、按权限/公司/公司-部门或职位/指定账号定向公告，以及弹窗、滚动条、首页侧栏三种展示方式。
- 新增公告权限 `route:announcements` 与 `action:announcement:create/read/update/delete/operate`，公告管理页通过页面注册表收纳到“系统管理”下，授权路由后默认获得公告查询权限。
- `server/app/db/session.py` 在已安装库创建 engine 后调用开发期同步入口，自动补齐新增表结构和权限种子，并把新增权限同步给内置管理员角色，方便当前开发 runtime 直接继续使用。
- 前端新增公告管理页、公告 API、公告 store 和 `AnnouncementTicker` 组件；登录页展示全平台公开滚动公告，登录后主框架展示未读滚动公告和一次性弹窗，首页右侧用时间轴展示公告列表与未读计数。
- 公告点击弹窗确认、关闭滚动条或点击首页时间轴项都会标记当前用户已读；已读后弹窗不再出现、滚动条消失、首页时间轴状态和未读计数同步更新。
- 公告目标区分“全平台”和“全部用户”：全平台公告可通过公开接口出现在登录页，全部用户公告必须登录后才会出现在主框架公告展示中。
- 公告新增表单默认只勾选“首页侧栏”，展示方式三项全不选时前后端都拒绝保存；“全部用户 + 首页侧栏”已通过接口验证可保存，测试公告随后删除。
- 验证：后端测试 14 passed，前端 `npm run build` 通过；浏览器验证公告管理页可打开、默认勾选状态正确且无控制台错误。
## 2026-06-04：修复用户资料类型标注和菜单层级
- `server/app/api/auth.py` 在登录、当前用户和个人信息更新响应中显式使用 `UserProfile.model_validate(...)`，避免类型检查器把 SQLAlchemy `User` 误判为不能传入 `UserProfile`。
- `server/app/models/role.py` 与 `server/app/models/user.py` 使用 `TYPE_CHECKING` 补齐关系字段的类型引用，保持运行时仍通过字符串关系名避免循环导入。
- 侧边栏二级菜单恢复树状层级感：子菜单项相对一级菜单右移，并在展开区域显示轻量层级线；收缩状态下继续保持图标居中。
- 验证：后端测试 14 passed，前端 `npm run build` 通过；浏览器验证 `/permissions` 下系统管理二级菜单缩进生效且无控制台错误。
## 2026-06-04：统一列表内部滚动规则
- 用户管理和公告管理页面改用 `work-card table-page-card` 与 `n-data-table flex-height`，让滚动只发生在表格 body 内，筛选区、操作区和字段表头保持固定。
- 权限管理页面的角色列表和权限分组改用 `work-card list-page-card` 内部滚动，左右卡片工具栏不再被列表内容顶走。
- `docs/development_page_guide.md` 新增列表滚动开发规则：后台列表页必须固定页面标题、筛选区、操作区和表头，新增表格页统一使用 `page-data-table`，非表格列表把滚动限制在数据容器内部。
- 验证：后端测试 14 passed，前端 `npm run build` 通过；HTTP 验证前后端服务可访问，当前 Browser 插件缓存缺少连接脚本，页面自动化验证受限。
## 2026-06-04：第一轮全量代码清理
- `UserService.assign_roles` 复用同一次 `RoleRepository.by_ids` 查询结果，最后管理员保护和本人管理员角色保护不再重复查询同一批角色。
- `RoleService.list_permissions` 补齐 `list[Permission]` 返回类型，保持 service 类型边界清晰。
- `seed_database` 去掉未使用的 `permissions_by_code` 局部变量，只保留初始化管理员所需的内置管理员角色。
- 清理验证生成的 `web/dist`、`server/.pytest_cache` 和源码目录 `__pycache__`，保留工作区只包含真实源码与必要配置。
- 验证：前端 `npm run build` 通过，后端测试 14 passed；`git diff --check` 通过；调试残留扫描无命中。
## 2026-06-04：第二轮全量代码清理
- `server/app/services/install.py` 删除未使用的 `Session` 导入，安装服务只保留实际使用的 `sessionmaker`。
- `server/app/api/__init__.py` 同步导出公告 API 模块，避免包级 API 聚合入口落后于当前功能模块。
- `server/app/schemas/__init__.py` 同步导出公告相关 schema，保持 schema 聚合入口与当前公告功能一致。
- 第二轮重新扫描前后端调试残留、废弃权限清理逻辑、列表滚动规则、包级导出、入口页、主框架和公告模块；`deprecated` 命中均为旧权限迁移清理逻辑，公告 ticker 的 `setInterval` 为轮播必需逻辑，未作为冗余删除。
- 验证：前端 `npm run build` 通过，后端测试 14 passed；`git diff --check` 通过；调试残留扫描无命中。
## 2026-06-04：最终全量复查
- 最终轮重新从源码清单、`.gitignore`、页面开发指南、前后端调试残留、TypeScript 未使用项、Python 编译、前端构建和后端测试完整复查，未发现新的可确认冗余代码、死代码或兼容性问题。
- `.gitignore` 已覆盖 `web/dist/`、`runtime/`、`.pytest_cache/`、`__pycache__/`、本地缓存、日志、上传下载导出目录和敏感本地配置。
- 清理最终验证生成的 `web/dist`、`server/.pytest_cache` 和源码目录 `__pycache__`，工作区不保留可再生产物。
- 验证：前端 `npm run build` 通过，`npm exec vue-tsc -- --noEmit --noUnusedLocals --noUnusedParameters` 通过；后端测试 14 passed，`python -m compileall -q app tests` 通过；`git diff --check` 通过；调试残留扫描无命中。
## 2026-06-05：完善登录失效、404 和忘记密码提示
- 前端请求层在收到 401 响应时清理登录态并触发应用级登录失效事件，路由层监听后统一跳转 `/login`，避免 token 失效后页面停留在受保护视图。
- 新增 `NotFoundView` 作为 404 兜底页面，未知路由进入无卡片居中 404 视觉，并在 5 秒倒计时后自动返回主页；主页后续仍由现有权限守卫决定实际可访问页面。
- 登录页将“忘记密码请联系管理员”改为“忘记密码”文字按钮，点击后弹窗提示“请联系管理员修改密码。”。
- 验证：前端 `npm run build` 通过，`npm exec vue-tsc -- --noEmit --noUnusedLocals --noUnusedParameters` 通过；后端测试 14 passed；`git diff --check` 通过；调试残留扫描无命中。
## 2026-06-05：调整主框架内容贴边布局
- 主框架 `.app-content` 去掉桌面和移动端内边距，让页面最外层工作区边框贴合侧边栏右边、顶部标题栏底边和底部页脚边界。
- `.work-card` 外层圆角改为 0，避免贴边布局下角落产生突兀留白；页面内部仍保留原有 18px 内容内边距。
- 当前改动只涉及 Web 全局样式，不使用浏览器自动化验证，由用户自行在浏览器确认实际视觉效果。
- 验证：前端 `npm run build` 通过，`npm exec vue-tsc -- --noEmit --noUnusedLocals --noUnusedParameters` 通过；`git diff --check` 通过；调试残留扫描无命中。
## 2026-06-05：固化主框架贴边布局规则
- `docs/development_page_guide.md` 新增主框架布局规则：后台主框架页面默认使用贴边工作区，最外层工作区边框必须贴合侧边栏右边、顶部标题栏底边和底部页脚边界。
- 后续新增页面优先复用 `.work-card`、`.table-page-card`、`.list-page-card` 等全局样式，不在页面组件中重新添加外层圆角、阴影、外边距或浮动卡片效果。
- 只有用户明确要求浮动布局、留白布局或特殊展示页时，才允许偏离贴边工作区规则，并需要记录原因。
## 2026-06-05：完善公告管理筛选和列表字段
- 公告管理页去掉页内重复标题，只保留主框架顶部标题；页内工具栏改为筛选区加新增按钮，支持按标题/内容、推送范围、展示方式、启用状态和创建时间范围筛选。
- 后端公告列表接口支持对应 query 参数过滤，并在管理列表、创建和更新响应中返回 `created_by_username`，前端表格显示为“操作账号”，用于追踪公告发布账号。
- 用户管理表格新增“注册时间”列，继续使用 `page-data-table` 内部滚动规则，避免列表数据滚动顶走筛选区和表头。
- 验证：前端 `npm exec vue-tsc -- --noEmit --noUnusedLocals --noUnusedParameters` 通过，前端 `npm run build` 通过，后端测试 14 passed，`git diff --check` 通过，调试残留扫描无命中。
## 2026-06-05：统一 Naive UI 中文语言包
- `web/src/App.vue` 的 `NConfigProvider` 增加 `zhCN` 和 `dateZhCN`，让日期选择器、确认按钮、清空按钮、月份/星期等 Naive UI 内置文案统一显示中文。
- 该配置放在全局入口，后续新增 Naive UI 组件默认继承中文语言环境，不需要在单个页面重复配置。
- 验证：前端 `npm exec vue-tsc -- --noEmit --noUnusedLocals --noUnusedParameters` 通过，前端 `npm run build` 通过，`git diff --check` 通过，调试残留扫描无命中。
## 2026-06-05：完善公告批量删除和表头筛选
- 公告管理新增勾选批量删除能力：前端表格按删除权限显示选择列和批量删除按钮，后端新增 `/api/announcements/batch-delete`，批量删除会逐条记录审计并一次提交事务。
- 公告管理顶部筛选栏只保留关键字、创建时间范围和查询按钮；推送范围、展示方式、状态迁移到表格字段表头筛选，筛选状态继续映射到后端列表接口参数。
- `.announcement-toolbar` 改为可换行布局，公告操作按钮独立放在右侧操作区，窄屏下自然换行，避免和日期范围、查询按钮重叠。
- `docs/development_page_guide.md` 新增表格筛选规则：枚举字段优先用表头筛选，顶部工具栏避免堆积下拉条件；批量操作放操作区并允许窄屏换行。
- 验证：前端 `npm exec vue-tsc -- --noEmit --noUnusedLocals --noUnusedParameters` 通过，前端 `npm run build` 通过，后端测试 14 passed，`git diff --check` 通过，调试残留扫描无命中。
## 2026-06-05：支持列表后端分页和公告排序筛选
- 用户管理和公告管理列表改为后端分页响应，统一返回 `items`、`total`、`page`、`page_size`；前端 `n-data-table` 使用 `remote` 分页，分页大小固定为 `20 / 50 / 100 / 500`，后端 `page_size` 上限同步为 500。
- 公告管理新增“操作账号”表头筛选，支持查看全部发布人或仅查看当前登录账号发布的公告；“创建时间”列支持正序/倒序远程排序。
- 用户管理保留关键字和注册时间范围查询，审核状态与启用状态使用表头筛选，注册时间支持远程正序/倒序排序；分页后移除基于当前页数据的最后管理员前端判断，最后管理员保护继续由后端强校验负责。
- 用户信息扩展手机号和邮箱字段，安装管理员、注册、个人资料、用户新增/编辑均使用同一套前后端格式校验；开发库同步会自动补齐 `users.phone` 和 `users.email` 列。
- `docs/development_page_guide.md` 新增表格分页规则：数据量可能增长的后台列表必须走后端分页，分页、表头筛选和排序统一映射接口参数。
- 验证：前端 `npm exec vue-tsc -- --noEmit --noUnusedLocals --noUnusedParameters` 通过，前端 `npm run build` 通过，后端测试 16 passed，`git diff --check` 通过，调试残留扫描无命中。
## 2026-06-05：补充用户列表查询测试
- 后端用户列表测试补充注册时间正序/倒序排序和时间范围筛选断言，覆盖用户管理表格远程排序、远程时间筛选的接口契约。
## 2026-06-05：补充本人和他人数据操作权限规则
- 权限模型明确拆分为基础动作权限和范围提升权限：`create/read/update/delete/operate` 只表达能否执行动作，不直接代表可以操作他人数据。
- 未授予范围提升权限时，`update`、`delete`、`operate` 默认只允许操作当前用户本人创建、上传、负责或归属的数据；操作他人数据需要额外拥有 `action:<resource>:manage_others`。
- 公告后续可使用 `action:announcement:manage_others` 控制是否允许编辑、删除、发布或停用他人公告；数据、任务、文件、脚本等页面也遵循同一规则。
- 新增业务表默认保留创建人或归属人字段，如 `created_by`、`owner_user_id`；上传、导入、手工新增和脚本生成的数据都要记录操作账号，便于审计和后续本人/他人权限划分。
- 前端行操作按钮仍先按基础功能权限控制，再叠加后端返回的行级能力字段；页面组件不自行硬编码账号、公司、部门或本人范围判断。
## 2026-06-05：实现公告他人操作权限
- 公告权限移除冗余的 `action:announcement:operate`，该权限没有独立接口使用，已加入废弃权限清理列表，开发库同步会从权限字典和角色关联中移除。
- 新增并实现 `action:announcement:manage_others`，用于在已有公告修改或删除权限的前提下控制是否允许编辑、删除、发布、停用他人创建的公告。
- 公告编辑、单条删除和批量删除在后端服务层统一校验数据归属：未拥有 `manage_others` 时只能操作本人创建的公告，操作他人公告返回“无权限操作他人公告”。
- 公告管理前端行按钮和批量勾选同步叠加本人/他人判断；权限管理页改为显示所有非查询动作权限，确保 `manage_others`、下载、启停等细粒度动作后续都能授权。
## 2026-06-05：实现前端中英双语切换
- 前端新增 i18n 层 `web/src/i18n`，包含语言包、翻译函数、日期格式化、Naive UI 语言映射和内置角色/权限显示映射；当前支持 `zh-CN` 与 `en-US`，默认中文。
- `appStore` 新增 `locale` 状态并持久化到 localStorage，同时同步 `document.documentElement.lang`；`App.vue` 根据当前语言切换 Naive UI 的 `locale` 和 `dateLocale`。
- 新增 `LanguageSwitcher` 组件，登录、注册、初始化和主框架页头均可切换语言；主框架页面注册从硬编码标题改为 `titleKey/labelKey`，菜单和页面标题自动按当前语言渲染。
- 登录、注册、安装、首页、404、个人信息、用户管理、权限管理、公告管理、公告滚动条、状态标签、校验规则和请求层校验错误已接入 `t(...)`；日期展示统一使用 `formatDateTime`。
- `docs/development_page_guide.md` 新增多语言开发规则：新增页面文案必须维护语言包，页面注册使用 `titleKey`，表单规则用 `computed` 响应语言切换，内置权限显示通过 `i18n/builtins.ts` 维护。
- 验证：前端 `npm exec vue-tsc -- --noEmit --noUnusedLocals --noUnusedParameters` 通过，前端 `npm run build` 通过，后端 `E:\code\Metrix\.venv\Scripts\python.exe -m pytest` 通过 17 passed；页面源码中文扫描仅剩语言包和后端内置权限分组映射。
## 2026-06-05：完善前后端国际化消息协议
- 前端正式引入本地依赖 `vue-i18n`，`web/src/i18n/index.ts` 保留项目级 `t(...)`、`formatDateTime(...)`、`translateMessage(...)` 封装，页面开发不直接依赖库细节。
- 后端 `MessageResponse` 统一为 `code`、`message`、`params`，其中 `code` 是稳定资源 ID，`message` 只作为英文 fallback，`params` 用于 `{name}`、`{count}` 等变量插值。
- 后端异常 helper 统一返回结构化 `detail` 对象，业务错误、鉴权错误、未初始化错误和公告本人/他人权限错误都不再返回中文展示文案。
- Pydantic 自定义校验改为稳定 `validation.*` 类型，前端请求层优先按 `code/type` 翻译，找不到翻译时才使用后端英文 fallback。
- 页面成功提示可使用接口返回的 `ServerMessage` 通过 `messageText(...)` 翻译，批量删除公告等带变量的消息不再由后端拼接最终展示文案。
- 开发期不为旧接口响应添加兼容层；用户管理、公告管理继续按最新分页对象 `items`、`total`、`page`、`page_size` 读取数据，旧数据通过同步迁移或直接调整适配最新结构。
- 权限管理前端增加废弃权限过滤，避免开发库残留的 `route:approvals` 或 `action:announcement:operate` 再次出现在授权界面或保存请求中。
- `docs/development_page_guide.md` 更新多语言规则，明确后端禁止返回中文业务 `detail/message`，新增文案必须维护语言包并使用前端插值。
- 验证：前端 `npm exec vue-tsc -- --noEmit` 通过，前端 `npm run build` 通过，后端 `E:\code\Metrix\.venv\Scripts\python.exe -m pytest` 通过 17 passed。
## 2026-06-05：修复表格操作列横向滚动
- 用户管理和公告管理表格不再手写固定 `scroll-x` 数值，改为按列宽常量求和，避免列增多后横向滚动范围不足。
- 用户管理和公告管理的操作列设置为右侧固定列，用户无需拖动到底也可以打开行操作或执行编辑、删除。
- 公告管理在有选择列时会把选择列宽度计入 `scroll-x`，保证选择列、数据列和固定操作列宽度一致。
- `docs/development_page_guide.md` 新增表格横向滚动规则：列宽集中维护、`scroll-x` 使用列宽总和、操作列优先固定到右侧，新增列后必须同步宽度常量。
## 2026-06-06：新增操作日志页面和日志范围权限
- 后端新增 `/api/audit-logs` 查询接口，复用现有 `audit_logs` 表，支持关键字、操作类型、目标类型、操作账号范围、创建时间范围、创建时间排序和后端分页，响应继续使用 `items`、`total`、`page`、`page_size`。
- 新增权限 `route:audit_logs`、`action:audit_log:read` 和 `action:audit_log:manage_others`；授予日志路由权限后默认扩展日志查询权限，未授予 `manage_others` 时后端强制只能查看本人日志。
- 前端新增 `AuditLogView` 并通过 `page-registry.ts` 收纳到“系统管理”二级菜单；页面使用 `work-card table-page-card`、`page-data-table`、后端分页、顶部关键字/时间范围和表头筛选。
- 多语言补充操作日志菜单、字段、权限、常见审计动作和目标类型的中英文文案；权限管理内置权限映射同步支持操作日志分组。
- `docs/development_page_guide.md` 新增操作日志开发规则：关键写操作继续通过 `record_audit(...)` 记录，日志查看所有账号必须走 `action:audit_log:manage_others` 范围提升权限。
## 2026-06-06：支持操作日志 CSV 下载
- 后端新增 `GET /api/audit-logs/export`，返回 `text/csv` 附件 `audit-logs.csv`，CSV 使用 UTF-8 BOM 方便表格软件直接识别中文内容。
- CSV 导出复用操作日志列表的关键字、操作类型、目标类型、账号范围、创建时间范围和排序条件，但不受当前页分页限制，导出当前筛选条件下的完整结果。
- 导出接口继续复用日志范围权限：只有 `action:audit_log:read` 时只能导出本人日志，带 `actor_scope=all` 时必须拥有 `action:audit_log:manage_others`。
- 前端操作日志页新增“下载 CSV”按钮，下载时携带当前筛选条件；请求层新增通用 `download(...)` 方法，保持 401 登录失效处理与普通 JSON 请求一致。
- 验证：后端 `E:\code\Metrix\.venv\Scripts\python.exe -m pytest server\tests\test_auth_rbac.py -q` 通过 18 passed；前端 `npm run build` 通过；`git diff --check` 通过。
## 2026-06-06：新增系统设置页面
- 后端新增 `system_settings` 表、设置 repository/service/schema/API，提供公开设置、管理员读取保存设置和一键备份接口；新增权限 `route:settings`、`action:setting:read/update/operate`，授予系统设置路由后默认扩展查询权限。
- 系统设置支持运行时平台名称、是否开放注册、注册时手机号码/邮箱/公司/部门或职位是否必填、日志保留时长、默认语言和数据备份；公开设置会在登录、注册和路由守卫加载，用于控制注册入口、默认语言和运行时平台名展示。
- 注册后端强制读取系统设置：关闭注册时拒绝注册；注册必填资料由系统设置逐项控制，手机号码和邮箱在非必填时允许为空但填写后仍校验格式。
- 日志保留改为后台维护任务，不在每次写操作日志时清理；FastAPI lifespan 启动 24 小时循环任务，清理时按每个账号自己的最后一条日志时间向前保留配置天数，避免按系统当前时间删除日志。
- 数据备份接口 `POST /api/settings/backup` 返回 ZIP，包含 `metadata.json` 和现有核心表 JSON 数据：用户、角色、权限、审计日志、公告、公告已读和系统配置，便于后续服务器迁移时使用。
- 前端新增 `SystemSettingsView` 并接入“系统管理”菜单，页面复用贴边工作区和 i18n 文案；备份按钮会下载 `metrix-backup-YYYY-MM-DD.zip`，登录页在关闭注册时隐藏注册入口。
- 验证：后端 `E:\code\Metrix\.venv\Scripts\python.exe -m pytest server\tests\test_auth_rbac.py -q` 通过 19 passed；前端 `npx vue-tsc --noEmit --noUnusedLocals --noUnusedParameters` 通过；前端 `npm run build` 通过；`git diff --check` 通过；调试残留扫描无命中。
## 2026-06-07：修复前端白屏
- 白屏根因是 `web/src/i18n/index.ts` 顶层导入 `appStore`，而 `appStore -> settingsStore -> api/client -> i18n` 形成循环初始化，浏览器报 `Cannot access 'appStore' before initialization`。
- i18n 初始化改为只读取本地语言 key 和语言包，不再顶层依赖 `appStore`；`appStore.setLocale(...)` 主动调用 `setI18nLocale(...)` 同步 vue-i18n、localStorage 和 `document.documentElement.lang`。
- 路由守卫对 `/api/install/status` 增加兜底：安装状态接口暂时失败时不再中断首屏导航，公开页仍可显示，受保护页继续按登录态回到登录页，避免接口异常导致空白页面。
- 验证：默认 5173/8000 端口下用 Browser 打开 `http://127.0.0.1:5173/`，页面跳转到 `/login` 且 `#app` 正常渲染；前端 `npx vue-tsc --noEmit --noUnusedLocals --noUnusedParameters` 通过，前端 `npm run build` 通过，后端 `E:\code\Metrix\.venv\Scripts\python.exe -m pytest server\tests\test_auth_rbac.py -q` 通过 19 passed。
## 2026-06-07：第一轮全量代码清理
- 前端请求层新增 `queryString(...)` 小工具，用户列表、公告列表和操作日志列表/导出统一复用查询参数拼接逻辑，避免各 API 文件重复维护过滤空值和分页排除逻辑。
- 操作日志 CSV 导出不再用 `void page`、`void page_size` 占位丢弃分页字段，改为通过 `queryString(filters, ["page", "page_size"])` 显式排除分页参数。
- 后端系统设置服务删除 `_days_delta(...)` 一行包装，日志裁剪阈值直接使用 `timedelta(days=days)`；`server/app/db/init.py` 合并 SQLAlchemy ORM 导入。
- 清理验证生成的 `web/dist`、`.pytest_cache`、`server/.pytest_cache` 和源码目录 `__pycache__`；`.gitignore` 已覆盖前端构建产物、运行时数据、缓存、日志、临时目录和本地敏感配置。
- 验证：后端 `E:\code\Metrix\.venv\Scripts\python.exe -m pytest server\tests\test_auth_rbac.py -q` 通过 19 passed；前端 `npx vue-tsc --noEmit --noUnusedLocals --noUnusedParameters` 通过；前端 `npm run build` 通过；`python -m compileall -q app tests` 通过；Browser 打开 `http://127.0.0.1:5173/` 自动进入 `/login`，`#app` 正常渲染且控制台无 error。
## 2026-06-07：第二轮全量代码清理
- 新增 `web/src/utils/table.ts`，统一封装 Naive UI 表格单选筛选值读取逻辑；用户管理、公告管理和操作日志页面删除各自重复的 `singleFilterValue(...)` 实现。
- 新增 `web/src/utils/download.ts`，统一封装浏览器 Blob 下载逻辑；操作日志 CSV 下载和系统设置数据备份下载复用同一入口。
- 第二轮重新扫描前后端源码、调试残留、废弃权限清理逻辑、表格筛选、下载逻辑、服务层和 repository；保留的 `void load...` 均为 Vue 事件/监听中显式触发异步刷新，废弃权限常量仍用于迁移清理和前端过滤，不作为死代码删除。
- 清理验证生成的 `web/dist`、`.pytest_cache`、`server/.pytest_cache` 和源码目录 `__pycache__`，未留下构建产物或测试缓存。
- 验证：后端 `E:\code\Metrix\.venv\Scripts\python.exe -m pytest server\tests\test_auth_rbac.py -q` 通过 19 passed；前端 `npx vue-tsc --noEmit --noUnusedLocals --noUnusedParameters` 通过；前端 `npm run build` 通过；`python -m compileall -q app tests` 通过；Browser 打开 `http://127.0.0.1:5173/` 自动进入 `/login`，`#app` 正常渲染且控制台无 error。
## 2026-06-07：最终全量复查
- 后端测试中直接向 SQLite 绑定 `datetime` 对象会触发 Python 3.12 默认 SQLite datetime adapter 废弃警告；新增测试辅助 `sqlite_datetime(...)`，测试写入原始 SQL 时间字段时统一使用 ISO 字符串，消除项目自身兼容性 warning。
- 最终轮重新检查前后端源码清单、配置文件、调试残留、废弃权限迁移逻辑、API 聚合导出、前端工具抽取、服务层和 repository；未发现新的可确认冗余代码、死代码或不兼容调用。
- `.gitignore` 仍覆盖 `web/dist/`、`runtime/`、`.pytest_cache/`、`__pycache__/`、日志、上传下载导出目录、临时目录和本地敏感配置；最终清理后未保留构建产物或测试缓存。
- 验证：后端 `E:\code\Metrix\.venv\Scripts\python.exe -m pytest server\tests\test_auth_rbac.py -q` 通过 19 passed，仅剩 FastAPI/Starlette TestClient 对当前 httpx 的第三方提示；前端 `npx vue-tsc --noEmit --noUnusedLocals --noUnusedParameters` 通过；前端 `npm run build` 通过；`python -m compileall -q app tests` 通过；`git diff --check` 通过；Browser 打开 `http://127.0.0.1:5173/` 自动进入 `/login`，`#app` 正常渲染且控制台无 error。
## 2026-06-07：重新全量复查第一轮
- 操作日志前端补齐系统设置相关审计动作：`settings.update`、`settings.backup` 纳入日志页动作筛选常量，并补充中英文展示文案；目标类型补齐 `system_settings`，避免系统设置更新和数据备份日志在 UI 中显示裸编码。
- 后端测试在系统设置用例中增加审计日志断言，确认设置更新和备份会记录 `settings.update`、`settings.backup`，并可按 `system_settings` 目标类型筛选。
- Browser 完整模拟测试覆盖登录、忘记密码、语言/主题切换、首页公告展示/已读、用户新增/编辑/筛选/重置密码/禁用启用/角色分配/删除、注册必填/关闭注册/审核通过/驳回、权限角色新增授权删除、公告新增编辑搜索批量删除单删、操作日志筛选、系统设置保存、个人资料和密码修改、404 返回；测试产生的临时用户、角色、公告和管理员资料改动均已恢复或清理。
- in-app Browser 当前不支持 `download` 事件，下载功能验证采用 UI 按钮可见性加后端响应校验：操作日志导出返回 `text/csv; charset=utf-8` 且带 BOM 表头，数据备份返回 `application/zip`。
- 验证：后端 `E:\code\Metrix\.venv\Scripts\python.exe -m pytest server\tests\test_auth_rbac.py -q` 通过 19 passed，仅剩 FastAPI/Starlette TestClient 第三方提示；前端 `npx vue-tsc --noEmit --noUnusedLocals --noUnusedParameters` 通过；前端 `npm run build` 通过；`python -m compileall -q app tests` 通过；调试残留扫描无代码命中；Browser 页面控制台无项目 error。
