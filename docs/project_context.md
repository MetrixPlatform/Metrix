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
- 安装、注册、用户管理、注册审批驳回、权限管理和个人信息表单统一改为左侧标签布局；后续多语言表单统一使用 `label-width="auto"`，由组件自动测量标签列宽。
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
## 2026-06-07：重新全量复查第二轮
- 第二轮重新读取前后端源码、测试、配置、路由、页面、服务层、repository、schema、model 和工具函数，未发现新的可确认冗余代码、死代码、废弃调用或不兼容实现；上一轮补齐的系统设置审计日志显示保持稳定。
- 第二轮 Browser 关键回归覆盖登录、首页、用户管理、权限管理、公告管理、操作日志、系统设置、个人信息和 404；所有主页面均可达，运行时平台名恢复为 `Metrix`，页面控制台无项目 error。
- 第二轮清理 `web/dist`、`.pytest_cache`、`server/.pytest_cache` 和源码目录 `__pycache__` 后工作区保持干净；`.gitignore` 仍覆盖构建产物、运行时库、缓存、日志、临时目录和本地敏感配置。
- 验证：后端 `E:\code\Metrix\.venv\Scripts\python.exe -m pytest server\tests\test_auth_rbac.py -q` 通过 19 passed，仅剩 FastAPI/Starlette TestClient 第三方提示；前端 `npx vue-tsc --noEmit --noUnusedLocals --noUnusedParameters` 通过；前端 `npm run build` 通过；`python -m compileall -q app tests` 通过；调试残留扫描无代码命中。
## 2026-06-07：新增 API Token 与 OpenAPI 文档
- 后端新增 `api_tokens` 表、模型、repository、schema、service 和 `/api/tokens` 接口；Token 明文仅创建时返回一次，数据库只保存 SHA-256 哈希、展示前缀、过期时间、最后使用时间和创建时间。
- 统一鉴权依赖 `get_current_user` 支持普通登录 Token 与 `mtx_` API Token；API Token 调用会检查系统 `api_enabled`、Token 状态/过期时间、账号状态、角色 API 能力和目标接口权限，后续使用现有权限依赖的 API 默认支持 Token 调用。
- 系统设置新增 `api_enabled` 总开关，公开设置会返回该字段；关闭后 `/api/tokens`、`/openapi.json`、`/docs` 和 API Token 调用都会被后端拒绝，前端菜单和路由守卫同步隐藏/拦截 Token 与 API 文档页面。
- OpenAPI 默认公开路径已关闭，改为自定义受保护 `/openapi.json`；`/docs` 继续使用本地 `swagger-ui-bundle` 静态资源，但同样要求登录并拥有 `action:api_docs:read`。
- 权限种子新增 `route:tokens`、`route:api_docs`、`action:api_token:read/create/delete` 和 `action:api_docs:read`，权限管理页通过现有权限字典和 i18n 映射展示 API 分组。
- 前端新增 `TokenManageView` 和 `ApiDocsView`：Token 页支持创建、只显示一次明文、复制、刷新和删除；API 文档页读取受保护 OpenAPI JSON，按标签、方法、路径、参数、请求体和响应码展示，并支持复制/下载 JSON。
- `docs/development_page_guide.md` 新增 API 与 Token 开发规则，说明后续接口如何自动支持 Token、如何维护 OpenAPI 文档、权限和 `feature: "api"` 页面开关。
- 浏览器验证发现 Vite 代理使用宽泛 `/api` 前缀会把前端页面 `/api-docs` 误转发到后端，导致直接刷新 API 文档页时显示后端 404；开发代理已改为只匹配 `/api/` 和 `/openapi.json`。
- 浏览器验证覆盖管理员登录、系统菜单新增 Token/API 文档入口、Token 创建明文一次性展示、Token Bearer 调用首页汇总和 `/openapi.json`、API 关闭后 Token/OpenAPI 后端强拒绝、API 文档页直接刷新、系统设置 API 开关、权限页 API 分组；临时 Token 已删除，API 开关恢复开启。
- 验证：后端 `E:\code\Metrix\.venv\Scripts\python.exe -m pytest server\tests\test_auth_rbac.py -q` 通过 20 passed，仅剩 FastAPI/Starlette TestClient 第三方提示；前端 `npm run build` 通过。
## 2026-06-08：完善 Token 显示复制与 API 文档测试
- 系统设置新增 `api_token_reveal_enabled`，默认开启，并随公开设置返回；系统设置页新增“允许显示/复制 Token”开关，关闭后前端隐藏完整 Token 显示/复制入口，后端 `/api/tokens/{id}/secret` 继续强制返回 403。
- `api_tokens` 表新增可空 `token_value` 字段并通过启动同步补列；新创建 Token 会保存完整值以支持后续显示/复制，列表接口仍不返回明文，只返回 `secret_available`，旧 Token 或无完整值 Token 只能显示前缀。
- Token 创建页明确提供“永不过期”和“自定义时间”两种过期策略，`expires_at = null` 表示永不过期；列表中空过期时间显示为“永不过期”，最后使用时间为空仍显示“从未”。
- Token 列表支持在设置允许且完整值可用时显示或复制完整 Token，所有显示/复制都通过后端 secret 接口走登录态、API 开关、角色权限和本人 Token 校验。
- `/openapi.json` 输出时复制 schema 后过滤 `/api/install*` 和 `/api/health*` 及对应 tag，避免把安装和探活接口展示给 API 调用者；业务接口和后续新路由仍按 OpenAPI 自动展示。
- API 文档页新增 Token 输入和接口测试弹窗，按 OpenAPI 自动渲染 path/query 参数与 JSON 请求体，发送 Bearer API Token 请求并展示 HTTP 状态和响应内容；不在前端维护第二份接口清单。
- `docs/development_page_guide.md` 同步补充 Token 可恢复显示、永不过期、OpenAPI 过滤和 API 文档测试面板的后续开发约定。
- 验证：后端 `E:\code\Metrix\.venv\Scripts\python.exe -m pytest server\tests\test_auth_rbac.py -q` 通过 20 passed；前端 `npm run build` 通过；Browser 验证登录、Token 列表“永不过期”和完整 Token 显示弹窗、API 文档页测试入口可达；接口验证 API Token 调用 `/api/auth/me` 成功，OpenAPI 不含 `/api/install*` 和 `/api/health*`。
## 2026-06-08：完善 API 文档详情、测试结果和日志来源
- 后端新增轻量认证上下文 `server/app/core/auth_context.py`，`get_current_user` 会把本次请求来源写入 SQLAlchemy session：网页登录为 `web`，API Token 调用为 `api` 并记录 Token 前缀。
- `/api/tokens*` 增加 `require_web_session` 强校验，Token 管理只能网页登录态操作；API Token 即使拥有角色权限也不能创建、查询、显示完整值或删除 Token。
- `audit_logs` 表新增 `source` 和 `api_token_prefix` 字段，并通过启动同步补列；`record_audit(...)` 自动从认证上下文写入来源，日志列表和 CSV 下载都能区分 Web/API 操作。
- API Token 继续作为用户级资源处理，后端测试显式覆盖其他用户无法看到或显示不属于自己的 Token。
- `/openapi.json` 过滤范围扩展到 `/api/tokens*` 和 `api-tokens` tag，API 文档只展示可被 API Token 调用的平台能力，不展示 Web-only Token 管理接口。
- API 文档页改为“接口列表 + 详情弹窗 + 测试弹窗”：列表保持紧凑，详情里查看 operationId、参数说明、请求体字段、请求示例、响应说明和响应示例；测试弹窗展示实际发送的数据和返回结果。
- 前端新增 `web/src/i18n/openapi.ts` 作为 API 文档专用翻译表，使用 `tag.*`、`operation.<operationId>.*`、`parameter.*`、`schema.property.*` 和 `response.<status>` key；页面优先使用翻译，缺失时回退 OpenAPI 原始说明。
- API 文档测试请求体不再默认 `{}`，会按 OpenAPI schema 自动生成可编辑示例；响应详情额外补充 400、401、403、404、500 等常见结果解释。
- `docs/development_page_guide.md` 补充 API 文档翻译、请求/响应示例、Token Web-only、用户级 Token 和审计来源规则。
## 2026-06-08：修复多语言表单布局
- 全局 `.inline-form` 左侧标签表单改为配合 `label-width="auto"` 使用，标签保持单行、右对齐，输入框左边缘由 Naive UI 自动标签列统一对齐。
- 登录、注册、安装、系统设置、Token、API 文档、个人信息、用户管理、权限管理和公告管理中的左侧标签表单统一移除固定窄 `label-width`，避免英文或后续新增语言把标签挤压换行。
- 长文案按钮、工具栏按钮、设置复选项、Token/安装单选项允许自适应换行；760px 以下侧栏收窄释放内容宽度，560px 以下左侧标签表单自动切为上下布局，避免窄屏遮挡输入控件。
- `docs/development_page_guide.md` 新增多语言表单布局规则：新增页面使用 `.inline-form` + `label-width="auto"`，不得写固定窄标签宽度，并需验证登录、注册、系统设置和常用弹窗。
- 验证：前端 `npm run build` 通过；Browser 复测登录页和注册页桌面/390px 窄屏，标签不换行、无重叠，桌面输入框左边缘保持一致；`git diff --check` 通过。

## 2026-06-08：优化操作日志详情展示
- `audit_logs` 表新增 `detail_data` 结构化详情字段，并通过启动同步补列；响应 schema 会把旧日志空值或 JSON 字符串兜底解析为对象，保持旧日志可读。
- 后端新增 `audit_detail(...)` 和 `audit_changes(...)` 辅助函数，用户、角色、公告、设置、认证和 Token 等写操作开始记录操作对象、字段变更前后值和必要 meta；密码、完整 Token、hash 等敏感信息不写入日志。
- 操作日志列表和 CSV 导出新增 `source` 查询参数，后端 repository 统一按来源过滤；关键字搜索同时覆盖结构化详情内容。
- 前端操作日志表格去掉 Token 前缀列，只展示来源列；来源列支持表头筛选，详情列改为可点击摘要，完整操作记录在弹窗中展示基础信息、操作对象、字段变更和附加记录。
- 多语言补充操作日志详情弹窗、变更字段、常见结构化字段名和来源筛选文案；长字段值在弹窗内换行，列表摘要保持单行省略，避免撑乱表格。
- `docs/development_page_guide.md` 补充操作日志开发规则：新增写操作应优先传结构化 `detail_data`，页面只显示来源，完整信息放详情弹窗，CSV 保留来源和 Token 前缀用于审计导出。
- 验证：后端 `E:\code\Metrix\.venv\Scripts\python.exe -m pytest server\tests\test_auth_rbac.py -q` 通过 20 passed；前端 `npm run build` 通过；Browser 验证日志页无 Token 前缀列、来源筛选可用、详情弹窗显示变更前后值且不展示 Token 前缀。

## 2026-06-08：支持列表列宽调整
- 前端 `web/src/utils/table.ts` 新增 `withResizableColumns(...)`、`updateColumnWidth(...)` 和 `sumColumnWidths(...)`，统一封装 Naive UI 表格业务列可拖拽调整宽度、拖拽后更新列宽状态和横向滚动宽度计算。
- 用户管理、公告管理、操作日志、Token 管理和 API 文档详情中的 `n-data-table` 都接入列宽拖拽；操作列保持不可调整并继续固定在右侧，选择列和展开列保持组件默认行为。
- 各列表页列宽对象改为响应式状态，拖拽后列宽与 `scroll-x` 会同步更新，避免调整列宽后横向滚动范围不足。
- `docs/development_page_guide.md` 在表格横向滚动规则中明确：后续列表表格所有业务列都必须支持拖拽调整列宽，并优先复用表格工具函数，不在页面中重复实现拖拽逻辑。
- 验证：前端 `npm run build` 通过；后端 `E:\code\Metrix\.venv\Scripts\python.exe -m pytest server\tests\test_auth_rbac.py -q` 通过 20 passed；`git diff --check` 通过；Browser 验证用户列表真实拖拽 `username` 列宽从约 155px 调整到 315px，公告、操作日志、Token 和 API 文档详情表格均为业务列有拖拽手柄、操作列无拖拽手柄。

## 2026-06-08：调整语言切换按钮字重
- 语言切换按钮中的 `文` 和 `A` 字重从 600 调整为 500，让图标文字更轻但仍保持清晰可读。
- 验证：前端 `npm run build` 通过；`git diff --check` 通过；Browser 打开 `/tokens` 后读取语言按钮 computed style，`文` 和 `A` 的 `font-weight` 均为 500。

## 2026-06-08：全量复查并修正导出与类型检查配置
- 第一轮重新阅读后端 schema、API、service、repository、测试、前端路由、store、API 封装、工具、组件、视图、i18n、CSS 和开发文档，未发现可安全删除的死代码；保留的废弃权限相关逻辑仍用于迁移清理和旧数据过滤。
- `web/tsconfig.json` 增加 `noEmit: true`，避免直接运行 `vue-tsc` 或参数传递错误时把 `.js` / `.js.map` 产物写入 `web/src` 污染源码目录；最终构建后确认 `web/src` 未生成 JS/map 产物。
- 操作日志 CSV 导出与页面规则对齐：`/api/audit-logs/export` 只导出 `id,operator,source,action,target_type,target_id,detail,created_at`，不再包含 `api_token_prefix`；测试和开发文档同步更新。
- Browser 完整模拟回归覆盖管理员登录、语言/主题、权限角色新增授权删除、用户新增/搜索/编辑/禁用启用/重置密码/角色分配/删除、受限账号登录、Token 永不过期创建/显示/复制/删除、API 文档详情和测试请求、API Token Web-only 边界、公告新增/搜索/编辑/批量删除/单删、操作日志来源列/详情弹窗/CSV、系统设置保存恢复、数据备份、注册提交/审核通过/驳回/登录、个人资料保存/改密/新密码登录和 404。
- 测试过程创建的临时用户、角色、Token、公告均已通过页面或接口清理；运行时设置恢复为 `Metrix`、注册开启、API 开启、Token 显示开启、日志保留 90 天。
- 验证：后端 `E:\code\Metrix\.venv\Scripts\python.exe -m pytest server\tests -q` 通过 20 passed，仅剩 FastAPI/Starlette TestClient 第三方提示；前端 `npx vue-tsc --noUnusedLocals --noUnusedParameters` 通过；前端 `npm run build` 通过；`python -m compileall -q server\app server\tests` 通过；`git diff --check` 通过；调试残留扫描无代码命中。
## 2026-06-08：修复表单控件宽度跳变
- 全局 `.inline-form` 为 `n-form-item`、`n-input`、`n-input-number`、`n-select`、`n-date-picker` 等控件补齐 `min-width: 0` 和 `width: 100%`，避免输入内容、密码后缀图标或校验状态导致控件宽度跳变。
- 安装页数据库和管理员信息区域改为更稳定的局部上标签布局，MySQL 端口列最小宽度提升到 150px，管理员信息输入框不再被左侧标签挤窄。
- `docs/development_page_guide.md` 增加表单控件宽度规则：新增表单必须撑满可用宽度并保持宽度稳定，紧凑布局不得牺牲输入框可用宽度。
## 2026-06-08：清理后端内置权限展示文案
- 后端 `server/app/core/permissions.py` 不再保存中文权限名称、分组和说明，权限种子的 `name`、`group_name`、`description` 统一生成 `permission.*` 稳定资源 key。
- 后端内置角色初始化改为保存 `role.admin.*`、`role.user.*` key；开发库启动同步时会覆盖旧中文内置角色和权限种子数据。
- 前端 `web/src/i18n/builtins.ts` 改为根据内置角色 key、权限 `code` 和分组 key 做 i18n 翻译，不再维护重复的权限 code 映射表。
- `docs/development_page_guide.md` 明确新增权限和内置角色种子不得写中文或英文展示文案，展示统一交给前端 i18n。

## 2026-06-08：优化表单占位提示
- 前端 `web/src/i18n/naive.ts` 基于 Naive UI 本地语言包派生项目 locale，统一清空 Input、InputNumber、Select、Cascader、DatePicker 和 TimePicker 的泛化默认 placeholder，避免普通表单空值时显示“请输入/请选择”。
- 登录、公告管理、用户管理和 Token 管理页面移除手写的泛化 placeholder；有明确标签的普通字段只依赖 label 和校验提示表达字段含义。
- 搜索框、时间范围、SQLite 默认路径、公告定向目标格式、API 测试输入等有信息增量的 placeholder 保留。
- `docs/development_page_guide.md` 增加表单占位提示规则：不要重复字段名或必填校验文案，placeholder 只用于搜索、格式示例、默认值说明、批量输入规则等场景。

## 2026-06-08：拆分前端语言资源
- 前端语言资源改为按语言拆分到 `web/src/i18n/locales/zh-CN.json` 和 `web/src/i18n/locales/en-US.json`，JSON 内按 key 路径分组，避免继续在 TS 文件中维护多语言大对象。
- `web/src/i18n/messages.ts` 改为语言类型、默认语言资源和动态加载器；默认 `zh-CN` 随首包加载，`en-US` 通过动态 import 按需拆成单独 chunk。
- `web/src/i18n/index.ts` 新增 `setupI18n(...)`，应用启动前加载当前语言；`appStore.setLocale(...)` 改为异步加载语言资源后再切换，路由默认语言同步和系统设置保存均等待语言切换完成。
- OpenAPI 翻译从 `openapi.ts` 的多语言对象迁移到语言 JSON 的 `openapi.*` 分组，`openApiText(...)` 继续保留原调用方式并走统一 i18n 查询。
- `web/src/i18n/builtins.ts` 不再硬编码 `admin/user` 角色 key 映射，优先翻译后端返回的资源 key，并按 `role.<code>.*` 兜底，后续新增内置角色更少改代码。
- 普通表单字段显式补充 `placeholder=""`，搜索、默认路径、格式示例和 API 请求体等有信息增量的 placeholder 保留，避免局部页面继续漏出 Naive UI 默认“请输入/请选择”。
- `docs/development_page_guide.md` 补充语言 JSON、动态加载、OpenAPI 分组和语言切换统一入口规则。

## 2026-06-08：优化语言名称维护方式
- 每个语言 JSON 顶层 `language` 改为只保存自己的显示名称，例如 `zh-CN.json` 写 `简体中文`，`en-US.json` 写 `English`，不再在每个文件里维护所有语言名称。
- `web/src/i18n/messages.ts` 通过 `import.meta.glob` 自动发现 `locales/*.json` 并生成语言加载器，默认语言 `zh-CN` 保持静态首包加载，其他语言继续按需拆分。
- `web/src/i18n/index.ts` 的 `localeOptions` 改为从各语言 JSON 的顶层 `language` 读取名称；语言切换器和系统设置语言下拉不再依赖 `language.zhCN`、`language.enUS` 这类跨语言 key。
- `web/src/i18n/naive.ts` 提供 `getNaiveLocale(...)`，没有单独适配 Naive UI 语言包的新语言会先回退默认组件语言，避免新增翻译 JSON 时必须同步修改组件语言映射。

## 2026-06-08：稳定认证页语言切换按钮
- `LanguageSwitcher` 改用离线内联 SVG 翻译图标，移除手工拼接的“文/A”文字图标，避免字体和行高导致按钮内容漂移；图标尺寸由 `.language-switcher-svg` 统一控制。
- 认证、注册和安装页的 `.auth-top-actions` 使用独立顶部工具行，`.auth-page` 预留顶部行空间，避免页面滚动或安装页表单过高时语言切换按钮遮挡表单。
- 开发文档补充规则：认证/注册/安装页顶部工具按钮必须使用固定尺寸图标按钮并放在独立顶部工具行，不覆盖卡片内容。

## 2026-06-08：修正认证页顶部工具布局
- 认证、注册和安装页的 `.auth-top-actions` 从覆盖式固定浮层改为 `.auth-page` 的独立顶部工具行，避免浏览器高度较小时语言/主题按钮压住登录表单字段。
- 新增 `ThemeToggleButton` 组件统一封装主题切换按钮，登录页、注册页、安装页和主框架页头统一复用；注册页和安装页补齐主题切换入口。
- 开发文档更新认证页顶部工具规则：未登录页面工具按钮必须放在独立顶部工具行，不得覆盖卡片内容。

## 2026-06-08：修复登录页小窗口元素重叠
- `.auth-page` 的布局行从 `auto minmax(0, 1fr) auto` 调整为三段 `auto`，窗口高度不足时通过页面整体滚动展示内容，避免登录卡片被压缩后与顶部工具按钮或版权页脚重叠。
- 登录页底部注册和忘记密码链接增加 `login-form-links` 专用竖向布局，避免与版权声明挤在同一水平区域。
- 安装页增加 `install-page` 类，认证页顶部工具行按登录、注册、安装卡片宽度分别对齐；窄屏下工具行和卡片统一撑满可用宽度。
## 2026-06-08：修复窄窗口按钮与标签布局
- 全局页面最小工作尺寸统一为 `600px * 400px`，保留浏览器宽高自适应；当窗口小于该尺寸时通过外层滚动条访问完整内容，不再为安装页、注册页或后台主框架设置更大的硬性最小宽高。
- 工具栏、筛选区和表单操作区的普通文字按钮保持单行显示，筛选网格最后一列使用内容宽度，避免查询等按钮在窄窗口下被挤成逐字竖排。
- 560px 以下左侧标签表单切换为上标签布局时，标签容器和标签文本同步左对齐，避免登录、注册、安装等页面的标签继承桌面右对齐后贴到表单右侧。
- `docs/development_page_guide.md` 补充页面最小尺寸、按钮挤压和窄屏上标签左对齐规则。
## 2026-06-08：修复注册页窗口恢复后表单挤压
- 560px 以下的 `.inline-form` 上标签布局将标签宽度固定为 `max-content` 并左对齐，避免 Naive UI `label-width="auto"` 在窄窗口挂载时把整行宽度缓存为最大标签宽度。
- 验证注册页放大状态下标签列约 80px、输入框约 468px，不再出现从小窗口进入注册页后最大化时输入框只剩小方块的问题。
- `docs/development_page_guide.md` 补充规则：小屏上标签布局不要让 label 使用会填满整行的 `auto` 宽度。
## 2026-06-08：调整登录注册页工具按钮与表单宽度
- 登录页和注册页的语言切换、主题切换按钮移动到卡片内右上角，按钮尺寸缩小为 26px、图标 16px；安装页仍保留独立 `.auth-top-actions` 工具行。
- 登录卡片宽度由 440px 收窄到 360px，注册卡片由 680px 收窄到 520px，登录输入框约 246px、注册输入框约 308px，减少输入框和卡片横向占用。
- Browser 验证登录页和注册页卡片内工具按钮不与标题重叠，`docs/development_page_guide.md` 已同步新的认证页工具按钮布局规则。
## 2026-06-08：固定认证页版权页脚
- `.auth-footer` 改为固定在视口底部，登录、注册和安装等认证页通过 `.auth-page` 底部 padding 预留 60px 安全空间，避免版权位置随卡片高度变化。
- Browser 验证登录页和注册页页脚 `position: fixed` 且贴合视口底部，卡片不与页脚重叠；安装页在已安装环境会被路由带回登录页，使用同一 `.auth-footer` 样式规则。
- `docs/development_page_guide.md` 补充认证页版权页脚固定底部的开发规则。
## 2026-06-08：恢复认证页底部操作横排
- 登录页底部“注册账号/忘记密码”恢复横向居中排列，避免竖向堆叠占用卡片高度。
- 注册页底部“提交注册/返回登录”合并到同一行，提交按钮占用主要宽度，返回登录保持紧凑文本入口。
- `docs/development_page_guide.md` 补充认证页底部辅助操作优先横排的布局规则。
## 2026-06-08：收紧 API Token 与 Web 管理能力边界
- 后端 `/openapi.json` 过滤扩展到认证、系统设置、用户管理、角色权限和权限字典接口；API 文档页只展示可由 API Token 调用的业务接口，不再显示认证、系统设置、用户、角色权限分组。
- `/api/auth/me`、个人资料、修改密码、系统设置、用户管理、角色和权限字典等 Web 管理接口增加 `require_web_session` 强校验，API Token 调用时返回 `error.webOnly`。
- 后端测试补充断言：OpenAPI schema 不包含 `/api/auth*`、`/api/settings*`、`/api/users*`、`/api/roles*`、`/api/permissions*`、`/api/tokens*` 等 Web-only path，且 API Token 不能调用这些管理接口。
- `docs/development_page_guide.md` 更新 API 与 Token 规则，明确后续新增 Web-only 管理接口必须同时做网页登录态强校验和 OpenAPI 过滤。

## 2026-06-08：添加注册审核开关
- 系统设置新增 `registration_approval_required`，默认开启；公共设置、系统设置保存、审计快照、前端类型和设置页表单同步支持该字段。
- 默认开启审核时，注册接口继续创建 `pending` 用户并返回 `auth.registerSubmitted`；注册页不再显示固定副标题，改为注册成功后弹窗提示等待管理员审核，确认后返回登录页。
- 关闭审核时，注册接口直接创建 `approved` 用户、写入 `approved_at` 并授予默认 `user` 角色，返回 `auth.registerSuccess`；前端仅显示普通成功提示后返回登录页。
- 开发文档补充注册审核规则：后端返回稳定 message code，前端 i18n 负责展示；调整系统设置 schema 时必须同步前端类型、store 默认值、设置表单和测试 payload。

## 2026-06-08：全量复查与完整功能回归
- 重新检查前后端源码、路由注册、权限种子、API 客户端、store、页面组件、i18n、CSS、后端 schema/service/repository/model 和测试用例；未发现新的可确认冗余代码、死代码、调试残留或不兼容实现。保留的废弃权限清理逻辑仍用于开发库同步迁移和前端过滤，不作为死代码删除。
- Browser 完整模拟回归覆盖登录、忘记密码弹窗、语言/主题切换、首页粒子和公告侧栏、用户新增/校验/编辑/禁用启用/重置密码/角色分配/删除、普通用户菜单权限、角色新增/授权/删除、公告新增/展示方式校验/筛选/批量删除/已读状态/操作他人权限边界、操作日志筛选和详情、系统设置保存、Token 创建/显示/删除、API 文档过滤和测试请求、个人信息保存、注册审核开启/关闭两条路径、404 自动返回主页。
- 测试过程中创建的 `codex_` 前缀临时用户、角色、公告和 Token 已通过页面操作清理；系统设置恢复为注册开启、注册需管理员审核开启、API 开启、Token 显示开启，管理员账号 `admin` 密码保持 `123456`。审计日志作为真实操作记录保留。
- 最终验证：`python -m compileall -q server\app server\tests` 通过；`python -m pytest server\tests -q` 通过 21 passed，仅有 FastAPI/Starlette TestClient 与当前 httpx 的第三方提示；`npx vue-tsc --noEmit --noUnusedLocals --noUnusedParameters` 通过；`npm run build` 通过；`git diff --check` 通过；Browser 控制台无项目 error。

## 2026-06-09：调整系统设置操作权限展示
- 权限码 `action:setting:operate` 继续保持不变，避免影响现有数据库授权关系和后端校验逻辑。
- 前端权限页展示文案从“操作系统设置”调整为“系统备份权限”，英文同步为 `System backup permission`，明确该权限当前用于系统设置页的数据备份操作。

## 2026-06-09：权限分配改为树形节点
- 权限管理页右侧权限分配区从多卡片分组改为单个可折叠树形列表，一级节点为权限分组，二级节点为具体路由/功能权限。
- 树形分组支持展开/收起、分组全选、半选状态和已选数量显示；保存时仍只提交真实权限 ID，后端权限码、授权接口和内置管理员强制全权限逻辑保持不变。
- 样式复用现有主题变量，列表内容在右侧权限树内部滚动，避免后续权限增多时继续堆叠卡片或顶走页面工具栏。
- 权限树默认全部收缩，权限分配工具栏提供一键展开和一键收缩图标按钮，便于权限数量增加后快速浏览或收纳。

## 2026-06-09：优化系统设置页布局
- 系统设置页从单页堆叠和左右工具区布局改为标签分页，当前包含“基础设置、注册与账号、API 与 Token、日志策略、数据备份”，页面自身撑满后台工作区，标签内容区独立滚动。
- 基础设置等少量字段表单改为受控宽度，避免输入框横向撑满整个工作区；底部保存按钮固定在设置卡片内，备份入口移动到“数据备份”标签页，按钮文案改为“备份数据”。
- 开发指南记录系统设置页后续新增设置应优先放入已有标签页，确实独立时再新增同级标签页，不要回到左右大卡片、单页堆叠或大面积留白布局。

## 2026-06-09：优化 API 文档详情空状态
- API 文档详情弹窗中，参数和请求体为空时不再只显示通用空状态短横线，改为横向空状态并明确显示“无需参数”或“无需请求体”。
- `web/src/i18n/locales/zh-CN.json` 与 `web/src/i18n/locales/en-US.json` 补充 API 文档空参数、空请求体文案，保持前端 i18n 统一维护。

## 2026-06-09：对齐操作日志下载展示
- 操作日志页面下载按钮文案从“下载 CSV”改为通用“下载”，避免界面按钮过度暴露文件格式细节。
- Web 页面下载改为前端按当前筛选和排序分页拉取完整日志，并复用页面展示函数生成 CSV；导出表头、来源、操作类型、目标类型、详情摘要和创建时间与网页展示一致。
- CSV 创建时间字段增加文本保护，避免 Excel 自动把时间截断显示成 `28:35.2` 这类格式；旧的前端 `downloadAuditLogs(...)` 封装和语言包 `auditLog.downloadCsv` 已删除。
- 审计动作继续由后端记录稳定 code，例如 `user.register`、`settings.backup`；前端按 `auditLog.action.<resource>.<action>` 翻译操作类型，按 `auditLog.target.<target_type>` 翻译目标类型，找不到翻译时兜底显示原始 code。
- 操作日志页的操作类型和目标类型筛选选项改为从默认语言包自动派生，再合并当前列表返回的新 code；后续新增写操作只需要补后端稳定 code 和各语言 JSON，不要在页面里继续维护硬编码动作列表。

## 2026-06-09：支持操作日志多选筛选
- `web/src/api/client.ts` 的 `queryString(...)` 支持数组参数，数组会序列化为重复 query key，保留单值参数原有行为。
- 操作日志页面的来源、操作类型和目标类型筛选从单选改为多选，筛选状态使用数组维护；账号范围 `actor_scope` 继续保持单选，因为它代表本人/全部的权限边界。
- 后端 `/api/audit-logs` 和 `/api/audit-logs/export` 同步接收多值 query 参数，仓储层统一清洗空值并用 `IN` 条件查询；同字段多值按 OR 语义处理，多字段之间继续按 AND 组合。
- 后端测试补充同字段多选和多字段组合筛选断言，确保 Web 列表、前端下载分页拉取和保留的原始导出接口使用一致的筛选语义。
- 开发指南补充表头枚举筛选规则：普通枚举字段默认优先支持多选；涉及权限范围或账号边界的字段可按业务语义保持单选。

## 2026-06-09：优化操作日志详情摘要布局
- 操作日志详情弹窗顶部摘要从 `n-descriptions` 表格布局改为自定义 `dl` 键值列表，显示为“标签: 内容”的同行形式。
- 摘要值统一使用单行省略号处理并保留 `title` 悬停完整内容，避免窗口缩小时账号、时间、目标对象等字符串换行撑乱弹窗。
- 摘要区默认两列展示，窄屏下自动切为一列；样式集中放在 `web/src/styles/main.css`，页面组件只保留结构和数据绑定。

## 2026-06-09：全量复查与完整功能回归
- 第一轮和第二轮重新检查前后端源码、权限种子、路由注册、API 封装、store、页面组件、i18n、CSS、后端 schema/service/repository/model 和测试用例；未发现可安全删除的源码冗余、死代码、调试输出、废弃组件引用或不兼容实现。
- 静态扫描确认后端业务源码没有中文展示文案残留，前端源码除语言 JSON 外没有中文硬编码命中；调试残留扫描仅命中文档历史记录和开发规则，未命中源码。
- Browser 回归覆盖登录、退出、忘记密码弹窗、首页公告侧栏、普通用户权限边界、用户新增/编辑/禁用启用/重置密码/注册审批通过/删除、权限角色新增/授权保存/删除、公告展示方式校验/新增/首页已读/批量删除、操作日志列表/详情/下载入口、系统设置分页/保存/备份入口、Token 创建明文展示/删除、API 文档过滤和详情空状态、注册提交等待审核弹窗、404 自动返回。
- 内置浏览器对下载接收、页面脚本构造事件和部分 Teleport 弹层 click 偶发受限；已用页面可见状态、真实坐标点击、后端 401 响应和前端登录失效事件代码路径补齐验证。无效 Token 调用 `/api/auth/me` 返回 401 和 `error.authExpired`，前端 `client.ts` 会清理登录态并派发 `metrix.auth-expired`，路由监听后跳回 `/login`。
- 测试过程中创建的临时用户、角色、公告和 Token 均已清理；最终用户列表仅保留内置管理员，`codex*` 用户剩余 0 个。系统设置保持注册开启、注册需管理员审核开启、API 开启、Token 显示开启，管理员账号 `admin` 密码保持 `123456`。
- 第二轮验证：后端 `..\.venv\Scripts\python.exe -m pytest tests -q` 通过 21 passed，仅有 FastAPI/Starlette TestClient 与当前 httpx 的第三方提示；`..\.venv\Scripts\python.exe -m compileall -q app tests` 通过；前端 `npx vue-tsc --noEmit --noUnusedLocals --noUnusedParameters` 通过；前端 `npm run build` 通过。
- 清理验证生成的 `web/dist`、`.pytest_cache`、`server/.pytest_cache`、源码目录 `__pycache__` 和本轮 `runtime/codex-logs`；`.gitignore` 仍覆盖构建产物、运行时库、缓存、日志、临时目录、本地依赖和敏感配置。

## 2026-06-10：新增框架产品化待处理清单
- 新增 `docs/framework_open_items.md`，记录当前框架从内部平台开发底座升级为通用后台 Web 框架所需补齐的事项。
- 待处理清单覆盖 README/快速启动/初始化/部署说明、标准 `demo-crud` 示例模块、权限/路由/菜单/i18n 模块化注册、数据库迁移策略、submodule 业务模块接入机制和前后端测试覆盖。
- 当前建议保持轻量演进：优先通过模块 manifest、示例模板和清晰文档减少新增模块时对核心文件的分散修改，暂不引入复杂插件系统。

## 2026-06-10：落地模块化注册基础机制
- 前端新增 `web/src/modules/types.ts` 和 `web/src/modules/registry.ts`，通过 `import.meta.glob` 自动发现 `web/src/modules/*/index.ts`，模块使用 `defineModule(...)`、`definePage(...)` 和 `defineMenuGroup(...)` 声明页面、菜单、权限、功能开关和 fallback 顺序。
- 内置页面迁移到 `web/src/modules/core/index.ts`，`web/src/router/page-registry.ts` 不再手写页面数组，只从模块声明派生主框架子路由、侧边栏菜单、页面标题和无权限 fallback。
- 前端 i18n 支持“公共语言包 + 模块语言包”合并，默认语言随首包加载，非默认语言继续按需动态加载；内置路由标题迁移到 `web/src/modules/core/i18n/zh-CN.json` 和 `en-US.json`，减少全局语言包重复。
- 后端新增 `server/app/core/module.py`、`server/app/modules/registry.py` 和 `server/app/modules/core.py`；启动时自动扫描 `server/app/modules` 中的 `APP_MODULE`，统一收集 API router、页面权限、功能权限和 OpenAPI 隐藏规则。
- `server/app/main.py` 改为遍历模块 router 自动 `include_router(...)`，OpenAPI 过滤规则从模块声明读取；`server/app/api/__init__.py` 不再集中导出所有 API。
- `server/app/core/permissions.py` 保留现有稳定权限常量，底层权限种子与路由默认查询权限由模块注册器收集，兼顾现有 API/service 引用和后续模块化新增。
- `docs/development_page_guide.md` 更新新增页面、i18n、新增权限和后端 API 注册流程：后续业务优先在模块目录内完成声明，不要再修改 `router/index.ts`、`AppShell.vue` 或 `server/app/main.py` 手工注册。

## 2026-06-10：完成框架产品化第一轮落地
- 根目录 `README.md` 从占位文档扩展为快速启动和部署说明，覆盖项目定位、技术栈、目录结构、环境要求、前后端启动、安装初始化、常用环境变量、SQLite/MySQL、内网离线资源、部署建议、模块开发和验证命令。
- 新增标准 `demo-crud` 示例模块：后端位于 `server/app/modules/demo_crud`，包含 `api.py`、`models.py`、`schemas.py`、`repositories.py`、`services.py` 和模块入口；前端位于 `web/src/modules/demo-crud`，包含模块入口、API 封装、权限常量、页面和中英语言包。
- `demo-crud` 展示最小完整业务开发路径：模块自动注册路由/菜单/权限/i18n，列表后端分页，表头筛选，固定操作列，写操作审计，业务表记录 `created_by`，默认只能操作本人数据，额外 `action:demo_item:manage_others` 才能操作他人数据。
- 后端模块 manifest 增强：`AppModule` 支持 `model_paths` 和 `table_syncs`；建表前自动加载模块模型，开发期字段同步由模块声明提供；内置 `users`、`audit_logs`、`api_tokens` 字段同步迁移到 core 模块声明。
- `server/app/modules/registry.py` 增加重复声明校验，覆盖模块 key、router path、model path、页面权限 code 和资源权限 code，后续模块写错时应在启动或测试阶段尽早失败。
- `docs/development_page_guide.md` 补充标准 CRUD 示例、模块模型注册、开发期字段同步、数据库迁移边界和 submodule 接入规则；`docs/framework_open_items.md` 改为当前状态清单，标记第一轮已完成事项和后续增强项。
- 前端新增无依赖 smoke 检查 `web/scripts/smoke.mjs` 和 `npm run test:smoke`，用于校验模块入口与模块语言包结构；后续若测试范围扩大，再评估 Vitest 或浏览器回归工具。
- 后端测试新增 demo CRUD 覆盖，当前验证包括 `python -m compileall -q server\app server\tests`、`npm run test:smoke`、`npx vue-tsc --noEmit --noUnusedLocals --noUnusedParameters`、`npm run build`、`..\.venv\Scripts\python.exe -m pytest tests -q --basetemp .pytest-temp`，后端测试结果为 23 passed，仅保留 FastAPI/Starlette TestClient 与 httpx 的第三方提示。

## 2026-06-10：推进框架产品化待办第二轮
- 开发期字段同步新增 `migration_records` 记录表，字段补齐成功后记录同步 key、类型、目标和 SQL；重复同步同一 key 时直接跳过历史记录写入，避免旧库再次补字段被唯一键阻断。
- 后端模块注册器继续增强校验，除模块 key、router path、model path 和权限 code 外，也会校验 `table_syncs` 中同一表字段同步声明是否重复，避免多个模块对同一字段各自声明造成启动后数据库冲突。
- 新增基础模块脚手架 `scripts/create-module.mjs`，可生成前端模块入口、占位页面、模块语言包、后端模块入口和受权限保护的 ping 接口；脚手架只做最小骨架，完整 CRUD、审计、模型和本人/他人权限仍参考 `demo-crud`。
- 前端 smoke 检查增强：校验模块入口必须使用 `defineModule`，模块语言包必须覆盖所有公共 locale，不同语言的模块 JSON key 必须一致，模块入口中的 `titleKey`、`labelKey` 和 `routePermission(...)` 必须能在语言包中找到对应翻译。
- `README.md`、`docs/development_page_guide.md` 和 `docs/framework_open_items.md` 同步更新迁移记录、脚手架命令、当前已落地能力和后续仍需补齐的生产迁移脚本、模块生命周期、前端回归测试事项。

## 2026-06-10：补齐轻量迁移脚本和模块生命周期基础校验
- 后端 `AppModule` 增加 `version`、`dependencies` 和 `migrations`；业务模块可用 `migration_step(key, statements, description)` 声明一次性 SQL 迁移，安装初始化和已安装库同步都会执行未记录过的迁移。
- 迁移执行记录继续写入 `migration_records`，key 格式为 `migration:<module>:<step>`；同一迁移 key 已存在时跳过执行，适合新增索引、辅助表、轻量数据修正等可重复跳过的升级步骤。
- 安装流程 `install_system(...)` 在建表后执行模块迁移，再写入初始管理员和权限种子；已安装环境继续由 `sync_database(...)` 执行建表、迁移、字段同步和权限种子同步。
- 后端模块注册器校验模块依赖是否存在，并校验 migration key、table sync 字段、router/model path、页面权限和资源权限是否重复；前端模块注册器同步校验模块依赖、菜单分组、页面 key、页面 path 和页面权限重复。
- `scripts/create-module.mjs` 生成的前后端模块默认包含 `version=0.1.0` 和 `core` 依赖；`demo-crud` 也声明依赖 `core`，作为后续业务模块的最小生命周期元数据示例。

## 2026-06-10：完成框架产品化待办轻量版收口
- 后端模块生命周期补齐轻量实现：`AppModule` 新增 `lifecycle_hooks`，模块可通过 `module_lifecycle_hook(event, key, statements, description)` 声明 `install`、`upgrade`、`disable` 三类小型 SQL 钩子；安装和升级钩子按模块版本记录到 `migration_records`，禁用钩子在模块从 enabled 变为 disabled 时执行。
- 新增 `module_states` 表，`sync_database(...)` 和首次安装流程都会记录已发现模块的 key、version、status 和 dependencies；status 当前为 `enabled`、`disabled` 或 `missing`，用于追踪源码模块状态，不自动删除模块历史数据、权限或审计记录。
- 新增 `server/app/services/data_portability.py`，提供统一便携数据包导出和导入能力；系统设置中的“备份数据”改为复用该服务，备份 zip 内包含 `metadata.json` 和按表导出的 JSON 数据。
- 新增 `server/tools/migrate_database.py`，提供 `export`、`import`、`copy` 三个命令，支持 SQLite/MySQL 之间通过便携 zip 迁移数据；`copy` 会保留 `--backup` 指定的 zip 作为失败回滚依据。
- 前端模块类型要求 `AppModule.version` 必填；smoke 继续增强：现在会校验模块入口必须使用 `defineModule`、模块 key 必须匹配目录、版本必须为语义化格式、依赖必须存在、菜单分组和页面路径不能重复、页面菜单分组必须存在，并扫描模块源码中的 `routePermission(...)` 与 `actionPermission(...)` 翻译是否完整。
- `README.md`、`docs/development_page_guide.md` 和 `docs/framework_open_items.md` 已同步更新模块生命周期、便携迁移脚本、模块状态表、smoke 校验范围和剩余后续项边界；当前不引入复杂插件系统或 Alembic，后续只有生产升级频率明显增加时再评估。
- 新增后端测试覆盖模块状态首次写入、生命周期 install/upgrade/disable 钩子、便携数据包导出导入、MySQL 安装流程模块状态同步和 demo CRUD 既有能力；本轮验证通过 `compileall`、`pytest`、`npm run test:smoke`、`vue-tsc` 和 `npm run build`。

## 2026-06-10：补齐通用后台框架产品化能力
- `scripts/create-module.mjs` 从最小 ping 骨架升级为完整 CRUD 模块脚手架，默认生成前端模块入口、API、权限、CRUD 页面、双语 i18n，以及后端 `api.py`、`models.py`、`schemas.py`、`repositories.py`、`services.py` 和 pytest 模板；生成结果沿用 `demo-crud` 的分页、筛选、审计、本人/他人权限和 i18n 约定。
- 后端新增显式 schema migration 基础体系：`server/app/migrations/registry.py` 定义 `SchemaMigration`，`server/app/migrations/versions/0001_framework_baseline.py` 作为基线修订；`server/tools/migrate_database.py` 新增 `schema-new`、`schema-status`、`schema-apply`、`schema-rollback` 命令，执行记录写入既有 `migration_records`。
- 模块生命周期进阶：`MODULE_LIFECYCLE_EVENTS` 增加 `uninstall`，`server/app/db/init.py` 新增 `run_module_uninstall(...)`，迁移工具新增 `module-uninstall --backup`，用于先导出便携备份再执行模块卸载钩子并把 `module_states.status` 标记为 `uninstalled`。
- 模块依赖校验支持版本约束，`dependencies` 可继续写 `core`，也可写 `core>=0.1.0`、`core==1.2.0` 等；注册器会在启动/测试阶段阻止缺失或不满足版本约束的模块组合。
- 前端引入 `@playwright/test`，新增 `web/playwright.config.ts`、`web/tests/regression/framework.spec.ts` 和 `npm run test:regression`，当前浏览器回归覆盖未安装跳转安装页、已安装匿名用户跳登录页、登录态恢复后访问有权限模块页面。
- `.gitignore` 补充 `web/test-results/` 和 `web/playwright-report/`，避免 Playwright 运行产物进入版本控制；运行回归时首次需要 `npx playwright install chromium` 下载浏览器二进制。
- 文档同步更新 `README.md` 和 `docs/framework_open_items.md`，把正式迁移第一版、前端回归入口、CRUD 脚手架和模块卸载/依赖版本约束标为已落地能力；保留真正插件化加载、更重 CI 审批和更完整组件/浏览器测试作为后续按需增强。
- 验证结果：`node --check scripts/create-module.mjs`、后端 `compileall`、后端 `pytest tests -q --basetemp .pytest-temp` 通过 33 passed、前端 `npm run test:smoke`、`npm run build`、`npm run test:regression` 通过；额外临时生成 `scaffold-check` 模块验证脚手架产物可通过 smoke 和后端编译，验证后已删除临时模块文件。

## 2026-06-10：第一轮框架清理与回归修复
- 安装流程 `install_system(...)` 在 `run_migrations(engine)` 后补充 `sync_columns(engine)`，与已安装环境的 `sync_database(...)` 保持一致，避免复用旧结构数据库安装时 `create_all` 不补列导致种子写入失败；MySQL 安装测试同步断言字段同步步骤会执行。
- 显式 schema migration 加固为单线性链：发现分叉、缺根或非线性链时直接失败，不再静默按 revision 排序；`schema-rollback` 只允许回滚最新已应用修订，避免中间回滚造成迁移记录和真实结构不一致。
- `schema-new` 改用 `datetime.now(timezone.utc)`，并用 `repr` 写入 `revision`、`description`，避免 Python 3.12+ 弃用警告和名称中包含引号时生成无效迁移文件。
- 前端清理未使用导出：删除 `web/src/modules/demo-crud/permissions.ts` 中未被引用的 `DEMO_ITEM_READ`，删除 `web/src/i18n/index.ts` 中未使用的 `useI18n()`；脚手架移除未使用的 `pluralCamel`、`__PLURAL_CAMEL__` 和冗余 `tableName`。
- 路由修复：未知业务路径作为 `AppShell` 的 catch-all 子路由显示 `NotFoundView`，避免被根路由吞掉；Playwright 新增已登录未知路由显示 404 的回归用例。`NotFoundView` 仍保持 5 秒后自动返回首页的既有行为。
- 文档同步：`docs/development_page_guide.md` 从旧的 ping/占位脚手架描述更新为完整 CRUD 脚手架说明，补充 `permissions.ts`、`uninstall` 生命周期、显式 schema migration 命令和“只允许回滚最新修订”的边界；`README.md` 补充前端模块 `permissions.ts` 和 `npm run test:regression:install`。
- `.gitignore` 补充根目录 `.pytest-temp/`、`web/node_modules/.vite/`、`web/blob-report/` 等测试/构建边缘产物；浏览器回归留下的 `e2e_user_001` 已从本地运行库清理。
- 验证结果：`node --check scripts/create-module.mjs` 通过；后端 `compileall` 通过；`pytest tests -q --basetemp .pytest-temp` 通过 34 passed；前端 `npm run test:smoke`、`npx vue-tsc --noEmit --noUnusedLocals --noUnusedParameters`、`npm run build`、`npm run test:regression` 通过，Playwright 为 4 passed；浏览器快速回归覆盖用户、权限、公告、日志、设置、Token、API 文档、个人资料、demo CRUD、注册和 404 页面。

## 2026-06-10：第二轮文档一致性与 404 样式清理
- 第二轮复查未发现新的阻塞性代码 bug；重点修正剩余文档精度问题，避免后续新增模块时按旧路径或旧生命周期说明开发。
- `docs/development_page_guide.md` 的后端模块示例从旧的 `app.api.tasks:router` / `app.models.task` 改为当前业务模块路径 `app.modules.task.api:router` / `app.modules.task.models`，并统一示例中的模块 key、页面权限 page 名和依赖声明。
- `docs/development_page_guide.md` 的迁移辅助命令补充 `module-uninstall --backup`；`docs/framework_open_items.md` 的生命周期描述同步为 install/upgrade/disable/uninstall，`module_states` 状态同步为 enabled/disabled/missing/uninstalled。
- `README.md` 收敛 Playwright 回归覆盖描述，明确当前回归覆盖安装守卫、匿名登录页、登录态恢复、模块页面和 404，不再夸大为完整权限菜单覆盖。
- `web/src/styles/main.css` 中 404 页面样式从全视口高度调整为填满主框架内容区，避免 `NotFoundView` 嵌入 `AppShell` 后产生多余滚动或居中偏差。

## 2026-06-10：文档入口收敛
- 原 `docs/development_page_guide.md` 迁移到仓库根目录并改名为 `DEVELOPMENT_GUIDE.md`，标题改为“开发指南”，用于承载新增页面、模块、权限、迁移、API 和前端交互规范。
- `docs` 目录只保留 `project_context.md`，删除已不作为当前入口维护的 open items 与早期设计文档；当前开发者入口由 `README.md` 和 `DEVELOPMENT_GUIDE.md` 承担。
- `README.md` 更新目录结构和文档入口说明，移除平台限定描述，命令示例改为更通用的 `python` / `npm` 写法，并把开发规范引用指向 `DEVELOPMENT_GUIDE.md`。

## 2026-06-12：framework-stable 分支第三轮全量复查与修复
- 鉴权加固：`decode_access_token` 现在只接受纯数字 `sub`，伪造或异常 payload 统一走 401，不再因 `int(subject)` 抛 `ValueError` 返回 500；新增伪造 subject 回归测试。
- 模块生命周期一致性：`disable` 钩子改为与 install/upgrade/uninstall 相同的“先查 `migration_records` 再执行”模式，记录 key 带模块版本（`hook:<key>:disable:<version>:<hook>`）；模块反复启停不会重复执行非幂等 SQL，删除了旧的无守卫 `_run_lifecycle_hooks`，生命周期测试补充重复启停场景。
- RBAC 静默降级修复：`assign_roles`、`approve_user`/`create_user` 的 `role_ids`、`assign_permissions` 的 `permission_ids` 现在严格校验 ID 全部存在，无效 ID 返回 400（`error.roleNotFound` / 新增 `error.permissionNotFound`），不再静默部分生效；新增对应接口测试。
- 数据一致性：管理员直接创建的用户补记 `approved_by` 和 `approved_at`，与注册审批通过、免审注册路径保持一致。
- 审计补缺：`get_token_secret` 显示完整 Token 时记录 `api_token.reveal` 审计；语言包补充 `auditLog.action.api_token.reveal`。
- 后端清理：删除无引用的 `ApiTokenRepository.get()` 和前端从未调用的 `GET /api/users/{user_id}` 端点；`_user_profile_snapshot` 重复实现合并为 `app/services/users.py` 的 `user_profile_snapshot`，`auth.py` 复用。
- 前端修复：保存系统设置不再调用 `appStore.setLocale` 强制覆盖当前用户语言（`default_locale` 只影响无本地偏好的会话）；`AppShell` 公告弹窗改为标记已读成功后才关闭，失败时保持弹出；`PermissionView.loadData` 增加错误提示，避免首屏白屏；校验错误字段 `permission_ids` 的 label 修正为新增的 `field.permissions`。
- 前端去重与收敛：`LOCALE_STORAGE_KEY` 统一定义在 `config/app.ts`；`initialLocale()` 收敛到 `i18n/index.ts` 并导出复用，`stores/app.ts` 不再依赖 `settingsStore`；`isFeatureEnabled` 收敛为 `settingsStore.featureEnabled(...)`；剪贴板复制（含 `execCommand` 降级）抽到 `web/src/utils/clipboard.ts`，`TokenManageView` 与 `ApiDocsView` 共用，顺带修复 ApiDocs 复制无降级问题。
- 前端清理：`APP_SLUG`、`DEPRECATED_PERMISSION_CODES`、`TranslateParam` 改为模块内私有；删除无引用的 `.module-placeholder`、`.api-response-list` 样式和 `.filter-select` 选择器；移除模板中无样式的 `announcement-manage-card`、`demo-crud-toolbar`、`demo-crud-category-filter`、`announcement-popup-modal` class，脚手架模板同步去掉 `__KEBAB__-toolbar`。
- smoke 增强：`web/scripts/smoke.mjs` 新增基础语言包 `i18n/locales/*.json` 的 key 一致性校验（原来只校验模块语言包）。
- 有意保留的重复/设计边界：`modules/core.py` 与 `core/permissions.py` 的 READ 常量重复用于避免循环 import；`creator_usernames`/`actor_usernames` 在各模块 repository 重复属于模块自包含约定；dashboard API 和 `/api/audit-logs/export` 作为 API 契约保留；列表页分页/筛选模式按脚手架约定逐页实现，不抽公共 composable。
- 验证结果：后端 `compileall` 通过、`pytest` 36 passed（新增 2 个用例）；前端 `npm run test:smoke`、`npx vue-tsc --noEmit --noUnusedLocals --noUnusedParameters`、`npm run build`、`npm run test:regression`（4 passed）全部通过。

## 2026-06-12：framework-stable 合并进 main

- `framework-stable` 与 `main` 无分叉，仅领先 1 个提交（`f20af7a`）；已在本地对 `main` 执行 `--ff-only` 快进合并，两分支现均指向 `f20af7a`。
- 合并后复验：`.venv` 下 `pytest` 36 passed、`npm run test:smoke` 通过。
- `origin/main` 已推送至 `f20af7a`，与 `origin/framework-stable` 对齐。

## 2026-06-12：新增 FTP/SFTP 储存管理模块

- 新增前后端 `storage` 业务模块（`server/app/modules/storage`、`web/src/modules/storage`），完全走模块自动发现，未改框架核心注册文件。
- 数据表 `storage_connections`：`storage_id` 全局唯一（可自定义 3-64 位 `[A-Za-z0-9_-]`，留空自动生成 `stg_` + 10 位 hex，创建后不可修改）、协议仅 ftp/sftp、`base_path` 根目录限定、`is_shared` 共享开关、密码加密存储。
- 凭据加密：`server/app/core/security.py` 新增 `encrypt_secret`/`decrypt_secret`，用安装密钥 SHA256 派生 Fernet 密钥；密码只在连接远端时解密，API 响应与审计不回传。
- 共享/私有规则：列表可见 = 本人 + 共享（`action:storage:manage_others` 可见全部）；文件操作（浏览/下载/上传/删/改名/建目录）= 本人或共享或 manage_others；连接信息编辑/删除/测试 = 仅创建者或 manage_others，共享不放开修改权。
- 并发模型：每个文件 API 请求独立建连（`clients.py` 的 `FtpClient`/`SftpClient`）、用完即关，无连接池、无共享状态、无锁；连接超时 10s，多用户并行操作多个或同一服务器互不阻塞；测试 `test_storage_parallel_connections_use_isolated_clients` 验证每请求独立实例并全部关闭。
- 路径安全：所有 path 参数为相对连接根目录的虚拟路径，服务层做 `..` 逃逸检测（400 `error.storagePathInvalid`）后再拼 `base_path`，外部无法越出根目录；文件/目录名禁止斜杠。
- API 设计：管理 API（tag `storages`，`require_web_session`，OpenAPI 隐藏）`GET/POST /api/storages`、`PUT/DELETE /api/storages/{connection_id}`、`POST /api/storages/test`（编辑场景密码留空按 id 复用存量密码）；文件 API（tag `storage-files`，进入 API 文档，API Token 可直接调用）`GET {sid}/files`（keyword/recursive 搜索枚举，递归上限 1000 条/500 目录并返回 `truncated`）、`GET {sid}/download`（流式）、`POST {sid}/upload`（multipart）、`POST {sid}/mkdir`、`POST {sid}/rename`、`DELETE {sid}/files`（目录递归删除）。
- 审计：`storage.create/update/delete` 与 `storage.file_upload/file_delete/file_rename/file_mkdir`，详情不含密码。
- 前端：`StorageManageView` 列表页（关键字/协议筛选、storage_id 一键复制、共享/私有与状态标签、行内 管理/编辑/删除 按归属显隐）；`FileManagerModal` 980px 大弹窗（面包屑导航、递归搜索、多文件上传、下载、重命名、新建目录、递归删除目录，操作按钮按 `action:storage:operate` 显隐）；上传走 FormData，`client.ts` 的 `rawRequest` 对 FormData 不再强制 JSON Content-Type。
- 新依赖：`paramiko`（SFTP，自带 `cryptography` 供 Fernet 使用）、`python-multipart`（FastAPI 文件上传）；已写入 `server/requirements.txt`。
- FTP 实现细节：列目录 MLSD 优先，500/502 不支持时回退 LIST 解析（unix/IIS 两种格式）；下载用 `transfercmd` 真流式；编码 UTF-8。
- 测试：`server/tests/test_storage.py` 6 个用例（CRUD 与 ID 规则、加密落库校验、共享/私有可见性与越权、假客户端文件全操作与路径逃逸、test 端点与连接失败 503、API Token 全链路与 OpenAPI 可见性、并发隔离）；`test_auth_rbac.py` 中 3 处模块清单断言同步加入 storage。
- 验证：后端 `compileall` + `pytest` 42 passed；前端 `test:smoke`、`vue-tsc`（含 unused 检查）、`build`、`test:regression` 4 passed 全部通过。真实 FTP/SFTP 服务器联调待内网环境验证。

## 2026-06-12：确立列表页标准布局规范并对齐储存页

- 以公告管理、用户管理页为基准确立列表页统一布局，规范正文写入 `DEVELOPMENT_GUIDE.md` 第 2 节，后续所有列表页按此开发：
  - 工具栏一行：左侧 `<page>-filter-row` grid 只放关键字、可选时间范围和查询按钮；右侧放批量操作和新增按钮；枚举筛选一律不放工具栏。
  - 枚举筛选放列头：受控 `filter` + `filterMultiple: false` + `filterOptionValue` + `filterOptions`，`@update:filters` 转后端参数重查；时间列用受控 `sorter` + `@update:sorter`。
  - 表格统一 `remote` 后端分页、`flex-height` + `page-data-table`、列宽可拖拽；操作列 `fixed: "right"` + `table-action-group` 圆形 quaternary 图标按钮（`circle` + `NIcon` + `title`），不用文字按钮。
  - 后端列表接口必须支持对应筛选与排序参数，数据库层过滤。
- `StorageManageView` 对齐规范：协议下拉从工具栏移到列头筛选，新增 共享/私有、状态、创建人 列头筛选与创建时间列头排序；操作列改为 管理（FolderOpen）/测试（PlugConnected）/编辑/删除 图标按钮，行内测试按 id 复用存量密码。
- 后端 `GET /api/storages` 扩展 `shared`（shared/private）、`is_active`、`created_by`（me）、`sort_order` 参数，repository 数据库层过滤排序；`test_storage.py` 补筛选与排序断言。
- 验证：后端 `pytest` 42 passed；前端 `test:smoke`、`vue-tsc`、`build` 通过。
- 长表单弹窗规范：储存连接弹窗按钮移入 `n-modal` 的 `#action` 插槽（`modal-fixed-actions`），`main.css` 为 `.modal-card > .n-card__action` 定样式并用 `:has()` 收紧带 action 弹窗的内容区最大高度——按钮固定底部、仅表单滚动；规范已写入 `DEVELOPMENT_GUIDE.md`。
- API 文档 i18n 机制确认与修正：前端 `ApiDocsView` 通过 `openapi.*` 命名空间翻译文档（`openapi.tag.<tag>`、`openapi.operation.<operationId>.summary/description`、`openapi.parameter.common.<参数名>`、`openapi.schema.property.<属性名>`、`openapi.response.<code>`），后端 OpenAPI JSON 保持稳定英文。storage 模块语言包原误用 `api.*` 命名空间导致不生效，已改为 `openapi.*` 并补齐 `storage-files` tag 与 6 个文件 API 的中英文 summary/description。
- 新增目录打包下载接口 `GET /api/storages/{storage_id}/download-archive?path=`（tag `storage-files`，`STORAGE_READ` 权限，API Token 可调）：递归遍历目录打包为 ZIP 流式返回，非目录返回 400 `error.storageNotDirectory`。前端文件管理器目录行新增下载按钮，目录下载自动保存为 `<目录名>.zip`，`downloadEntry` 按 `is_dir` 区分单文件下载与目录打包。
- 目录打包改为真流式 ZIP（依赖 `zipstream-ng`，纯 Python 可离线部署）：先递归 `list_dir` 收集文件树并用 `archive.add(_lazy_download(...), arcname=...)` 注册惰性下载生成器，远端文件在 ZIP 流被消费时才逐个拉取（FTP 单连接顺序传输安全）；`_zip_stream` 用 `finally` 在迭代结束/客户端断开时关闭连接。优点：不占临时磁盘/内存、客户端断开即停止远端拉取、首字节延迟低；代价：响应无 `Content-Length`（chunked，无下载百分比）、流中途出错只能中断得到损坏包。已移除原 `zipfile` + `SpooledTemporaryFile` 先打包后发送方案。
- 新增对外连接检查接口 `GET /api/storages/{storage_id}/health`（tag `storage-files`，`STORAGE_READ` 权限，API Token 可调）：按存量连接登录远端并校验根目录可访问，成功返回 `storage.connectionOk`，失败返回 503 `error.storageConnectFailed` 或 400 `error.storageBasePathMissing`；范围规则与文件 API 一致（本人/共享/manage_others，禁用连接 400）。已补 operation 中英文翻译与测试断言。

## 2026-06-14：单端口部署——FastAPI 自动托管前端构建产物

- `server/app/main.py` 新增 `_mount_frontend(app)` 函数：启动时检测 `web/dist/index.html` 是否存在，存在则挂载 `/assets` 静态目录并注册 `GET /{path:path}` SPA fallback（缓存 `index.html` 到内存），不存在则跳过、纯 API 模式。
- 路由优先级自然正确：所有 `/api/*` 和 `/static/swagger-ui/*`、`/openapi.json`、`/docs` 在 fallback 之前注册，不会被拦截。
- 开发模式不受影响：依然 Vite 5173 + FastAPI 8000 双端口开发，proxy 机制不动。
- 部署：先 `cd web && npm run build`，再 `cd server && python main.py`，单端口 8000 同时服务 API 和前端页面，无需 Nginx。
- `web/dist/` 已在 `.gitignore` 中，构建产物不入仓库。
- 验证：后端 `pytest` 42 passed，`npm run build` 通过，路由挂载确认 SPA fallback 和 assets mount 均存在。

## 2026-06-14：新增数据库管理模块

- 新增前后端 `database` 业务模块（`server/app/modules/database`、`web/src/modules/database`），后端声明 `route:database`、`action:database:*` 与 `action:sql_script:*`，管理类接口隐藏 OpenAPI，数据与任务接口允许 API Token 调用。
- 数据模型新增 `db_connections`、`sql_scripts`、`data_jobs`：连接密码复用 `encrypt_secret`/`decrypt_secret` 加密存储；连接共享/私有、本人/他人 `manage_others` 范围规则沿用 storage；SQL 脚本有独立资源权限；任务记录保存导入/导出状态、产物路径、行数、过期时间和下载时间。
- 方言抽象 `engines.py` 通过 SQLAlchemy `Inspector` 提供 schema/table/column/primary key 元数据，当前 UI/API 支持 MySQL 与 MariaDB，内部保留 SQLite 路径用于可重复自动化测试；每次请求独立创建外部库 engine/connection，使用 `NullPool`，完成后 `dispose()`，避免跨用户共享连接状态。
- SQL 安全边界：`SELECT/SHOW/DESC/DESCRIBE/EXPLAIN/WITH` 单语句判定为 read，其余或多语句判定为 operate；`/query` 按分类动态校验 `database:read` 或 `database:operate`，`/run-script` 统一要求 operate，支持接口直接传 `content` 或按 `script_id` 执行已保存脚本。
- 数据 API 覆盖元数据、表数据分页、SQL 执行、多语句脚本执行、行级增删改、建表/改表/重命名/清空/删表、建库/改库/删库，以及导入/导出任务提交、任务查询、下载和删除。
- 异步数据任务：`jobs.py` 使用专用 `ThreadPoolExecutor`，并发数来自系统设置 `data_job_max_workers`（默认 2，范围 1-16），提交即返回 `job_id`，超出 worker 的任务在线程池队列排队；worker 使用独立平台 session 和独立外部库 engine。启动时把残留 pending/running 标为 failed，后台每 30 分钟清理过期或已下载任务文件与记录；导出成功保留时长来自系统设置 `data_job_retention_hours`，下载流结束后删除文件并标记 downloaded。
- 导出器支持 CSV（单表/单查询）、XLSX（多表多 sheet，`openpyxl` write_only）、SQLite、SQL；导入器支持 CSV/XLSX/SQLite/SQL，提供 append/overwrite/upsert 与可选自动建表，均按批读取/写入，避免一次性加载大数据。
- 前端新增 `/database` 连接列表、页内 SQL 工作台和页内数据任务视图：列表沿用 storage 规范，点击名称进入工作台；工作台包含库/表选择、表数据网格、行 JSON 编辑、新建库/表、删表、Monaco SQL 编辑器、执行结果表、导出结果、脚本保存/载入/执行和导入向导。数据任务不再作为独立侧栏页面，统一从数据库管理页进入；任务类型/状态筛选放在表头，工具栏只保留返回/刷新等单行动作。
- 列表 UI 规则：类型、状态、创建人等枚举筛选必须放表头并使用受控单选筛选；工具栏只放关键词/查询和右侧动作，`table-page-card` 工具栏默认不换行，避免筛选控件换行破坏页面。数据库连接列表和数据任务列表的创建时间列均支持正序/倒序远程排序；数据任务接口通过 `sort_order=ascend|descend` 控制。
- i18n 校验：数据库模块静态 `t(...)` key 已用脚本扫描中英文合并语言包并确认覆盖；公共语言包补齐 `common.back` 和 `common.confirm`，避免按钮/弹窗标题显示原始 key。
- 清理复查：移除 `DatabaseService` 中已由 `DataJobService` 接管的任务列表死代码与未使用导入；补齐后端 `message_response` 返回码对应的 `common.saved`、`common.deleted`、`database.rowsAffected` 中英文翻译；浏览器回归新增数据库管理页/内嵌任务页用例，覆盖任务入口、返回按钮翻译和创建时间排序请求。
- 第四轮审查跟进：`DataJobService` 不再吞 `BaseException`，executor 关闭/重配会等待旧任务收束，任务恢复/清理失败会记录 warning；导入批量写入使用安全 bind name 映射，支持包含 `$` 的合法列名；`SHOW/DESC/DESCRIBE/EXPLAIN` 不再强制拼接分页 SQL；移除数据库 schema/engine 中确认未使用的常量；Storage 目录 ZIP 下载失败清理改为 `finally`。
- 前端清理：API 文档测试 query 必填参数使用独立 `apiDocs.queryParamRequired` 文案；文件大小格式化抽到 `utils/format.ts`；SQL 工作台新建库/表改为 Naive UI 弹窗；新增 `npm run typecheck` 和 `npm run verify`，TS 覆盖 Playwright 配置/测试，新增 `pytest.ini` 固定后端测试入口与临时目录。
- UI 对齐：数据库内嵌数据任务页返回按钮改为与储存文件管理页一致的图标返回按钮，保留 `aria-label` 以兼顾可访问性和回归测试。
- 数据库标识符修复：MySQL/MariaDB 库名、表名、列名允许数字开头（如 `0421`），统一依赖后端 quote identifier 保证安全；`PydanticCustomError` 增加全局 400 响应处理，避免服务层直接校验失败冒泡为 500。
- 数据库工作台布局修复：侧栏加宽并固定最小宽度，库/表操作按钮改为两列等宽网格，移除动作区横向滚动造成的挤压痕迹；Tab 内容区改为 flex column，SQL Monaco 编辑器固定 280px 可见高度，避免切到 SQL 页时塌成一条线。Playwright 回归新增工作台布局断言（侧栏宽度、按钮不溢出、SQL 编辑器高度）。
- 数据库工作台顶部返回按钮统一为储存文件管理页同款 `ArrowLeft20Regular` 图标按钮，并保留 `aria-label/title`；Playwright 回归断言按钮仍可访问且不再显示文字返回。
- 数据库工作台侧栏改为树状库表管理（`n-tree`）：库节点用 `Database20Regular`、表节点用 `Table20Regular` 图标区分，点击库节点展开并懒加载其表（`on-load`），点击表节点加载数据；不再用下拉选择库，库多时也好控制。SQL 页移除库下拉，改为只读“当前库”标签。Monaco 编辑器跟随 `appStore.dark` 设置 `vs-dark/vs` 主题并在切换时 `setTheme`，修复深色模式下编辑器仍为白色。
- 数据库工作台树状管理再升级（脚本入树 + 节点内操作）：库节点下分「表」「脚本」两个分类子节点，分别懒加载该库的表与该连接的 SQL 脚本（脚本随连接走）；动作按钮全部进入树节点 `render-suffix`——库节点显示「刷新」图标 + 「⋯」操作菜单（新建库/新建表/删除库），表节点显示「⋯」（导入/清空表/删表），脚本节点显示「⋯」（载入/执行/删除）；操作容器 `onClick` 阻止冒泡避免误触选中。移除顶部刷新/新建/删除工具栏与独立「脚本」Tab（脚本改由树管理，点击脚本载入到 SQL 编辑器）。SQL 页结果表可折叠（折叠时 Monaco 编辑器填满，便于写长 SQL）。
- 表节点「⋯」菜单新增「导入」：点击直接以该库该表为目标打开导入向导，无需先切换选中表。`SqlWorkbenchView` 用独立 `importTarget`（database/table）驱动 `ImportWizard`，数据页导入按钮与表节点导入都先设置 `importTarget` 再开窗；`ImportWizard` 监听 `show`，每次打开时把表单的库/表同步为最新目标并清空已选文件（修复此前向导库/表只在挂载时初始化、后续不更新的隐患）。
- SQL 脚本改为按库归属：`sql_scripts` 新增 `database` 列（model + 模块 `table_syncs` 列同步给存量库补列，DDL 用反引号兼容 MySQL 保留字与 SQLite）；`SqlScriptPayload`/`SqlScriptItem`、repository.list、service.list_scripts、`/api/sql-scripts` 均加 `database` 过滤；前端保存脚本时带上当前选中库，树里脚本分类按 `connection_id + database` 加载。修复此前脚本随连接显示在所有库下的问题——现在脚本只出现在对应库的「脚本」分类。新增后端用例 `test_sql_script_is_database_scoped`。
- SQL 页折叠结果按钮从顶部工具栏移到编辑器下方的「查询结果」栏（右侧），更贴近被控制的结果区；编辑器 `min-height` 保持 280 满足回归断言，结果折叠时编辑器自然填满。
- SQL 多结果导出：`ExportRequest` 新增 `queries: list[ExportQuery]`（name + sql），`exporters._datasets` 优先按 queries 生成多数据集（每条 SELECT 一个 sheet/表，写语句报 `error.databaseExportReadOnly`，CSV 多结果走原 single-only 校验报错）。前端「导出结果」改为弹窗：用 `splitSqlStatements`（识别引号/注释的 `;` 拆句）取出编辑器里的 SELECT/WITH 语句，复选选择导出哪些；多选时格式仅 XLSX/SQLite/SQL（自动剔除 CSV）。执行逻辑不变，只读用户仍可用。新增后端用例 `test_database_export_multiple_queries`（多 sheet xlsx + CSV 多结果失败）。
- 数据表格优化：数据表与查询结果表列均设固定 `width:180 + minWidth:80 + resizable:true`，支持鼠标拖拽调整列宽；列保留 `ellipsis:{tooltip:true}`，内容超宽截断后悬浮显示完整内容。数据表（远程分页）表头排序受控——`@update:sorter` 写入 `dataSort{columnKey,order}` 并以 `order_by + order_desc` 重新拉取；查询结果表（内存数据）用 `sorter:"default"` 客户端排序。后端 `table_rows`/`table_data`/`/table-data` 路由新增 `order_desc` 方向参数，`getTableData` 同步加 `order_desc`。新增后端排序方向断言。
- 表数据分页策略：`/api/databases/{conn_id}/table-data` 支持 `include_total` 参数（默认 true 保持 API 兼容），`total_exact` 标记总数是否精确。数据库工作台表数据标签页默认取精确总数，底部分页显示“共 X 条”，不再长期显示“已加载至少 X 条”的估算文案；如后续确需大表极速首屏加载，需同时设计可见的“估算总数/刷新精确总数”交互，不能只静默传 `include_total=false`。前端默认页大小为 50，表节点点击时先切换选中状态并异步加载数据，使用请求序号忽略过期响应，避免连续切表时旧响应回写。
- 数据库连接列表和数据任务列表按列表规范补齐列宽拖拽：列统一设置 `width/minWidth/resizable`，数据库列表 `scroll-x=1500`、任务列表 `scroll-x=1600`，`.page-data-table .n-scrollbar-rail--horizontal` 常显，避免超宽列时横向滚动条不可见。
- 数据库任务命名与 API 收敛：外部 API 从泛称 `/api/data-jobs` 改为 `/api/database-transfer-jobs`，OpenAPI tag 仍为 `database-transfer-jobs`，响应 schema 仍为 `DatabaseTransferJob*`；前端正式名称统一显示“数据库任务”，入口按钮和页内短名称显示“导数任务”，避免界面文案过长，也避免与后续定时任务、数据处理任务等通用任务概念冲突。数据库数据 API 与数据库任务 API 均补齐 `openapi.operation.*`、参数和 schema property 的中英文翻译，API 文档页可显示明确 summary/description。
- OpenAPI `operationId` 不再使用 FastAPI 默认的路径拼接长 ID。`server/app/core/openapi_ids.py` 的 `short_operation_id` 统一生成为 `<tag>.<route_function>`（tag 中 `-` 转 `_`），例如 `database_data.list_tables`、`database_transfer_jobs.submit_export`、`storage_files.download_storage_file`；这样既短、可读，又避免不同 tag 下函数名重复。前端 API 文档 i18n 的 operation key 必须同步使用该短 ID。
- 启动生命周期会调用 `normalize_legacy_operation_ids(app.routes)`，自动用 FastAPI 默认旧 ID 与当前短 ID 生成映射，并幂等修正开发库中 `audit_logs`、`migration_records` 里残留的旧长 ID（action/target/detail/detail_data/key 等文本字段），避免历史操作日志/操作记录仍显示反人类旧标识。demo CRUD 虽然已隐藏导航，但 `/api/demo-items` 仍作为开发参考接口进入 API 文档，必须维护 `demo-items` tag 与 `demo_items.*` operation 的中英文 `openapi.*` 翻译。
- API 文档 i18n 查询需要特殊处理带点的 `operationId`：`web/src/i18n/openapi.ts` 会优先把 `operation.<operationId>.summary/description`、`parameter.<operationId>.<name>` 中的 operationId 当作语言包里的完整 key 查询（如 `"demo_items.update_demo_item"`），避免 vue-i18n 的点路径解析把短 ID 拆成多层导致回退英文。
- 项目规则 `.cursor/rules/rules.mdc` 明确版本控制偏好：执行新任务前若工作区已有未提交的有意义修改，应先提交现有修改作为干净基线；任务完成后在运行时允许时必须提交有意义变更。若运行时安全约束阻止无当前会话明确授权的自动提交，必须明确说明冲突并取得授权后立即提交，不能静默跳过。
- 列表显示规范：所有页面和弹窗中的 `n-data-table` 普通数据列默认单行显示，超出列宽显示省略号并在鼠标悬停时通过 Naive UI `ellipsis.tooltip` 或元素 `title` 展示完整内容；`withResizableColumns` 会统一给普通列补 `ellipsis: { tooltip: true }`，动作列/选择列/展开列不受影响。表格横向滚动宽度应使用列宽合计，`sumColumnWidths()` 会统一追加末端缓冲，避免滚动到最右侧时最后一列或固定操作列被裁切；不要再为宽表写死小于实际列宽总和的 `scroll-x`。全局 CSS 禁止表格单元格换行，并对按钮、标签、文件名、复制单元格等自定义渲染元素做单行省略。操作日志详情弹窗中的自定义变更表和 meta 列表也按同一规则处理。
- 储存管理上传交互：`web/src/api/client.ts` 提供基于 `XMLHttpRequest` 的 `upload<T>()`，用于获得 `upload.onprogress`，仍沿用 Authorization 头、401 失效事件和统一错误文案，并支持 `AbortSignal` 取消单个上传请求；储存文件上传通过该方法回传单文件进度。`FileManagerView` 上传时右下角显示固定尺寸浮窗，默认展开，标题显示总上传进度和完成/失败/取消数量，右上角提供收起和关闭按钮，展开态展示文件列表与单文件进度，pending/uploading 文件可单独取消，超高滚动；收起态只保留标题栏和总进度，按网盘上传任务面板的轻量模式设计。
- 储存管理文件操作：储存连接列表 `keyword` 同时匹配名称、ID、主机、创建人用户名和姓名，前端搜索框清空后自动回到第一页重查。文件管理页支持复制、移动、粘贴和批量删除；复制/移动先进入页内剪贴板，右上角仅在有剪贴板时显示粘贴按钮，粘贴目标为当前目录，若当前目录有同名项则一次性选择覆盖、自动重命名或取消。行操作统一收纳到“更多”下拉菜单，批量删除使用表格多选，目录删除仍走后端递归逻辑。后端新增 `/api/storages/{storage_id}/copy`、`/move`、`/batch-delete`，复制目录通过下载流写入临时缓冲后上传，移动优先使用远端 rename，并补审计 `storage.file_copy`、`storage.file_move`、`storage.file_batch_delete`。
- 导航栏排序设置：`SystemSettings/PublicSettings` 新增公开字段 `navigation_order`，后端以 JSON 字符串存入 `system_settings`，只接受 `path:/...` 与 `group:<key>` 两类 key，保存时会去重并过滤非法项。前端 `page-registry` 为菜单项生成稳定 `navigationKey`，侧边栏按 `settingsStore.navigationOrder()` 覆盖默认 `menu.order`；未出现在设置里的新菜单会按默认顺序追加。默认导航顺序为首页、储存管理、数据库管理、系统管理。系统设置新增“导航栏”页签，标题说明和恢复默认按钮固定显示，中间清单使用 Naive UI `NScrollbar trigger="none"` 常显滚动条；该页签使用 `navigation-settings-pane/navigation-settings-section/navigation-order-scroll` 专用高度约束，禁止整体页签滚动，避免底部项目被保存栏遮挡。顶级菜单和分组子菜单分层用上移/下移调整，分组默认收缩且可展开/收缩，恢复默认会清空自定义数组，避免后续新增菜单被旧排序固定住。
- 数据库任务保留时长改为系统设置项：`SystemSettings`/`SystemSettingsUpdate` 以 `data_job_retention_hours` 作为实际字段（默认 168，范围 1-8760 小时），继续返回/接受 `data_job_retention_days` 兼容旧配置；系统设置「数据库任务」页使用数值输入 + 小时/天单位选择，保存时统一换算成小时。导出成功后的 `expires_at` 和孤儿文件清理均读取小时级设置，不再使用固定 24 小时。`/api/database-transfer-jobs/download-count` 返回当前用户已完成未下载导出任务数量，并支持可选 `connection_id`；数据库列表页「导数任务」角标不传连接，统计全平台本人未下载完成导出任务，数据库工作台角标传当前连接 id，只统计该连接下本人任务。提交导出/导入任务后 toast 提示“请到导数任务中查看”并刷新角标。
- 数据库任务列表查询：`GET /api/database-transfer-jobs` 支持 `keyword`、`connection_id`、`created_by=me|others`，返回项新增 `created_by_username`；管理员可筛其他人任务，普通用户仍被服务层限制为本人任务。前端导数任务列表不再提供折叠筛选区，也不在表头暴露类型/状态/创建人筛选，只保留关键字搜索框和搜索按钮，放在刷新按钮左侧；搜索框 `clearable`，点击清空会重置关键字并重新加载。工作台进入任务页时仍可带当前连接范围并以可关闭标签展示。
- 数据库连接列表搜索：`GET /api/databases` 的 `keyword` 同时匹配连接名称、ID、主机、默认库名、创建人用户名和创建人姓名；前端数据库管理搜索框提示包含“创建人”，按 Enter 或点击查询触发搜索，点击输入框清空按钮会自动回到第一页并重新查询。
- 数据库标识符处理：库/schema/default_database、表名、字段名、索引名和排序字段统一按可引用标识符处理，允许中文、横杠等真实数据库常见名称，但拒绝空值、超长和控制字符；所有 SQL 拼接必须继续通过 `ExternalDatabase.quote_identifier()` 统一加反引号/双引号并转义。不要在表数据、行编辑、建表、改表、索引、排序字段或库名参数中重新使用窄正则拦截，否则会导致中文库名或 `fdd外部邻区-eutranrelation` 这类真实表名报 `Invalid table`/`Invalid schema`。字段类型允许 `COLLATE "..."` 这类元数据后缀，但仍禁止分号等危险字符。
- 数据库脚本与表结构设计器：`SqlScriptItem` 返回 `statement_count`，并新增 `GET /api/sql-scripts/{script_id}` 供脚本详情查看；工作台加载脚本后维护当前脚本状态，顶部可查看脚本 ID、创建时间、最后修改时间和语句数量，保存会调用 `PUT /api/sql-scripts/{id}` 更新原脚本，不再误新建。`POST /api/databases/{conn_id}/run-script` 支持按 `script_id` 执行已保存脚本，路径连接 ID 仍必填，`database` 可选；传入 `script_id` 时优先使用保存内容，未显式传库名时使用脚本绑定库，并校验脚本连接归属。表分类和脚本分类节点右侧增加 `+` 快捷新建按钮；表结构设计器支持新建表时自定义字段、默认值、主键、自增、备注和索引，编辑现有表时读取字段/主键/索引，生成字段新增/修改/删除、字段重命名和索引新增/删除动作，并可直接修改表名（前端先调用现有重命名表 API，再提交结构变更）。字段类型编辑使用下拉选择 + 长度输入组合，类型列和类型下拉宽度要优先保证可读，`VARCHAR/CHAR/DECIMAL/NUMERIC` 可输入长度，`INT/BIGINT/TEXT/DATETIME` 等无需长度的类型禁用长度框；MySQL/MariaDB 返回的 `VARCHAR(200) COLLATE "utf8mb4_0900_ai_ci"` 会解析为 `VARCHAR` + `200` 显示，同时保存时保留 `COLLATE ...` 后缀；未知或带特殊修饰的既有类型走自定义类型保留，避免无意丢失。后端 `CreateTableRequest` 支持 `indexes`，`AlterTableRequest` 支持 `index_actions` 和 `rename_column`，表详情响应新增 `indexes`；SQLite 重命名表使用 `ALTER TABLE ... RENAME TO ...`，MySQL/MariaDB 继续使用 `RENAME TABLE`。
- SQL 脚本命名与临时模式：同一 `connection_id + database` 范围内脚本名称唯一，`SqlScriptService.create/update` 会通过 `SqlScriptRepository.get_by_scope_name()` 拦截重复名称并返回 `error.sqlScriptNameDuplicate`，不同库下可使用同名脚本。数据库工作台 SQL 工具栏提供“临时 SQL”按钮，点击后解除 `currentScript` 绑定、关闭脚本详情、清空树节点选中和当前库/表选择但保留编辑器内容；此后执行走普通临时 SQL，不会误更新已保存脚本，保存按钮也回到新建脚本模式。
- 前端导航清理：CRUD 示例模块保留路由、代码和注释作为开发新页面参考，但移除 `menu` 配置，默认不再显示在导航栏；系统分组内顺序调整为用户、权限、公告、日志、Token、API 文档、系统设置，系统设置固定在该分组底部。
- 新增本地开发启动脚本 `dev.bat`（项目根）：分别在两个窗口启动后端（`server/` 下设 `METRIX_RELOAD=1` 跑 `python main.py`，uvicorn 自动重载）与前端（`web/` 下 `npm run dev`，Vite HMR），改代码即自动更新；首次会在 node_modules 缺失时自动 `npm install`；缺 `.venv` 会给出提示。后端重载依赖 `main.py` 既有的 `METRIX_RELOAD` 环境变量开关。
- 多轮代码优化（用临时 ruff 扫描，仅分析用途、未入 `requirements`，完成后卸载还原 venv）：第1轮后端——`audit.py` 的 `Mapping` 改从 `collections.abc` 导入（去废弃 typing 导入）、`permissions.expand_permissions` 循环变量不再遮蔽 `route_code` 导入、`engines.ExternalDatabase.__enter__` 去掉多余引号注解、`exporters` 合并完全重复的 `_safe_sqlite_identifier/_safe_sql_identifier` 为 `_safe_identifier`。第2轮前端——`SqlWorkbenchView` 把 5 处结构相同的 `dialog.warning` 确认弹窗抽成 `confirmAction(content,onConfirm,positiveText?)`（净减 16 行）。第3轮——移除脚本页改造后遗留的无用文案 `database.tabs.scripts`、`database.script.search`。复核结论：后端 ruff F/UP 已为 0（无死码/未用导入/废弃调用），剩余 E501 长行、FastAPI `Depends` 默认值（B008 误报）、storage 内一致的 `raise ... ` 不带 `from`（B904 风格）属既有风格非冗余，按 KISS 不做大范围改动。每轮 pytest(46)+typecheck+build+regression(6) 通过并各自浏览器验证（确认弹窗、表节点删表等）后提交。
- 修复 tab 面板高度自适应：`.database-main .n-tabs-pane-wrapper` 设为 `display:flex; flex-direction:column`，补齐 flex 链，数据/查询表 `flex-height` 真正填满高度，消除底部大片空白。
- 数据库工作台库表树支持拖拽调宽：`.database-workbench-body` 使用 `--database-sidebar-width` 控制左侧列宽，中间 `database-sidebar-resizer` 作为竖向拖拽条，宽度限制为 220-560px 且至少保留右侧主区域 520px；用户拖动后的宽度保存到 `localStorage` key `metrix.databaseWorkbench.sidebarWidth`，双击拖拽条恢复默认 280px，窗口缩放时会重新钳制，避免右侧内容被挤没。
- 修复 SQL 编辑器代码提示（之前输入 SEL 无补全）：`MonacoEditor` 补全 provider 增加 `getWordUntilPosition` 计算 range，开启 `quickSuggestions` 与触发字符。关键字/函数不再手写硬编码，改为复用 Monaco 自带 SQL 语法定义里的列表——从 `monaco-editor/esm/vs/basic-languages/sql/sql.js` 导入 `language.keywords` 与 `language.builtinFunctions`（在 `vite-env.d.ts` 补了该模块的最小类型声明），再叠加库/表/列名（字段优先、函数次之、关键字最后，用 `sortText` 排序）。Monaco 基础 SQL 仅提供高亮不含补全，注册 completion provider 是标准做法；如需按方言（MySQL）做语法解析级的上下文补全，可引入 `monaco-sql-languages`（DTStack，ANTLR 解析、含 MySQL worker），属较重依赖，当前未引入。
- 储存文件复制/移动/批量删除与创建人搜索增强后，`pytest server/tests/test_storage.py -q`、`npm run typecheck` 通过。
- 数据库脚本详情/原脚本更新/表结构设计器增强后，`pytest server/tests/test_database.py -q`、`npm run typecheck` 通过，ReadLints 无新增诊断；表结构编辑补充表名重命名和字段重命名后复跑同样验证通过。
- 表名/字段名/库名宽松标识符支持后，新增中文 + 横杠表名、中文字段名和中文库名参数回归，`pytest server/tests/test_database.py -q` 通过。
- 数据库工作台库表树可拖拽调宽后，`npm run typecheck` 通过，ReadLints 无新增诊断。
- SQL 脚本同库重名限制和临时 SQL 模式后，`pytest server/tests/test_database.py -q`、`npm run typecheck` 通过，ReadLints 无新增诊断。
- 数据库工作台表数据标签页恢复精确总数分页后，`npm run typecheck` 通过，`git diff --check` 通过。
- SQL 脚本独立重命名入口后，`npm run typecheck` 通过。
- 数据库工作台表数据标签页加载回写和标签切换卡顿修复后，`npm run typecheck`、`npm run build`、`git diff --check` 通过。
- 数据库工作台表数据复制功能后，`npm run typecheck` 通过。
- 验证：`compileall server/app` 通过；`pytest server/tests -q` 43 passed；`npm run test:smoke` 通过；`npm run build` 通过；本次页内任务/表头筛选修正后复跑 `npm run build` 与 `pytest server/tests/test_auth_rbac.py` 通过；第二轮清理后复跑 `npm run test:smoke`、`npm run test:regression`（5 passed）、`pytest server/tests`（43 passed）和 `npm run build` 通过；第三轮复查复跑严格 TS 未使用检查、Python compileall、数据库/响应翻译覆盖扫描和 `npm run test:smoke` 通过；第四轮跟进后 `npm run verify` 通过、`pytest` 为 44 passed，并新增导入 bind name 回归测试；真实启动后端 8000 与前端 5173 后，用管理员 `admin/123456` 完成核心 API 烟测和真实浏览器导航（首页、用户、权限、公告、审计、设置、Token、储存、数据库、开发示例、API 文档、数据库内嵌任务页）通过；ReadLints 无新增诊断。本地 MySQL `127.0.0.1:3306 root/123456` API 级集成验证通过（创建连接、测试连接、元数据、查询、写入、XLSX 异步导出与下载）。Docker MariaDB 集成验证已通过：使用 `127.0.0.1:7897` 代理经 Registry API 下载/导入 `mariadb:11` 镜像后，临时容器完成创建连接、测试连接、schema/table 元数据、查询、写入、SQL 异步导出与下载验证。工作台树状重构后复跑 `npm run typecheck`、`npm run build`、`npm run test:regression`（6 passed）通过，并用临时 Playwright 深色截图脚本核对树状库表、图标、新建/删除下拉、刷新图标与 Monaco 深色主题渲染正常后删除该临时脚本与截图。脚本入树 + 节点内操作 + 高度自适应 + SQL 结果折叠 + 补全修复后再次复跑 `npm run typecheck`、`npm run build`、`npm run test:regression`（6 passed）通过，并用临时深色截图（7 列 236 万行数据场景）核对数据表填满无空白、库>表/脚本分类树、节点刷新/⋯操作按钮、SQL 结果折叠展开、输入 SEL 弹出 SELECT/SHOW TABLES 补全均正常后删除临时脚本与截图。本次任务保留配置/角标/列表滚动修复后，`ReadLints` 无新增诊断，`pytest server\tests\test_database.py server\tests\test_auth_rbac.py -q`、`npm run typecheck`、`npm run build`、`npm run test:smoke` 均通过。任务范围筛选修复后复跑 `pytest server\tests\test_database.py -q`、`npm run typecheck`、`npm run build`、`npm run test:smoke` 均通过。数据库任务命名/API 文档/导航调整后，`ReadLints` 无新增诊断，`pytest server\tests\test_database.py server\tests\test_auth_rbac.py -q`、`npm run typecheck`、`npm run build`、`npm run test:smoke` 均通过。表数据快速加载优化后，`ReadLints` 无新增诊断，`pytest server\tests\test_database.py -q`、`npm run typecheck`、`npm run build`、`npm run test:smoke` 均通过。数据库任务保留时长小时/天自定义后，`ReadLints` 无新增诊断，`pytest server/tests/test_auth_rbac.py::test_system_settings_control_registration_retention_and_backup server/tests/test_database.py::test_database_metadata_query_rows_and_export` 与 `npm run typecheck` 通过。上传浮窗右上角操作和单文件取消优化后，`ReadLints` 无新增诊断，`npm run typecheck` 与 `npm run test:smoke` 通过。数据库连接搜索创建人并支持清空自动查询后，`ReadLints` 无新增诊断，`pytest server/tests/test_database.py::test_database_metadata_query_rows_and_export` 与 `npm run typecheck` 通过。

## 2026-06-15：优化数据库工作台拖拽条提示

- 数据库工作台库表树宽度拖拽条在中部增加竖向椭圆把手，椭圆内用三个竖排圆点提示可拖动调宽；样式使用现有主题 CSS 变量和 `color-mix(...)`，浅色/深色主题均跟随当前主色、边框和面板背景。
- 拖拽交互逻辑、命中区域、宽度限制、双击恢复默认宽度和 `localStorage` 持久化逻辑保持不变，本次仅调整 `web/src/styles/main.css` 的视觉层样式。

## 2026-06-15：优化数据库工作台多标签交互

- 数据库工作台右侧从固定“数据 / SQL”面板改为动态多标签页，默认不打开任何页面；点击左侧表节点会按 `database + table` 去重创建/激活表数据标签并查询数据，点击脚本节点会按脚本 ID 创建/激活 SQL 标签。
- 表数据标签内保留搜索、新增行、导入、导出、分页和排序，所有操作都按当前标签绑定的库表执行；关闭当前标签后优先激活左侧相邻标签，否则激活右侧相邻标签。
- 表数据标签工具栏提供“复制”下拉，基于当前 tab 已加载并显示的当前页 `columns + rows` 写入剪贴板，始终包含表头；`XLSX (TAB)` 输出 Tab 分割文本供 Excel 直接粘贴，`CSV` 输出逗号分割并按 CSV 规则转义，`SQL` 输出字段头注释和当前页每行 `INSERT INTO` 语句（标识符用反引号转义、值按 SQL 字面量转义）。
- 表数据标签页加载状态必须按 tab key 查找最新标签并整体替换 `workbenchTabs` 中的 tab 对象来回写 `rows/columns/pagination/loading`，不要只修改异步函数里捕获的旧 tab 引用；搜索、排序、分页和页大小变化都走 `loadTableData(tab, options)`，由该函数统一递增 `requestId` 并忽略过期响应。标签内容使用 `display-directive="if"`，只挂载当前激活页，避免多个 `NDataTable`/Monaco 同时渲染造成切换和加载卡顿。
- SQL 标签分为已保存脚本与临时 SQL：已保存脚本标题为脚本名并带 `i` 详情入口，临时脚本按“临时 SQL / 临时 SQL 2 ...”命名且无详情入口；保存临时 SQL 后会转为脚本标签并支持后续更新原脚本。
- SQL 脚本支持独立重命名：脚本树节点更多菜单和已保存脚本标签工具栏均提供“重命名脚本”，弹窗只编辑名称；保存时先 `GET /api/sql-scripts/{id}` 取当前已保存详情，再调用 `PUT /api/sql-scripts/{id}` 只替换 name，避免把编辑器里尚未保存的 SQL 内容误写回脚本。重命名成功后刷新脚本树，并同步已打开脚本标签标题和详情弹窗；同库同名仍由后端 `error.sqlScriptNameDuplicate` 拦截。
- 表结构设计器从弹窗改为标签页，新建标签显示“新增表”，编辑标签显示“编辑 - 表名”；保存后保留设计器标签并刷新库表树和已打开的数据标签，避免切换页面时丢失布局空间。
- 标签栏固定 `+` 下拉入口，提供“新建表”和“临时 SQL”；新建表优先使用当前选中库、连接默认库或第一个 schema，仍无可用库时给出提示。
- Monaco SQL 编辑器关闭默认英文右键菜单，改用项目内轻量自定义菜单，常用操作包含更改所有匹配项、剪切、复制、粘贴、全选和命令面板，文案按 `appStore.locale` 在中英文之间切换。
- 验证：`npm run typecheck` 通过，`npm run build` 通过，`git diff --check` 通过，ReadLints 无新增诊断；本次未改后端，未运行后端数据库测试。

## 2026-06-15：新增容器管理模块

- 新增后端 `server/app/modules/containers` 模块，页面权限为 `route:containers`，操作权限为 `action:container:create/read/update/delete/operate/manage_others`；模块通过 Docker SDK 连接当前部署宿主机 Docker Engine，并提供 Docker 状态、镜像、容器和容器任务 API。
- 容器管理一期只管理当前宿主机 Docker，不做多主机连接管理；连接方式由 Docker SDK 读取 `DOCKER_HOST`、TLS 环境变量或本地 socket。Linux 容器部署建议挂载 `/var/run/docker.sock` 并设置 `DOCKER_HOST=unix:///var/run/docker.sock`；Windows/macOS Docker Desktop 建议使用 Linux containers 模式，Windows 原生后端开发可用 `npipe:////./pipe/docker_engine`。
- 多用户隔离采用平台逻辑隔离：容器创建时写入 `metrix.created_by=metrix`、`metrix.owner_user_id=<user_id>`、`metrix.resource_type=container` labels，列表和操作按 labels + `manage_others` 过滤；镜像是 Docker daemon 全局资源，通过 `container_image_records` 保存归属、来源和公共/私有状态，普通用户只看自己的镜像与公共镜像。
- 安全边界：挂载 Docker socket 等同给平台容器宿主机 Docker 高权限，默认只适合可信内网部署；创建容器默认不开放 `privileged`、宿主网络、Docker socket 挂载和任意宿主目录挂载，卷挂载仅支持 Docker volume 到容器路径。
- 前端新增 `web/src/modules/containers` 模块，页面 `/containers` 分为容器、镜像和任务页签；支持容器创建、启动、停止、重启、日志查看、删除，镜像导入、导出、删除、公共/私有切换，以及导入/导出任务列表和下载。模块 i18n 已接入中英文页面文案、权限、错误码、审计和 OpenAPI 文案。
- 新增后端依赖 `docker`；本地验证使用 fake Docker client 覆盖核心 API、权限隔离、镜像归属、导入/导出任务，不依赖真实 Docker daemon。
- 容器管理页和 CRUD 示例页筛选栏使用 `table-filter-row`，搜索框、下拉框和查询按钮保持单行展示；容器状态下拉和状态标签必须走 i18n，不显示 Docker 内部英文状态值。无平台归属记录的 Docker 镜像视为公共镜像，可供所有用户查看和创建容器；普通用户不能删除这类镜像，只有管理员/`manage_others` 可删除。
- Naive UI `NSelect` 的清空/未选中状态要使用 `null`，不要用空字符串作为默认值；否则没有匹配 option 时 placeholder 不显示，会出现状态筛选框默认空白的问题。
- 系统设置新增 Docker 连接配置：`docker_connection_mode` 支持 `auto`/`manual`，`docker_host` 为手动 Host。自动模式按 `DOCKER_HOST`、`/var/run/docker.sock`、`/run/docker.sock`、Windows `npipe:////./pipe/docker_engine`、`tcp://localhost:2375`、`tcp://127.0.0.1:2375` 顺序检测并使用第一个可 ping 的 Docker Host；容器状态卡显示实际命中的 Host，不再显示 `from_env`。
- 后端 `has_permission()` 对内置 `admin` 角色直接放行；登录和 `/api/auth/me` 返回给前端的权限列表也必须为管理员返回全部有效权限，避免已有开发库管理员角色未绑定新权限时，后端允许但前端隐藏容器镜像删除/可见性等管理员操作。
- 系统设置页加载 Docker 连接配置时要对缺失/旧响应做前端兜底：`docker_connection_mode` 非 `manual` 时一律回退为 `auto`，避免旧后端或缓存响应未返回新字段时 `NSelect` 默认空白。

## 2026-06-15：第一轮代码清理和测试同步

- 修正 `server/requirements.txt` 中错误依赖名 `httpx2` 为 FastAPI `TestClient` 实际依赖的 `httpx`，避免新环境安装到不匹配的第三方包。
- 后端模块注册测试同步容器模块：`route:containers -> action:container:read`、模块列表、模型路径、OpenAPI 隐藏 tag、router 前缀和禁用模块过滤均纳入断言，确保容器模块加入后全量测试继续覆盖真实结构。
- 前端 Playwright 回归测试同步当前数据库任务和多标签工作台：数据任务接口改为 `/api/database-transfer-jobs`，排序测试提供真实任务行后点击表头；数据库工作台默认不再打开 SQL 页，测试改为通过“新建标签 -> 临时 SQL”打开编辑器；侧边栏宽度断言按当前响应式最小宽度 `220px` 校验。
- 本轮验证包含真实前后端运行和浏览器路由巡检：使用 `admin/123456` 登录后访问 `/`、`/users`、`/permissions`、`/announcements`、`/audit-logs`、`/settings`、`/tokens`、`/api-docs`、`/storage`、`/database`、`/containers`、`/demo-crud`、`/profile`，未捕获前端 error/unhandled rejection；容器页显示 Docker 已连接并能看到宿主机容器。
- 第三轮清理补齐容器任务表 i18n：镜像无标签使用 `common.none`，任务 ID 使用 `container.field.jobId`，通用 `message.operationSuccess` 加入中英文语言包；删除未使用的 `defaultNavigationOrder` 导出。脚手架生成的表格操作列同步现有规范，使用 `table-action-group`、圆形 `NButton`、`NIcon` 和标题提示。README/开发指南同步 Node 版本、前后端模块依赖约束差异和 pytest 根目录运行命令。
- 追加权限生命周期验证：通过真实后端 API 使用管理员创建临时普通用户，验证创建后可登录、禁用后登录被拒绝、重新启用后可登录、删除后登录被拒绝；验证完成后已关闭 `5173`/`8000` 端口。
- 容器管理页的容器/镜像/任务表格不要使用 Naive UI `flex-height`：在短视口或 DevTools 占用高度时，`flex-height` 可能计算出过小高度导致 tbody 不挂载，出现接口已返回但列表空白。改为普通表格渲染，并用 Playwright 覆盖 1024x520 短视口镜像列表可见性。
- 侧边栏默认排序约定：`首页`、`储存管理`、`数据库管理`、`容器管理`、业务/模板新建菜单、`系统管理`。`系统管理` 分组固定放到底部、位于 `容器管理` 下方；导航菜单/脚手架生成的新模块默认放在 `系统管理` 上方。若系统设置中已有 `navigation_order`，它会覆盖默认排序，需要同步保存为包含 `path:/containers` 且 `group:system` 最后的顺序。
- 容器日志弹窗 `ContainerLogModal` 增加“自动刷新”开关（每 3 秒轮询，关闭弹窗或卸载时清理定时器），每次刷新后日志区自动滚到底部追随最新日志。日志框必须固定高度（`height: 56vh; max-height: 440px; min-height: 260px` 加内部 `overflow:auto`），不要用 `autosize` 或 `flex:1` 撑高度，否则空日志塌缩、日志多了又把弹窗撑大。Naive UI 弹窗卡片内容是 `n-card-content`，全局 `main.css` 里用 `.container-log-modal.modal-card > .n-card-content { max-height:none; overflow:hidden }` 关掉外层滚动条，避免出现内外双滚动条；注意组件 scoped 样式无法命中 NModal 渲染的卡片根节点，这类覆盖要写在全局样式里。
- 容器日志框采用命令行终端样式：深色背景（`#11151c`）、等宽字体、按行渲染且 `white-space: pre` 不自动换行（超长行靠 `.container-log-lines { width: max-content; min-width: 100% }` + 外层 `overflow:auto` 横向滚动）。按日志级别着色：`detectLogLevel` 先解析结构化 `"level":"xxx"`/`level=xxx`，再回退到关键字匹配，映射 error 红、warn 黄、success 绿、info 蓝、debug 灰、default 浅灰。深色终端背景下默认滚动条几乎不可见，需用 `::-webkit-scrollbar*` + `scrollbar-color` 自定义横纵滚动条为深色轨道 + 亮色滑块，确保可见可用。容器日志接口 `logs()` 不加 Docker 时间戳（不传 `timestamps=True`），原样返回容器输出，与 `docker logs` 默认一致（如 sftpgo 自身输出 JSON 结构日志，含自带 `time` 字段，平台不得再叠加时间戳）。日志弹窗宽度收窄为 `min(720px, ...)`，并提供“自动换行”开关：关闭时 `white-space: pre` 不换行 + 横向滚动，开启时 `pre-wrap` + `word-break` 换行、`.container-log-lines` 宽度回到 `auto`。
- 容器日志清空（`clear_logs` + `POST /api/container-instances/{id}/clear-logs?restart=`，权限 `CONTAINER_OPERATE`）：Docker 无清空日志 API，标准方式是截断 json 日志文件。关键结论（已在 Windows Docker Desktop 实测验证）：**截断“运行中”容器的日志文件会破坏 Docker 日志读取（`docker logs` 会挂起，sparse 文件）；停止状态下截断是干净的**。因此停止态直接截断（无需重启、不提示）；运行态返回 `requires_restart=True`，前端弹窗确认后再走“停止→截断→启动”。宿主机通常无法访问守护进程日志路径（如 Docker Desktop VM 内 `/var/lib/docker/containers/...`），故截断通过“在守护进程内运行一个以目标镜像、root、挂载 `/var/lib/docker/containers`、`network none` 的辅助容器执行 `truncate -s 0`”实现（`DockerAdapter.truncate_container_log`，依赖目标镜像含 `/bin/sh`）。清空失败不破坏容器：异常时尝试把容器重新启动回原状态并报 `error.containerLogClearFailed`。
- 容器列表新增“系统占用”列（CPU%、内存使用/限制）：仅对当前页运行中的容器用 `container.stats(stream=False)` 计算，`_attach_container_stats` 用 `ThreadPoolExecutor` 并发、单个失败降级为 `-`（停止容器或 npipe 超时即显示 `-`）。CPU% 用 cpu_stats 与 precpu_stats 的 delta 公式，内存用 `usage - inactive_file/cache`。容器表操作列收窄到 88px。容器日志弹窗 tail 输入框左侧加“最近条数”标签。
- 容器列表“系统占用”“端口”列参照 1Panel 样式：系统占用渲染为 `CPU: X%` / `内存: X%` 两行（内存按 `usage/limit` 百分比，绝对值放 `title`）；端口渲染为带 `→` 图标的竖向小标签，超过 2 个折叠并显示“展开...”/“收起”（`expandedPorts` 记录展开的容器 id，预览数 `PORT_PREVIEW_COUNT=2` 以降低行高）。系统占用单元格用 `CPU`/`RAM` 两行（标签 + 等宽数值 `font-variant-numeric: tabular-nums`），并通过对应 `td` 的 `vertical-align: middle` 相对行高纵向居中（端口 `td` 仍 `vertical-align: top`）。注意 NDataTable 列 `render` 返回的 vnode 在表格组件上下文渲染，拿不到本组件 scoped 样式，且全局 `.n-data-table-td` 有 `white-space:nowrap; overflow:hidden`，因此 `.container-usage-cell`/`.container-port-list` 等单元格样式必须写在全局 `main.css`，并对含这些类的 `td` 用 `:has()` 覆盖为 `white-space:normal; overflow:visible; vertical-align:top` 才能竖向堆叠不被截断。
- 容器交互式终端（参照 1Panel）：后端 WebSocket `@instances_router.websocket("/{id}/exec")`，浏览器无法设置 WS 鉴权头，故用查询参数 `token`（`decode_access_token` + `CONTAINER_OPERATE` 权限 + 容器可见性）鉴权，并接收 `user`/`cmd`/`cols`/`rows`。`ContainerService.open_exec` 校验容器运行中后用 `DockerAdapter.create_exec`（`exec_create(tty,stdin)` + `exec_start(socket=True)` 返回 `NpipeSocket`/raw socket，已在 Windows npipe 实测可用）。桥接：后台线程 `raw.recv` → `run_coroutine_threadsafe(ws.send_bytes)`，WS 收到 JSON `{type:input|resize}` → `raw.sendall` / `api.exec_resize`。前端用 `@xterm/xterm` + `@xterm/addon-fit`，`ContainerTerminalModal` 提供用户/命令(自定义勾选+shell 下拉)表单与连接/断开，输出二进制写入 xterm、输入与 resize 走 JSON；终端动作仅对运行中的容器且有 `CONTAINER_OPERATE` 时显示。Vite dev 代理 `/api/` 需设 `ws: true` 才能转发 WebSocket（改 vite.config 后必须重启 dev server）。
- exec 终端需跨传输可用（Windows npipe / Linux/Mac unix socket / TCP）。docker-py `exec_start(socket=True)` 返回的底层 socket 形态不同：npipe 是 `NpipeSocket`、unix 是 `socket.socket`、tcp 是 `SocketIO`（其 `._sock` 才是真 socket）。`create_exec` 用 `getattr(sock, "_sock", None) or sock` 归一；WS 桥接再用 `_sock_recv`/`_sock_send` 做兜底（`recv`→`read`、`sendall`→`send`→`write`），确保三种传输都能读写。已实测 Windows npipe；unix/tcp 形态按 docker-py 内部结构兼容，建议在 Linux 部署再实测一次。
- 终端弹窗里 xterm 屏幕高度用 `clamp(160px, calc(76vh - 340px), 300px)`：正常窗口不出现外层滚动条（弹窗内容随高度自适应），仅当浏览器窗口过小时弹窗内容超过 `max-height` 才出现滚动条；扣除量 340px 是按表单+头部约 214px 实测留余量校准的。

## 2026-06-16：单窗口开发启动器

- 新增根目录 `dev.py`：单个终端窗口同时启动后端（venv python `server/main.py`，`METRIX_RELOAD=1` 自动重载）和前端（直接 `node web/node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173`，绕开 `npm.cmd` 在 Windows 上的 shell 调用问题），两边输出以 `[backend]`/`[web]` 前缀合并到当前窗口。子进程在 Windows 用 `CREATE_NEW_PROCESS_GROUP`、POSIX 用 `start_new_session`；`Ctrl+C` 触发 `KeyboardInterrupt` 后 `_stop_all()` 用 `taskkill /F /T /PID`（Windows）或 `os.killpg`（POSIX）整树关闭，避免遗留 uvicorn reload/vite 子进程占用端口。任一进程退出会自动连带关闭另一个。
- 关键坑：Windows 控制台默认 GBK，Vite 输出的 `➜`（`\u279c`）会让写日志线程抛 `UnicodeEncodeError` 并使该服务日志中断。`dev.py` 在 `main` 里 `sys.stdout.reconfigure(errors="replace")`，并在 `log()` 内对写入再做一层 `encode(encoding, "replace")` 兜底，确保日志线程不被非法字符杀死。
- `dev.bat` 改成在同一窗口调用 `.venv\Scripts\python.exe dev.py`（不再 `start` 两个新 cmd 窗口）。README 快速启动同步为推荐 `python dev.py` 单命令。

## 2026-06-16：新增脚本管理模块

- 新增前后端 `scripts` 业务模块（`server/app/modules/scripts`、`web/src/modules/scripts`），走框架自动注册；唯一核心改动是 `server/app/main.py` 的 `lifespan()` 挂载脚本运行清理循环、启动恢复（reset 残留 pending/running 为 failed）和 APScheduler 启动/停止。页面权限 `route:scripts`，操作权限 `action:script:create/read/update/delete/operate/manage_others`，本人/他人范围用 `manage_others`（与 storage/containers 一致）。所有脚本接口加 `require_web_session`、OpenAPI tag `scripts` 与 path 前缀 `/api/scripts` 隐藏（v1 不开放 API Token）。
- 执行底座复用容器模块 `clients.create_client()`（按系统设置 `docker_connection_mode`/`docker_host` 解析 Docker Host），`runtime.py` 自己组织 `client.client.containers.run(...)`：bind-mount 项目工作区到 `/workspace`、`network_mode` 取项目 none/bridge、`mem_limit`/`nano_cpus` 限额、注入包源环境变量、加 `metrix.owner_user_id`/`metrix.script_project_id`/`metrix.script_run_id` labels。**绝不 pull**，镜像缺失报 `error.scriptImageMissing`（提示去容器管理导入 tar）。运行用 detach + `logs(stream=True)` 落盘（2MB 上限）+ `threading.Timer` 超时 kill + `wait()` 取退出码，结束 remove；终端用同镜像起常驻 `sleep` 容器并 exec 桥接（复用容器 `_sock_recv/_sock_send`），WS 关闭即 `remove(force=True)`。
- 三张表 `script_projects`（name/slug/language/base_image/network_mode/run_command/env(JSON)/cpu_limit/memory_limit_mb/timeout_seconds/workspace_path/created_by）、`script_runs`（run_id 唯一/trigger/schedule_id/status/exit_code/log_path/error_code/时间戳）、`script_schedules`（trigger_type interval|cron/interval_seconds/cron_expr/enabled/last_run_at/next_run_at）。工作区目录 `runtime/script_workspaces/u<owner>/p<id>/`，运行日志 `runtime/script_runs/<run_id>.log`，均被 `.gitignore` 的 `runtime/` 覆盖。
- `runs.py` 照搬数据库 `jobs.py` 的 `ThreadPoolExecutor` 范式：提交即返回 `run_id`，worker 独立 session，并发数取系统设置 `script_run_max_workers`；启动 `reset_interrupted_runs()`，每 30 分钟 `cleanup_runs_once()` 按 `script_run_retention_hours` 清运行记录与日志。取消运行：另一会话置 `canceled` 并按 run label best-effort 删容器；worker 的 `_finalize` 必须先 `db.expire_all()` 再读 run，否则 identity-map 缓存的 `running` 会把已取消的运行覆盖成 success（关键坑，已加回归测试）。
- `scheduler.py` 用 APScheduler `BackgroundScheduler`（内存 jobstore，`max_instances=1`、`coalesce=True`）：`start_scheduler()` 在 lifespan 启动并从 `script_schedules` 重新注册 enabled 计划、回写 `next_run_at`；增删改计划同步增删 job。**调度器未运行时**（如 pytest 不进入 lifespan）`register_schedule` 仍用 trigger 直接算 `next_run_at`，保证计划 CRUD 离线可测。新增后端依赖 `apscheduler`（纯 Python，可随平台离线部署），已写入 `server/requirements.txt`。
- 系统设置新增脚本字段：`script_pip_index_url`/`script_pip_trusted_host`/`script_npm_registry`/`script_go_proxy`（默认空，运行/终端按需注入 `PIP_INDEX_URL`/`PIP_TRUSTED_HOST`/`NPM_CONFIG_REGISTRY`/`GOPROXY`）、`script_run_max_workers`（默认 2，1-16）、`script_run_retention_hours`（默认 168）、`script_workspace_quota_mb`（默认 1024）。这些是管理员设置（`SystemSettings`，非公开），前端 `api/types.ts`、`SystemSettingsView.vue` 新增「脚本」tab；顺带补齐此前缺失的 `settings.dataJobs`/`dataJobsDesc` i18n。
- 工作区文件操作（list/read/write/mkdir/rename/delete/upload）参考 storage 服务层做 `..` 逃逸检测（`_virtual_path` + `resolve()` 二次校验），写/传前按 `script_workspace_quota_mb` 校验目录配额；上传可放 wheel 到 `wheels/`，venv 约定建在 `/workspace/.venv`。
- 前端：`ScriptManageView.vue` 列表页（关键字搜索 + 语言/网络/创建人列头筛选 + 创建时间排序 + 项目弹窗，镜像下拉=本地预设高亮/任意本地镜像/可输入，选预设自动带语言与运行命令），点击名称进入 `ScriptWorkbenchView.vue` 工作台（左侧 `n-tree` 懒加载文件树、中间通用 `CodeEditor.vue`、下方 Tab：运行日志/运行历史/定时计划/环境信息 + 运行/终端入口）。脚本列表表格**不用 flex-height**（沿用容器模块教训，短视口 tbody 不挂载会空列表）。
- `CodeEditor.vue` 仅用 Monaco 内置能力，**不引入 `monaco-languageclient`、不接外部语言服务器**：JSON/TS/JS/CSS/SCSS/LESS/HTML 启用对应 `?worker`（离线即有补全/诊断），python/go/c++/sql/shell/yaml/xml/ini 等走 basic-languages 高亮，.vue 退化为 html 高亮。关键坑：`MonacoEnvironment.getWorker` 是全局单例，数据库模块的 `MonacoEditor.vue` 把它设为只返回 editor.worker；新编辑器在 `onMounted` 里重新写入完整 getWorker（json/ts/css/html + 兜底 editor.worker），保证两个编辑器并存时各自正常（SQL 编辑器只需 editor.worker，恰好是兜底）。`ScriptTerminalModal.vue` 复用 xterm + query token WebSocket 范式连 `/api/scripts/{id}/terminal`。
- 测试：`server/tests/test_scripts.py` 用假 Docker engine（`containers.run` 返回可控退出码/可阻塞的假容器、`images.list/get`，**不依赖真实 daemon**）覆盖项目 CRUD 与本人/他人范围、工作区文件操作与路径逃逸、配额、运行提交→成功→日志、运行取消、计划 CRUD（interval/cron/非法 cron）、可用镜像与 OpenAPI 隐藏 + API Token web-only。`test_auth_rbac.py` 的模块清单/权限映射/model 路径/OpenAPI 隐藏 tag 与 path 前缀/router 前缀/禁用模块过滤断言已纳入 scripts。
- 部署约束：bind-mount 的是 **Docker daemon 宿主机**路径，后端需与 daemon 同主机（或工作区目录对 daemon 可见）；Windows/Mac Docker Desktop 需该盘已共享。网络 `none`=断网、`bridge`=接入网络（同一 bridge 在内网只通内网、迁移到有外网宿主机后自动可访问外网，是「现在离线、将来联网」的统一开关）。
- 验证：`compileall -q server\app server\tests` 通过；`pytest` 58 passed（新增 7 个脚本用例）；前端 `npm run test:smoke`、`npx vue-tsc --noEmit --noUnusedLocals --noUnusedParameters`、`npm run build` 通过（Monaco json/ts/css/html worker 正常打包）。本轮未做真实 Docker 端到端核验（采用假 Docker 单测）。

## 2026-06-16：脚本预设镜像追加本地 Python

- `server/app/modules/scripts/presets.py` 的 `PRESET_IMAGES` 增加 `python:3.13.11-slim`（language=python、run_command=`python main.py`、use_venv）作为首个 Python 预设，因为部署机本地已存在该镜像；预设是否“可用”由 `runtime.py` 按本地镜像集合标记，前端 `ScriptManageView` 直接消费 API 的 `presets`，无需改前端。
- 经验坑：本机 Docker 守护进程配置了镜像代理 `127.0.0.1:7897`，该代理未运行时 `docker pull python:3.12-slim` 直接失败（`connectex: target machine actively refused`）。内网/离线环境拿不到 Docker Hub 时，应直接用本地已有镜像或走容器管理离线导入 tar，不要依赖在线 pull。
- 验证：`pytest server/tests/test_scripts.py -q` 7 passed，ReadLints 无诊断。

## 2026-06-16：脚本终端改造（嵌入式 Tab + VSCode 风格 + 环境变量）

- 终端从弹窗 `ScriptTerminalModal.vue` 改为工作台底部「终端」Tab：新增 `web/src/modules/scripts/components/ScriptTerminalPanel.vue`（内联，连接/断开 + 可选自定义命令），`ScriptWorkbenchView.vue` 的 `n-tabs` 增加 `terminal` 页签并用 `display-directive="show"` 保持挂载，切到运行日志/历史等其它页时终端连接不断；首次切到该 Tab 自动连接，离开工作台（组件卸载）才清理常驻容器。删除旧 Modal 组件与头部「终端」按钮。
- 终端像 VSCode 可用（修复上下键无历史、TAB 不补全）：根因是 exec 默认跑 `/bin/sh`（dash 无 readline）。后端 `runtime.py` 新增默认 shell 包装器 `sh -c 'cd /workspace; [ -f .venv/bin/activate ] && . .venv/bin/activate; if command -v bash; then exec bash; else exec sh; fi'`——优先 `bash`（readline 历史 + TAB 补全），无 bash（如 alpine）退回 busybox sh，并自动激活项目 venv。UI 勾选「自定义」仍可指定命令（走 shlex）。`api.py` 终端 WS 默认 `cmd` 改为空串，由后端决定默认 shell。
- 终端环境变量：`open_terminal` 改用 `terminal_environment(settings, project)` = 包源变量（PIP_INDEX_URL 等）+ 项目 `env`（JSON 解析）+ `TERM=xterm-256color` + `LANG=C.UTF-8`，作为常驻容器 environment，exec 自动继承；`TERM` 是行编辑/补全显示正确的关键。`parse_project_env` 从 `runs.py` 上移到 `runtime.py` 复用，`runs.py` 删除重复实现与不再使用的 `json` 导入。
- i18n：脚本语言包新增 `script.tab.terminal`、`script.terminalIdle`，删除随弹窗废弃的 `script.terminal`/`terminalTitle`/`terminalCommand`，`terminalHint` 更新为「默认 bash、上下键历史、TAB 补全、自动激活 venv」。
- 验证：`compileall -q server\app` 通过、`pytest server/tests/test_scripts.py` 7 passed；前端 `npm run test:smoke`、`vue-tsc --noEmit --noUnusedLocals --noUnusedParameters`、`npm run build` 通过；ReadLints 无诊断。Docker 守护进程代理未开，未做真实终端联调。

## 2026-06-16：修复 dev.py 启动竞态导致的代理报错

- 现象：`python dev.py` 启动时前端 vite 立即就绪、浏览器随即请求 `/api/install/status`、`/api/auth/me`、`/api/announcements/public`，而后端 uvicorn 仍在 “Waiting for application startup”（worker 未绑定 8000；脚本模块新增的 APScheduler 启动/模块加载/运行恢复让启动更慢），于是一串 `[vite] http proxy error ... connect ECONNREFUSED 127.0.0.1:8000`；待 “Application startup complete” 后自动恢复，属无害瞬时报错（前端对 install/status 本就有兜底）。
- 修复：`dev.py` 改为先起后端，再用 `_wait_for_backend()` 轮询 `GET http://127.0.0.1:8000/api/health`（拿到任意 HTTP 响应即视为就绪，最长 60s，期间检测到后端进程已退出则直接结束），就绪后才启动前端 vite，避免浏览器打到冷后端。`/api/health` 无需鉴权，返回 `{ok, installed}`；等待地址用 `METRIX_HOST`/`METRIX_PORT` 覆盖，默认 127.0.0.1:8000。
- 说明：uvicorn 热重载在改后端代码触发 worker 重启的短暂窗口仍可能有个别 proxy error，属热重载固有现象，不处理。

## 2026-06-16：脚本管理增强（共享/运行入口/压缩包/多终端/导航置底）

- 导航永久置底：`web/src/router/page-registry.ts` 的 `buildMenuItems` 末尾用 `pinSystemGroupLast()` 强制把 `group:system`（系统管理）排到最后，无论模块 `menu.order` 或系统设置 `navigation_order` 如何；已写注释说明这是永久约定，新增业务模块默认在其上方。
- 脚本共享：`script_projects` 新增 `is_shared`（模块 `table_syncs` 给存量库补列）。可见性/权限拆分为「读+运行」与「编辑」两级：`ScriptProjectService.get_project` 允许 创建者/共享/`manage_others`（列表可见、运行、看运行历史/日志、取消）；新增 `get_manageable_project` 仅 创建者/管理员（改配置、改/传/删文件、终端、建计划）。`runs._get_visible_run` 同步允许共享；repository 列表对非管理员返回「本人 + 共享」。前端列表对共享他人项目隐藏「管理/编辑/删除」（名称不可点进工作台），仅显示运行/运行历史。
- 列表操作列：运行（无 `run_command` 时禁用）、运行历史 为独立圆形图标；其余「管理/编辑/删除」收进 hover「更多」下拉（仅可管理者显示）。运行历史用新组件 `ScriptRunHistoryModal.vue`（运行清单→点查看日志，轮询、可取消）。新建脚本弹窗加共享开关与可选「上传代码」（创建后上传到工作区根，压缩包自动解压）。
- 压缩包上传自动解压：`services.upload_file` 检测 `.zip/.rar/.7z`→`_extract_archive`：先解压到临时目录，再逐文件经 `_safe_target` 拷回工作区（防 zip-slip），按配额校验解压后大小。ZIP 用 stdlib，7Z 用 `py7zr`，RAR 用 `rarfile`（依赖服务器 unrar/7z，缺失报 `error.scriptArchiveToolMissing`，损坏报 `error.scriptArchiveInvalid`）；新增审计 `script.archive_extract`。新增依赖 `py7zr`、`rarfile`（写入 `server/requirements.txt`）。
- 超时 0=不限：模型/schema 默认 `timeout_seconds=0`（schema `ge=0`），`runtime.run_script` 仅在 `>0` 时启动超时 kill 定时器。前端表单默认 0、min 0、提示「0=不限」。
- 网络文案：`script.network.bridge`「接入网络」→「接入」、`none`「断网」→「断开」（en: Connected/Disconnected）。
- 工作台：文件侧栏新增「折叠全部」按钮（清空 `expandedKeys`）；底部面板终端改为多终端——`+` 新建终端标签，新增终端标签右侧带关闭图标，默认第一个终端与 运行日志/运行历史/定时计划/环境信息 标签不可关闭（`display-directive="show"` 保持连接）。去掉终端面板的 bash/venv 提示文案；终端仍默认优先 bash + 自动激活 `/workspace/.venv`。
- i18n 修复：`script.run` 原是对象（与状态对象重名导致运行按钮显示原始 key `script.run`），重构为 `script.run="运行"` 字符串 + `script.runStatus.*`（状态）+ `script.runCancel`/`script.runViewLog`；新增 shared/sharedHint/timeoutHint/uploadCode/chooseFile/uploadCodeHint/historyTitle/collapseAll/terminalAdd 与 archive 错误码、`archive_extract` 审计文案（中英）。
- 测试：`test_scripts.py` 新增 ZIP 解压用例与共享「可见/可运行/不可编辑」用例；`pytest server/tests/test_scripts.py` 9 passed。
- 验证：`compileall -q server\app` 通过；`pytest test_scripts.py test_auth_rbac.py` 44 passed；前端 `npm run test:smoke`、`vue-tsc --noEmit --noUnusedLocals --noUnusedParameters`、`npm run build` 通过；ReadLints 无诊断。RAR 解压依赖服务器端 unrar/7z，本机未做真实 RAR/7Z 联调。

## 2026-06-17：运行历史弹窗细节修正

- `ScriptRunHistoryModal` 表格加 `:scroll-x="560"` 让横向滚动条正常出现，操作列改 `fixed:"right"` 始终可见；创建时间列客户端可排序（`sorter: localeCompare(created_at)` + `defaultSortOrder:"descend"`，ISO 字符串按字典序即时间序）；刷新按钮从工具栏改为右上角图标按钮，放进 `n-modal` 的 `#header-extra` 插槽（在关闭按钮左侧）。运行列表保留 `max-height:240`、日志 `<pre>` `max-height:220 + overflow:auto`，保证运行多/日志多时纵向滚动正常。弹窗宽度通过全局 `web/src/styles/main.css` 的 `.script-history-modal.modal-card { width: min(720px, calc(100vw - 32px)) }` 加宽到 720px（参照 `.container-log-modal`；scoped 样式命不中 Teleport 出去的卡片根，这类宽度覆盖必须写全局）。
- 运行历史操作列从 120 收窄到 80（取消按钮也改成图标按钮），其余列拓宽（触发100/状态110/退出码100/创建时间220）以在 720px 弹窗内更均衡。
- 列表「运行」按钮点击后保持 loading 旋转直到运行**真正结束**：`ScriptManageView.runFromList` 提交后用 `getScriptRun(run_id)` 每 2s 轮询，直到 success/failed/timeout/canceled 才从 `runningIds` 移除；按钮 `loading: isRunning(row.id)`、`disabled` 同时含运行中，避免重复提交（用 `ref<number[]>` 跟踪运行中项目 id，保证表格重渲染）。

## 2026-06-17：脚本/容器列表横向滚动条置底（对齐数据库列表）

- 现象：脚本列表、容器列表的 `page-data-table` 没加 `flex-height`，Naive 表按内容高度渲染，横向滚动条落在数据行下方而非卡片底部；数据库列表加了 `flex-height` 所以滚动条贴卡片底。
- 脚本列表：`ScriptManageView` 的表加 `flex-height`（与数据库列表一致；该表是 `table-page-card` 直接子节点，flex 链天然成立，安全）。
- 容器列表三张表（容器/镜像/任务）在 `n-tabs` 内——之前因缺 flex 链用 `flex-height` 会算出过小高度导致空列表，才移除过 `flex-height`。本次给容器 `n-tabs` 加 `class="container-tabs"`，并在全局 `main.css` 补 flex 链（`.container-tabs` 及其 `.n-tabs-pane-wrapper`/`.n-tab-pane` 均 `display:flex;flex-direction:column;min-height:0;flex:1 1 auto`，参照 `.database-main` 工作台做法），再给三张表加 `flex-height`，并移除 `animated`（避免过渡包装层干扰 flex 链）。横向滚动条现固定在卡片底部。
- 验证：`vue-tsc`、`build` 通过，ReadLints 无诊断。未对用户正在运行的实例跑 Playwright（会触发安装/登录流程改其数据）；短视口空列表风险已用 flex 链从根因规避（与数据库列表/工作台同款），如需严格复核可在干净环境跑 `npm run test:regression`（含 1024x520 镜像列表用例）。

## 2026-06-17：修复脚本设置字段翻译路径

- 现象：系统设置「脚本」tab 中 `field.scriptRunMaxWorkers`、`field.scriptPipIndexUrl` 等显示为原始 key，硬刷新无效。
- 根因：这些脚本设置字段翻译之前被加到了后面的嵌套 `auditLog.detail.field` 对象里，而设置页使用的是顶层 `field.*` 路径；因此 `t("field.scriptRunMaxWorkers")` 命不中。
- 修复：在 `web/src/i18n/locales/zh-CN.json` 与 `en-US.json` 的顶层 `field` 对象补齐 `scriptRunMaxWorkers`、`scriptRunRetentionHours`、`scriptWorkspaceQuotaMb`、`scriptPipIndexUrl`、`scriptPipTrustedHost`、`scriptNpmRegistry`、`scriptGoProxy`。本轮按用户要求只修改并提交，不运行测试。

## 2026-06-17：脚本运行限制支持 0 表示不限制

- 系统设置中的 `script_run_max_workers`、`script_run_retention_hours`、`script_workspace_quota_mb` 均支持 `0` 作为“不限制”。后端 schema 从 `ge=1` 改为 `ge=0`，设置读取 `_parse_int` 最小值也改为 0；前端 `SystemSettingsView` 对应 `NInputNumber` 最小值改为 0，并新增中英文提示 `settings.scriptZeroUnlimited`。
- 并发数：`script_run_max_workers=0` 时不再使用固定大小线程池，而是每次运行直接起独立 daemon 线程执行 `_run_job`，表示平台不限制同时运行数量；大于 0 时继续复用固定 `ThreadPoolExecutor`。
- 运行记录保留：`script_run_retention_hours=0` 时 `cleanup_runs_once()` 直接返回，不删除运行记录、日志文件或孤儿日志。
- 工作区配额：`script_workspace_quota_mb=0` 时 `_ensure_quota()` 直接返回，不限制工作区大小。
- 开发指南同步更新脚本调度与限制说明。本轮按用户要求只修改并提交，不运行测试。

## 2026-06-17：脚本编辑器接入 Monaco 内置候选词

- `web/src/modules/scripts/components/CodeEditor.vue` 新增静态补全 provider，不接 LSP、不手写关键字表，而是像数据库 SQL 编辑器一样直接复用 `monaco-editor/esm/vs/basic-languages/*/*.js` 导出的 `language` 定义（`keywords`、`typeKeywords`、`builtins`、`builtinFunctions`、`builtinVariables`、`tags`、`attributes`、`operators`）生成候选项。
- 覆盖语言：python、go、cpp、shell、sql、yaml、xml、ini、javascript、typescript、css/scss/less、html。JSON/TS/JS/CSS/HTML 的 worker 仍保持原有内置语言服务；静态 provider 只是补充候选，不引入 `monaco-languageclient` 或外部语言服务器。
- `CodeEditor` 开启 `suggestOnTriggerCharacters` 与 `quickSuggestions`，触发字符包括空格、`.`、`:`、`<`、`-`、`$`、`/`；卸载时统一 dispose completion providers。
- `web/src/vite-env.d.ts` 增加 Monaco basic-language 模块通用声明，避免 TS 无法识别这些 `.js` 语言定义模块。本轮按用户要求只修改并提交，不运行测试。

## 2026-06-17：脚本编辑器支持自动保存

- `ScriptWorkbenchView` 编辑器工具栏新增「自动保存」开关，状态用 `localStorage` key `appKey("scriptWorkbench.autoSave")` 持久化。
- 开启后监听 `currentContent`，内容变化 800ms 防抖调用 `writeScriptFile` 保存当前文件；自动保存不弹成功提示，只在失败时沿用 `showError` 提示。手动「保存」仍保留成功提示。
- 切换文件、删除当前文件、组件卸载时会清理待执行的自动保存定时器；读取文件时用 `skipNextContentWatch` 跳过首次内容回填，避免刚打开文件就误触发保存。
- 补充脚本模块中英文 `script.autoSave` 文案。本轮按用户要求只修改并提交，不运行测试。

## 2026-06-18：数据库 run-script 增加可选单连接会话模式

- 背景：`run-script` 默认逐语句执行——`ExternalDatabase.execute_write` 每条都 `engine.begin()` 新开连接，且引擎用 `NullPool`（连接用完即弃），所以 `CREATE TEMPORARY TABLE`、`SET SESSION/GLOBAL` 等会话状态跨不了语句。带临时表的脚本（如 CapacityReport 报表）因此无法整段跑通。
- 改动（向后兼容，默认行为不变）：
  - `schemas.py`：`RunScriptRequest` 新增 `single_session: bool = False`。
  - `engines.py`：`ExternalDatabase` 新增 `session_connection()`（开一条 `isolation_level="AUTOCOMMIT"` 的连接并在整段脚本复用）、`execute_sql_on(conn, ...)`、`execute_write_on(conn, ...)`。
  - `services.py`：`run_script` 当 `single_session=True` 时用 `session_connection()` 取得单连接、所有语句在该连接上执行（`nullcontext(None)` 兜底保持默认逐语句路径）；逐语句结果/报错/`stop_on_error` 语义不变。
- 选 AUTOCOMMIT 而非单事务：MySQL DDL 会隐式提交，整段「一个事务回滚」做不到也无意义；这里要的是「同一条连接」让临时表/会话变量存活，AUTOCOMMIT 下每条即时提交、连接不断开，临时表照常跨语句。临时表连接私有、会话结束自动清理、并发安全。
- 配套（CapacityReport 平台脚本，位于 `temp/`，已被 `.gitignore`，不入库）：`report_script.sql` 改回临时表版本（仅 `SET GLOBAL`→`SET SESSION`）；`platform_client.run_script` 支持 `single_session`，`main.py` 调用报表 SQL 时传 `single_session=True`。
- 本轮按用户要求只修改并提交，不运行测试。

## 2026-06-19：用查询(read)权限替代 route 页面权限

- 目标：导航/进入页面的网关从独立的 `route:<page>` 改为该模块资源的 `action:<resource>:read`（查询权限）；角色编辑器里勾任意操作自动带上查询；首页用一条 `action:dashboard:read` 表示；新角色默认带首页；彻底退役 `route:*` 机制并清理库中遗留行（含此前未翻译的 `route:database_jobs`）。
- 背景：旧模型导航只认 `route:<page>`，而资源操作权限不会反推页面权限，导致「授予了操作权限但导航不出现」；且「页面」分组与同名资源分组并存、易混。本轮直接退役 route 机制，让「查询权限=能看列表+能进页面+出导航」。
- 后端：
  - `core/module.py` 删除 `route_code`/`PagePermissionSpec`/`page_permission` 及 `AppModule.page_permissions` 字段；`modules/registry.py` 删除 `get_page_permission_specs` 与页面权限唯一性校验。
  - `core/permissions.py` 移除全部 `ROUTE_*`/`ROUTE_READ_PERMISSIONS`/页面 seed；新增 `DASHBOARD_READ`；`PERMISSION_SEEDS` 仅资源权限；`expand_permissions` 改为「含任意 `action:<res>:<verb>` 即补 `action:<res>:read`」（页面网关兜底，保证授予能力即可进页面）。
  - `modules/core.py` 移除 `page_permissions`，新增 `dashboard` 资源（仅 `read`，组 `dashboard`，排在编辑器最前）；scripts/containers/database/storage/demo_crud 各 `__init__.py` 移除 `page_permission`/`page_permissions`（保留各自 `*_READ` 常量，仍被 `api.py` 守卫使用）。
  - `api/dashboard.py` 守卫改 `DASHBOARD_READ`；`db/init.py` 默认 user 角色改 `[DASHBOARD_READ]`，新增 `_delete_legacy_route_permissions`（删除 `code LIKE 'route:%'` 行并清角色关联）；`services/roles.py` `create_role` 默认给新角色赋 `action:dashboard:read`。
- 前端：各模块 `index.ts` 的 `page.permission` 改 `actionPermission("<resource>","read")`（scripts→script、containers→container、demo_crud→demo_item、core 八页对应各自资源）；`modules/types.ts` 删除 `routePermission`；`views/PermissionView.vue` 取消隐藏 `:read` 的过滤（显示查询项），勾任意动作自动补勾同资源查询、取消查询连带取消该资源其它动作；`config/permissions.ts` 的 DEPRECATED 收敛为 `action:announcement:operate`。
- i18n：核心删 `permission.group.page` 与 `permission.route:*`，新增 `permission.group.dashboard` 与 `permission.action:dashboard:read`（查看首页/View dashboard）；各模块删 `permission.route:<x>` 标签（保留菜单标题 `route.<x>`）。
- 脚手架/文档/测试：`scripts/create-module.mjs` 模板改为 read 即页面权限（index/init/生成测试/i18n 去 route）；`DEVELOPMENT_GUIDE.md` 更新前后端示例与「权限 code 规则」；`server/tests/test_auth_rbac.py` 全量改写 route 断言为新模型。
- 生效：现有角色无需重勾——含模块操作权限的角色经 `expand_permissions` 自动获得对应 read（页面），刷新/重登即出现导航；旧 `route:*` 行在应用下次初始化时清理。验证：后端改动文件 `py_compile` 通过、`server/app` 内无残留 route 机制引用；前端 `npm run typecheck` 通过；i18n JSON 全部可解析；脚手架 `node --check` 通过。本轮按用户要求只修改并提交，不运行 pytest。

## 2026-06-19：工作区文件树接入离线 vscode-icons 类型图标

- 需求：脚本工作台「工作区文件」树像 VSCode 那样按文件类型显示图标、文件夹按类型显示（JetBrains 风格），且内网离线可用。
- 方案：`unplugin-icons` + `@iconify-json/vscode-icons`（均 devDependencies，仅构建期）；按代码静态引用的图标名构建期 tree-shake，仅约 53 个 SVG 进入脚本模块分包（不打整套约 3.7MB）。未引入 `vscode-icons-js`/`@iconify/vue`，改用自维护映射表（`web/src/modules/scripts/utils/fileIcons.ts`，导出 `getFileIcon`/`getFolderIcon`）以便静态分析按需打包。
- 覆盖：常见源码/配置扩展名（py/go/cpp/c/h/js/ts/tsx/jsx/vue/json/yaml/xml/ini/toml/md/sh/html/css/scss/less/sql/txt/dockerfile/env/gitignore 等）+ 无扩展名 `Dockerfile`，识别不到回退 `default-file`；文件夹 src/images/img/assets/test(s)/docs/dist/build/public/config/.git/node_modules/.vscode 分类图标，展开用 `-opened` 变体，其余回退 `default-folder(-opened)`。少量回退：`.lock`→默认文件、`.csv`→文本、`assets`→`folder-type-asset`、`build`→复用 `dist`。
- 集成：`web/src/modules/scripts/views/ScriptWorkbenchView.vue` 给 `n-tree` 加 `:render-prefix`（`renderTreePrefix`）与对齐样式；`web/vite.config.ts` 接 `Icons({ compiler: "vue3", autoInstall: false })`（离线、不联网自动装）；`web/tsconfig.json` 的 `types` 增加 `unplugin-icons/types/vue` 让 `~icons/*` 通过类型检查。
- 顺带修复：`web/src/vite-env.d.ts` 中 monaco `basic-languages/*/*.js` 用了 TS 不支持的双通配模块声明，导致 `CodeEditor.vue` 类型检查 TS7016、`npm run build` 阻断；改为单通配 `*` 后 `typecheck`/`build` 通过。
- 验证：`npm run typecheck`、`npm run build` 通过，图标随脚本分包按需打包。本轮按用户要求只修改并提交，不推送。

## 2026-06-19：脚本工作台 IDE 交互增强（VSCode 化）

- 需求：脚本工作台对齐 VSCode 体验——工作区文件树右键菜单（复制/粘贴/重命名/删除）、拖拽移动、编辑器多标签、底部面板默认终端。复制/粘贴/移动参考储存管理（`storage`）的剪贴板与后端能力。
- 后端（对齐 `storage` 的安全校验与权限，编辑类操作走 `get_manageable_project`=创建者/管理员）：
  - `server/app/modules/scripts/schemas.py` 新增 `ScriptConflictPolicy`(error/overwrite/rename) 与 `ScriptEntryTransferRequest`(paths/target_dir/conflict_policy)。
  - `server/app/modules/scripts/services.py` 新增 `ScriptProjectService.copy_entries`/`move_entries` 与 `_resolve_destination`，以及模块级 `_transfer_sources`/`_ensure_not_nested`/`_unique_destination`/`_split_name`/`_path_size`/`_remove_path`；复制用 `shutil.copytree/copyfile` 并按配额校验、移动用 `shutil.move`（同目录为 no-op），全部经 `_safe_target` 防越界/zip-slip，冲突 rename 生成「X - copy」、overwrite 先删后写、error 抛 `error.scriptEntryExists`。
  - `server/app/modules/scripts/api.py` 新增 `POST /{project_id}/copy`、`/{project_id}/move`（`SCRIPT_OPERATE` 权限），返回 `list[ScriptFileEntry]`。新增审计 `script.file_copy`/`script.file_move`（i18n 已补）。
- 前端：
  - `web/src/modules/scripts/api.ts` 新增 `ScriptConflictPolicy`/`ScriptEntryTransferPayload` 与 `copyScriptEntries`/`moveScriptEntries`。
  - `web/src/modules/scripts/views/ScriptWorkbenchView.vue` 重构：单文件 `currentPath/currentContent` 模型改为「打开文件列表 `openFiles` + 活动标签 `activePath`」；编辑器顶部用 `n-tabs(type=card)` + `n-tab(closable, :tab 渲染函数=文件图标+名+脏点)` 作纯标签栏（`showPane=!tabChildren.length`，无空面板），下方仍是单个共享 `CodeEditor`（避免多 Monaco 实例导致补全重复注册）。标签右键用 `n-dropdown(trigger=manual)` 提供 关闭/关闭其他/关闭左侧/关闭右侧/关闭全部；自动保存按活动文件防抖（沿用 `AUTO_SAVE_KEY`）。
  - 文件树：`n-tree` 加 `:node-props` 绑定 `contextmenu` 打开 `n-dropdown(trigger=manual)`（复制/粘贴/重命名/删除，粘贴在剪贴板有内容时才可用、无取消项）；剪贴板 `clipboard` 记住源路径、复制后保留可多次粘贴；粘贴用 `conflict_policy=rename` 粘到选中目录或选中文件所在目录。移动改用 `draggable` + `@drop`（拖到文件夹即移动，`conflict_policy=error`，同目录/拖入自身或子目录均拦截），右键菜单不含「移动」。删除走确认弹窗、复用 `deleteScriptEntry`；重命名复用 `renameScriptEntry`。
  - 树刷新改为局部/保留展开：`refreshDir`(目标目录在树中已加载则就地重载其 children，否则 `reloadTreePreservingExpansion` 递归重载已展开子树并保留 `expandedKeys`)，新建/上传/粘贴/移动/重命名/删除后只刷新受影响目录；刷新按钮也改为保留展开。删除/重命名/移动会同步关闭或改写受影响的打开标签（`closeTabsUnder`/`syncPathsAfterMove`）。
  - 底部面板默认 `activeTab` 由 `log` 改为 `terminal-1`（终端面板 `watch(active)` 无 `immediate`，挂载时不会自动连容器，仅展示空闲态）。
- i18n：`web/src/modules/scripts/i18n/{zh-CN,en-US}.json` 补 `script.paste/rename/copyPrepared/pasted/moved/renamed/moveInvalidTarget` 与 `script.editorTab.{close,closeOthers,closeLeft,closeRight,closeAll}`，以及审计 `file_copy`/`file_move`。
- 关键取舍：编辑器用单一共享编辑器实例（非每标签一个 Monaco），切换标签交换内容/语言；切换标签会取消上一个文件的待保存防抖（与原单文件逻辑一致，未引入 focus-out 即时保存）；拖拽移动到根目录需拖到根级节点的前/后（无独立根节点）。
- 验证：`npm run typecheck`、`npm run build` 通过；改动 py 文件 `python -m py_compile` 通过；改动文件 ReadLints 无报错。本轮按用户要求只修改并提交，不推送；与本任务无关的 `dev.bat` 不纳入提交。

## 2026-06-19：脚本工作台编辑页体验改进

- 需求：进入工作台首个终端自动连接、自动保存默认开启、编辑器工具栏精简、底部面板可折叠、Markdown 源代码/预览切换。本轮只动脚本模块前端与其 i18n、记忆文档。
- 首个终端自动连接：`components/ScriptTerminalPanel.vue` 新增 `autoConnect` prop（默认 false），在 `onMounted` 内当 `autoConnect && project && !autoConnected` 时直接 `connect()`；其余终端仍走原 `watch(active)` 的按需连接。`ScriptWorkbenchView` 给终端面板传 `:auto-connect="!term.closable"`（仅默认的 `terminal-1` 自动连）。终端 pane 用 `display-directive="show"` 故工作台挂载即 mount，`activeTab` 默认就是 `terminal-1`（可见、有尺寸），`fit()` 正常。
- 自动保存默认开启：`autoSaveEnabled` 初值由 `=== "1"` 改为 `localStorage.getItem(AUTO_SAVE_KEY) !== "0"`——无存储值时默认开启，只有用户显式关过（存 "0"）才保持关闭，尊重历史选择。
- 工具栏调整（`script-editor-bar` 的 actions 区）：删除原「删除」按钮（文件删除仍可从左侧文件树右键菜单 `delete`→`deletePath` 进行），同时移除仅服务于该按钮的 `deleteActive()`；「保存」按钮移到「自动保存」开关左侧，并加 `v-if="!autoSaveEnabled"`——开启自动保存时隐藏保存按钮，关闭时显示。
- 底部面板折叠：新增 `panelCollapsed`（`localStorage` key `appKey("scriptWorkbench.panelCollapsed")` 记忆）与 `togglePanel()`；在 n-tabs `#suffix` 的「新建终端」旁加一个 chevron 图标按钮（展开显示 `ChevronDown20Regular`、收起显示 `ChevronUp20Regular`）。收起用 naive-ui NTabs 公开属性 `:pane-wrapper-style="panelCollapsed ? 'display: none' : undefined"` 隐藏内容容器（类 `n-tabs-pane-wrapper`），`.script-panel` 加 `.script-panel-collapsed`（`flex:0 0 auto;height:auto;min-height:0`）让 `.script-editor-host`(flex:1) 占满。展开时 `nextTick` 派发一次 `window resize`（Monaco 用 automaticLayout 自适应；xterm 经其 ResizeObserver 在容器由 0 变可见时自动 `fit`）。
- Markdown 预览：静态引入 `markdown-it`（`new MarkdownIt({ html:false, linkify:true, breaks:false })`，`html:false` 转义原始 HTML 故 `v-html` 安全、无需 DOMPurify）。`languageForPath` 增加 `markdown:"markdown"`（`.markdown` 同 `.md`）；`isActiveMarkdown` 以 `activeFile.language === "markdown"` 判断，仅 md 文件在右上角显示 `n-radio-group`(源代码/预览，复用既有 NRadioButton/NRadioGroup)。`showMarkdownPreview` 为真时编辑器宿主渲染 `.script-markdown-preview`(absolute inset:0、滚动、`:deep()` 标题/代码/引用/表格样式) 替代 `CodeEditor`。`setActive` 切换文件时把 `viewMode` 复位为 `source`（打开新文件回到源代码视图）。
- 依赖：`web/package.json` 新增 `markdown-it`(^14.2.0) 依赖与 `@types/markdown-it`(^14.1.2) devDependency；构建后 markdown-it 打入脚本分包。注：`node_modules` 里虽有 `marked`，但它只是未声明的传递依赖（不在 package.json），按需求采用并显式声明 `markdown-it`。
- i18n：`web/src/modules/scripts/i18n/{zh-CN,en-US}.json` 的 `script` 下新增 `panelCollapse`/`panelExpand`/`markdownSource`/`markdownPreview`。
- 验证：`npm run typecheck`、`npm run build` 通过；改动文件 ReadLints 无报错。本轮按用户要求只修改并提交，不推送；与本任务无关的 `server/app/core/permissions.py`、`web/src/config/permissions.ts`、`dev.bat` 改动保持原样不纳入提交。

## 2026-06-19：脚本工作台编辑页体验改进（后续反馈修复）

- 需求：工具栏并入「运行」行、底部新增「配置」标签编辑 run_command、运行按钮按 run_command 禁用/提示、修复折叠失效与终端外层溢出。仍只动脚本模块前端与 i18n、记忆文档。
- 工具栏并入运行行：删除独立的 `.script-editor-bar`（少占一行竖向空间），把「文件路径 + Markdown 源代码/预览切换 + 保存（`v-if="!autoSaveEnabled"`）+ 自动保存开关」全部移入头部 `.script-workbench-actions`（即「运行」按钮所在行），用 `<template v-if="activeFile">` 包裹；保存仍在自动保存左侧、随开关显隐。路径用 `.script-editor-path`（`max-width:260px` + 省略号）简洁显示工作区相对路径。清理了不再使用的 `.script-editor-bar`/`.script-editor-actions` 样式。
- 「配置」标签：tabs 顺序 运行日志/运行历史/定时计划/环境信息/配置/终端（插在终端左侧）。内容为 `run_command` 输入 + 保存按钮（`SCRIPT_UPDATE` 权限）。保存复用 `updateScript(project.id, payload)`（`ScriptProjectPayload` 需全字段，故用 `props.project` 其余字段 + 新 `run_command` 组装）；成功后同步本地 `runCommand`，使运行按钮禁用/提示即时生效。新增本地状态 `runCommand`(生效值，驱动运行按钮) 与 `configRunCommand`(配置页草稿)，进入配置标签时 `handleTabChange` 把草稿重置为当前生效值。
- 运行按钮禁用/提示：`:disabled="!runCommand"`、`:title="runCommand || t('script.runCommandMissing')"`（`PermissionButton` 用 `v-bind="$attrs"` 透传到 n-button，title 作原生 tooltip 显示实际运行命令，明确「运行」执行的是配置命令而非当前编辑文件）。
- 折叠失效根因与修复：naive-ui NTabs 仅在 `animated=true` 时才渲染 `.n-tabs-pane-wrapper`（见 `Tabs.mjs`），当前未开 `animated` 故该容器根本不存在，上一轮的 `:pane-wrapper-style="display:none"` 完全无效。改为去掉该绑定，纯用面板类驱动：`.script-panel-collapsed :deep(.n-tab-pane){display:none}` 直接隐藏所有面板内容、`:deep(.n-tabs){flex:0 0 auto}` 收缩到仅 tab 栏，配合 `.script-panel-collapsed{flex:0 0 auto;height:auto;min-height:0}` 让编辑器占满。由 `:class` 响应式驱动，点击切换立即生效。
- 终端外层溢出修复：根因是 `.script-terminal-screen` 固定 `height:clamp(160px,28vh,340px)` 常高于 `.script-panel`(38%/min220px) 的可用空间，导致面板 `overflow:auto` 出现外层滚动条而 xterm 自身不滚。改为：`.script-panel` 改 `overflow:hidden`，并建立 flex 高度链——`:deep(.n-tabs){flex:1;min-height:0}`、`:deep(.n-tabs>.n-tabs-nav){flex:0 0 auto}`、`:deep(.n-tab-pane){flex:1;min-height:0;overflow:auto}`（非终端页内部自带 max-height/滚动）；`ScriptTerminalPanel` 的 `.script-terminal` 改 `height:100%;overflow:hidden`、`.script-terminal-screen` 改 `flex:1;min-height:0`，使终端精确填充其面板高度、不溢出，xterm 经 FitAddon 适配高度并由 `.xterm-viewport` 自身纵向滚动。
- 终端 fit 时机：除原有 `watch(active)`(切到终端) 与 `ResizeObserver`(容器尺寸变)，新增 `window` `resize` 监听（active+connected 时 `fit()`+`sendResize()`）；面板展开仍由 `togglePanel` 派发 `window resize` 触发，覆盖「切到终端/面板展开/窗口 resize」三种 fit 场景。
- i18n：`script.tab.config`（配置/Config）、`script.configHint`（配置运行命令提示）；运行按钮空命令提示复用既有 `script.runCommandMissing`。
- 验证：`npm run typecheck`、`npm run build` 通过；改动文件 ReadLints 无报错。本轮无新增依赖。只修改并提交，不推送；与本任务无关的 `server/app/core/permissions.py`、`web/src/config/permissions.ts`、`dev.bat` 保持原样不纳入提交。

## 2026-06-19：脚本工作台修复拖拽到根目录 + 关闭未保存文件提示

- 拖拽到根目录修复：`ScriptWorkbenchView.handleTreeDrop` 原 `targetDir` 用 `nodeDir(node)`（文件夹→自身），导致把文件拖到顶层节点的 before/after 时落到该文件夹而非根目录，无法移到根。改为：`inside` 文件夹→该文件夹；其余（before/after 或落在文件上）→ `parentPath(node.key)`（成为该节点的同级目录），顶层节点的 parent 即 `/`，从而支持移动到工作区根目录。后端 `move_entries` 经 `_virtual_path("/")` 已正确解析根目录，无需改动。
- 关闭未保存文件提示：仅在「自动保存关闭」时生效。脏判定复用既有 `content !== savedContent`（抽出 `isDirty`）。新增 `requestCloseTab`（单标签）与 `requestCloseTabs`（关闭其他/左/右/全部的批量场景）；关闭含未保存修改的文件时弹 `dialog.warning`：保存并关闭 / 不保存 / 取消（点 X 或遮罩=取消、不关闭）。编辑器标签 `@close` 与右键菜单各关闭项均改走 request 版本；删除文件仍走原有删除确认、不重复提示。
- i18n：新增 `script.unsavedTitle/unsavedConfirm/unsavedConfirmMulti/saveAndClose/closeWithoutSaving`（中英文同步）。
- 验证：改动文件 ReadLints 无报错。只修改并提交，不推送；无关的权限文件与 `dev.bat` 不纳入提交。

## 2026-06-19：登录会话有效期改为系统设置可配（默认12小时，0=永不过期）

- 背景：登录 token 有效期原写死在 `core/config.py` 的 `token_expire_minutes = 12*60`。改为系统设置项 `session_token_expire_hours`，默认 12，`0` 表示永不过期。
- 后端：
  - `schemas/settings.py`：`SystemSettings` 与 `SystemSettingsUpdate` 新增 `session_token_expire_hours: int = Field(default=12, ge=0, le=8760)`。
  - `services/settings.py`：新增 `SETTING_SESSION_TOKEN_EXPIRE_HOURS`、`DEFAULT_SESSION_TOKEN_EXPIRE_HOURS=12`，并在 `_default_settings`/`_merged_settings`(`_parse_int` min=0,max=8760)/`update_settings.set_many`/`_settings_snapshot` 全链路接入。
  - `core/security.py`：`create_access_token(subject, expire_minutes=None)`——`minutes<=0` 时不写 `exp`（永不过期）；`decode_access_token` 改为「无 `exp` 声明则跳过过期校验」。`config.token_expire_minutes` 仅作 `expire_minutes=None` 时的兜底默认。
  - `services/auth.py` 登录：`expire_minutes = SettingService(db).get_settings().session_token_expire_hours * 60`，传入 `create_access_token`。
  - 仅影响新签发的 token；已签发带 `exp` 的旧 token 不受影响。无需数据库迁移（键值设置缺省回退默认）。
- 前端：`api/types.ts` 的 `SystemSettings` 加 `session_token_expire_hours`（`SystemSettingsUpdate` 由 `Omit<...>` 自动包含）；`SystemSettingsView`「基础」tab 新增「登录有效期(小时)」`n-input-number`(min0/max8760) + 提示，并接入 form 默认值/`buildPayload`/`applySettings`；中英文新增 `field.sessionTokenExpireHours`、`settings.sessionExpireHelp`。
- 验证：改动文件 ReadLints 无报错。只修改并提交，不推送。

## 2026-06-20：修复核心 OpenAPI 文档翻译回退

- 背景：API 文档页通过 `openapi.operation.<operationId>.summary/description` 覆盖后端 OpenAPI 文案；后端已统一使用短 operationId（如 `audit.list_audit_logs`），但核心公共语言包仍保留旧 FastAPI 自动 ID（如 `list_audit_logs_api_audit_logs_get`），导致首页、公告、操作日志接口回退显示英文 summary。
- 前端：更新 `web/src/i18n/locales/{zh-CN,en-US}.json` 的核心 OpenAPI operation key，覆盖 `dashboard.summary`、`announcements.*`、`audit.*`；补充日志来源参数说明和首页/公告/日志常见响应字段说明；公告“指定权限”输入提示从旧 `route:users` 改为 `action:user:read`。
- 约定：后续新增或调整 API 文档翻译时，以运行时 `/openapi.json` 中的短 `operationId` 为准；模块语言包继续把 OpenAPI 文案放在各自 `openapi.operation`、`openapi.parameter`、`openapi.schema.property` 下，避免使用旧的路径拼接式 operationId。
- 验证：公共中英文 JSON 均可解析；旧 OpenAPI ID 与旧 `route:users` 示例扫描无残留；`npm run test:smoke`、`npm run typecheck` 通过。

## 2026-06-20：容器管理新增 Docker 储存卷管理

- 背景：容器管理已有容器、镜像、任务能力，但缺少 1Panel 等容器工具常见的 Docker volume 管理。跨平台边界统一采用 Docker Engine 的 named volume API，不扫描或直接操作宿主机目录；Windows/Linux/macOS 由 Docker Desktop/Engine 负责真实存储位置差异。
- 后端：新增 `/api/container-volumes` router，支持分页查询、创建、删除未使用卷、清理当前权限范围内未使用的平台卷；卷创建和容器创建自动写入 `metrix.created_by/metrix.owner_user_id/metrix.resource_type=volume` labels。普通用户只能查看/删除自己创建的卷，`action:container:manage_others` 可管理全部；创建容器挂载已有卷时也校验卷归属，避免普通用户挂载他人或外部卷。删除使用中的卷会返回 `error.containerVolumeInUse`。
- 前端：容器管理页新增“储存卷”标签，包含关键字搜索、使用状态筛选、创建卷、清理未使用卷、列表列宽拖拽、使用容器展示和删除操作；创建容器弹窗的重启策略下拉改为 i18n 文案（不自动重启/始终重启/除非手动停止/失败时重启），提交值仍保持 Docker 原始枚举。
- i18n/OpenAPI：容器模块中英文语言包补齐储存卷 UI 文案、错误、审计动作、OpenAPI tag/operation/parameter/schema 字段说明；权限描述扩展为容器、镜像与储存卷。
- 验证：容器模块中英文 JSON 可解析；`.venv\Scripts\python.exe -m compileall -q server/app/modules/containers server/tests/test_containers.py` 通过；`.venv\Scripts\python.exe -m pytest server/tests/test_containers.py` 通过；`npm run test:smoke`、`npm run typecheck`、`npm run build` 通过（Vite 仅有既有大 chunk 提示）。

## 2026-06-21：补齐列表列宽规则并清理旧开发文档

- 前端：补齐数据库连接列表、数据任务列表、储存文件列表、脚本运行历史弹窗和 SQL 工作台动态结果表的列宽拖拽链路，统一使用响应式 `columnWidths`、`sumColumnWidths`、`@unstable-column-resize` 与 `updateColumnWidth`；SQL 工作台按标签页分别保存表数据列宽和查询结果列宽，避免不同表或结果互相影响。
- 清理：示例 CRUD、数据任务和 SQL 工作台行操作列改为 `table-action-group` + 圆形图标按钮；容器管理列宽 key 映射改为初始化时生成，避免每次拖拽重复构造。
- 文档：`README.md` 去掉已退役的 `route:<page>` 和 `dev.bat` 说法，改为当前 `action:<resource>:read` 页面/导航网关；`DEVELOPMENT_GUIDE.md` 明确后续列表列宽实现规则，操作列不参与拖拽。

## 2026-06-21：第一轮全量清理和错误修复

- 后端：删除脚本预设模块中未使用的 `PRESET_LANGUAGES` 与 `preset_by_image`；数据库导入接口对非法 `mapping` JSON 返回稳定业务错误 `error.databaseImportMappingInvalid`，避免表单异常输入绕过校验变成 500，并补回归测试。
- 前端：删除未使用的 `getDataJob`、`getScript` API 封装；数据库连接列表按 `DATABASE_UPDATE`/`DATABASE_DELETE` 拆分编辑、测试和删除入口；SQL 工作台行编辑/删除和 SQL 执行入口按 `DATABASE_OPERATE` 显示；数据库任务、数据库工作台和容器管理确认弹窗统一捕获异步失败并显示错误提示。
- 容器：镜像导入弹窗打开、关闭和提交成功后清空文件列表与进度，避免重复打开残留上一次上传状态。
- 验证：`.venv\Scripts\python.exe -m compileall -q server/app server/tests`、`.venv\Scripts\python.exe -m pytest -q`、`npm run test:smoke`、`npm run typecheck`、`npm run build` 均通过；构建仅保留既有大 chunk 提示，pytest 仅保留 Starlette TestClient 的 `httpx` 兼容提示。

## 2026-06-22：第二轮权限边界和异步错误清理

- 后端容器镜像可见性修复：`list_images()` 区分“完全未登记的 Docker daemon 镜像”和“已登记但当前用户不可见的私有镜像”；普通用户不再把他人私有镜像误当公共镜像，也不能创建容器或导出该镜像。新增私有镜像隔离回归测试。
- 前端权限边界：容器行操作按本人/`CONTAINER_MANAGE_OTHERS` 控制启动、停止、重启、终端和删除；容器日志弹窗的“清空日志”仅在具备容器操作权限且有行级管理权时显示；数据库任务删除按钮只对本人或具备 `DATABASE_MANAGE_OTHERS` 的用户显示。
- SQL 工作台：表数据导出、查询结果导出和复制当前页数据统一捕获异步失败并显示错误提示，避免网络或剪贴板失败产生未处理 Promise。
- 验证：`.venv\Scripts\python.exe -m compileall -q server/app server/tests`、`.venv\Scripts\python.exe -m pytest -q`、`npm run test:smoke`、`npm run typecheck`、`npm run build`、`npm run test:regression` 均通过；Playwright 干净环境 7 passed，Vite 代理在无后端测试场景下仍有既有 ECONNREFUSED 噪声。

## 2026-06-22：第三轮终审清理

- SQL 工作台脚本树操作菜单按权限收口：载入和详情保持可见，重命名仅 `SQL_SCRIPT_UPDATE` 可见，执行仅 `DATABASE_OPERATE` 可见，删除继续按 `SQL_SCRIPT_DELETE` 控制。
- 容器日志复制失败时统一走 `showError`，避免剪贴板拒绝权限时产生未处理 Promise。
- 容器镜像删除逻辑修正：非管理员删除自己私有镜像记录时，如果同一 `image_id` 仍有其他用户或公共记录，只删除当前用户记录，不删除 Docker 全局镜像；补充多用户同 image_id 删除回归。
- 验证：`.venv\Scripts\python.exe -m compileall -q server/app server/tests`、`.venv\Scripts\python.exe -m pytest -q`、`npm run test:smoke`、`npm run typecheck`、`npm run build`、`npm run test:regression` 均通过；Playwright 仍仅有测试环境下 Vite 代理 ECONNREFUSED 噪声。

## 2026-06-22：容器管理高危写操作收紧为仅 Web 登录

- 背景：开发指南要求「容器管理接口必须保持 Web 登录、不默认给 API Token 开放高危操作」，但容器模块所有端点此前只用 `require_permission(CONTAINER_*)`（`get_current_user` 同时放行 Web 会话与 API Token），高危写操作实际可被 API Token 调用；新加的卷接口沿用同一模式，是该既有缺口的延续。
- 修复：`containers/api.py` 给所有高危写端点加 `dependencies=[Depends(require_web_session)]`——镜像 import/visibility/delete、实例 create/start/stop/restart/clear-logs/delete、卷 create/delete/prune（共 12 个）。读接口（engine status、镜像/实例/卷/任务 list、logs、export、job download）保持 `require_permission` 不变，API Token 仍可读。
- 容器 exec 终端 WS 经 `_ws_authenticate`→`decode_access_token` 鉴权，本就只认 Web 会话 token（API Token 前缀 `mtx_` 解不出 subject），无需改动。
- 影响：API Token 不再能创建/删除/启停容器、导入/删除镜像、创建/删除/清理卷；网页 UI 全程 Web 会话不受影响；被拦截时返回 403 `error.webOnly`。
- 验证：`python -m py_compile server/app/modules/containers/api.py` 通过；按约定未跑完整测试。
