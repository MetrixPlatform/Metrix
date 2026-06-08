# 页面开发指南

这份文档只记录新增主框架页面的最短路径。当前系统还处于开发阶段，不为旧 API 响应或旧表结构额外编写兼容层；新增权限、字段和接口契约以最新代码为准，开发库通过后端同步迁移或直接调整数据适配。

## 新增页面

1. 在 `web/src/views` 新建页面组件，页面内部只写当前页面需要的交互和布局。
2. 在 `web/src/router/page-registry.ts` 的 `appPages` 中添加页面注册项。
3. 注册项统一维护页面 `key`、`path`、`titleKey`、懒加载组件、路由权限、菜单位置和 fallback 顺序。
4. 需要显示到侧边栏时配置 `menu`；不需要显示菜单的页面不配置 `menu`。
5. 需要收纳到二级菜单时使用已有 `group`，新增分组时维护同文件的 `menuGroups` 和对应 `labelKey`。

`page-registry.ts` 会自动派生主框架子路由、页面标题、侧边栏菜单、父级展开状态和无权限 fallback，不要在 `router/index.ts` 或 `AppShell.vue` 里重复维护页面列表。

## 多语言

前端文案统一通过 `web/src/i18n` 管理，底层使用本地依赖 `vue-i18n`，当前支持 `zh-CN` 和 `en-US`。新增页面、弹窗、按钮、表单提示、空状态、确认信息、表头、枚举显示和路由标题都不能在页面组件中直接硬编码展示文案。

- 新增页面标题和菜单名称时，在语言包中新增 `route.*` key，并在 `page-registry.ts` 使用 `titleKey` 或 `labelKey`。
- 页面展示文案使用 `t("...")`，日期时间使用 `formatDateTime`，不要在页面里直接调用固定语言的格式化逻辑。
- 表单校验规则需要使用 `computed` 生成，确保语言切换后校验提示同步更新。
- 后端返回的内置角色、权限名称和权限分组通过 `web/src/i18n/builtins.ts` 做显示转换；新增内置权限时同步维护语言包和内置映射。
- API 结构化校验错误由前端请求层按字段 key 翻译；后端自定义 Pydantic 校验错误使用稳定 `validation.*` 类型，不返回中文展示文案。
- 后端业务成功或失败消息统一返回 `code`、`message`、`params`：`code` 是稳定资源 ID，`message` 只作为英文 fallback，`params` 存放插值变量。前端使用 `translateMessage(...)` 或 `messageText(...)` 翻译，找不到语言包 key 时才显示后端 fallback。
- 需要变量插值的文案使用 `{name}`、`{count}` 这类命名参数，例如 `user.deleteConfirm` 或 `announcement.batchDeleted`；后端只传变量值，不拼接最终展示句子。
- 后端禁止返回中文 `detail`、中文 `MessageResponse.message` 或拼接后的中文业务提示；新增异常使用 `bad_request(...)`、`forbidden(...)`、`not_found(...)` 等统一 helper。
- 新增语言时只扩展 `locales`、Naive UI 语言映射和语言包，不要在各页面单独写语言切换逻辑。
- 左侧标签表单统一使用 `.inline-form`、`label-placement="left"` 和 `label-width="auto"`，不要写固定窄标签宽度；标签必须单行右对齐，输入框左边缘由自动标签列保持一致。
- 表单控件必须撑满当前可用宽度，并保持宽度稳定；`n-input`、`n-input-number`、`n-select`、`n-date-picker` 等不能因为输入内容、密码显示图标、后缀按钮或校验状态出现宽度跳变。
- 两列或紧凑表单中，如果标签会挤压输入框宽度，应在局部使用“标签在上、控件在下”的布局或调整网格列宽，不能牺牲输入框可用宽度。
- 长文案按钮、复选框、单选按钮和工具栏操作需要允许换行或自适应宽度，不能因为翻译变长而裁切、重叠或遮挡其他控件。
- 窄容器和移动宽度下，左侧标签表单可以切成“标签在上、控件在下”的布局，但标签仍不能换行或遮挡输入框；新增语言后至少验证登录、注册、系统设置和常用弹窗。

## 主框架布局

后台主框架页面默认使用贴边工作区布局：内容区不得额外留出外边距或外层内边距，页面最外层工作区边框必须贴合侧边栏右边、顶部标题栏底边和底部页脚边界，形成 100% 宽高的工作面。

- 新增主框架页面优先使用现有 `.work-card`、`.table-page-card`、`.list-page-card` 等全局样式，不要在页面组件里重新添加外层圆角、阴影、外边距或浮动卡片效果。
- 页面内部可以保留必要的内容内边距和工具栏间距，但不要让最外层工作区从主框架边界内缩。
- 只有用户明确要求浮动布局、留白布局或特殊展示页时，才允许偏离贴边工作区规则，并需要在对应实现或项目记忆中记录原因。

## 新增权限

1. 在 `server/app/core/permissions.py` 使用 `route_code(page)` 定义页面路由权限。
2. 业务资源需要增删改查操作时，使用 `action_code(resource, action)` 定义功能权限。
3. 在 `PAGE_PERMISSION_SPECS` 中添加页面权限规格。
4. 在 `RESOURCE_PERMISSION_SPECS` 中添加资源功能权限规格。
5. 路由权限授予后需要默认拥有查询能力时，在页面权限规格里填写对应 `read_permission`。

后端内置权限和内置角色种子只保存稳定 key 或编码，不保存中文、英文等展示文案。权限种子的 `name`、`group_name`、`description` 使用 `permission.*` 这类资源 key，内置角色使用 `role.*` key；页面展示统一由前端 i18n 根据权限 `code`、分组 key 或角色 key 翻译。

权限管理页面读取后端权限字典，不需要在前端再维护一份权限列表。受保护 API 必须在后端使用权限依赖做强校验，前端按钮只负责显示体验。

## API 与 Token

平台 API 功能由系统设置 `api_enabled` 总开关控制。关闭后 Token 页面、API 文档页面、`/openapi.json` 和 API Token 调用都必须不可用；前端只负责隐藏入口，后端必须继续强校验。

- API 文档页面使用前端 `/api-docs`，读取受保护的 `/openapi.json` 并按 OpenAPI/Swagger 结构展示接口；`/docs` 和 `/openapi.json` 都需要登录且拥有 `action:api_docs:read`。
- API 文档页使用“接口列表 + 详情弹窗 + 测试弹窗”的布局：列表只展示方法、路径和摘要，参数、请求体字段、请求示例、响应说明、响应示例等放在详情中查看，避免大量说明直接铺在列表里。
- API 文档页内置接口测试面板：开发者填入 API Token 后，可以按 OpenAPI 参数测试接口；测试面板必须展示实际发送的数据和返回结果，页面只自动处理常见 path/query 参数和 JSON 请求体，不在前端维护第二份接口清单。
- 请求体和响应示例优先从 OpenAPI schema 的 `example`、`examples`、`default`、`enum` 中读取；未显式配置时由前端按 schema 类型生成可编辑示例，不能让测试请求体只显示空 `{}`。
- `/openapi.json` 默认过滤安装、探活和 Token 管理接口，如 `/api/install*`、`/api/health*`、`/api/tokens*`，避免把初始化、探活和 Web-only 管理能力暴露给 API 调用者文档。
- Token 页面使用 `/tokens`，权限为 `route:tokens`，授予后默认扩展 `action:api_token:read`；创建和删除分别使用 `action:api_token:create`、`action:api_token:delete`。
- Token 管理只能通过网页登录态操作，后端 `/api/tokens*` 需要 `require_web_session` 强校验；API Token 即使拥有角色权限也不能调用 Token 创建、查询、显示完整值或删除接口。
- API Token 是全平台鉴权入口，后续接口默认不需要额外适配 Token。只要接口继续使用 `get_current_user`、`require_permission(...)` 或 `require_any_permission(...)`，Bearer Token 与 API Token 都会进入同一套用户状态和角色权限校验。
- API Token 创建时 `expires_at = null` 表示永不过期；前端创建弹窗必须显式提供“永不过期”和“自定义时间”两种选择。
- API Token 始终保存哈希和展示前缀；当系统设置 `api_token_reveal_enabled` 开启时，新创建 Token 还会保存可恢复的完整值，用户可在列表中通过专门的 `/api/tokens/{id}/secret` 接口显示或复制完整 Token。
- API Token 是用户级资源，后端 repository/service 必须按当前用户 ID 查询；管理员也不跨用户查看、显示或删除他人的 Token。
- 列表接口不得直接返回明文 Token，只能返回 `secret_available` 让前端判断是否显示“显示/复制”按钮；旧 Token 或未保存完整值的 Token 只能显示前缀。
- 关闭 `api_token_reveal_enabled` 后，前端隐藏完整 Token 显示/复制入口，后端 secret 接口仍必须返回 403；关闭该开关不会删除已保存的完整值。
- 用 API Token 调用接口时，用户角色仍必须拥有 `action:api_token:read`，并且目标接口本身仍要通过对应权限；收回角色 API 能力后，既不能创建新 Token，旧 Token 也不能继续调用平台接口。
- 后续新增业务 API 时，在 FastAPI 路由上设置清晰 `tags`、`summary`、响应模型和必要的 `responses`，请求/响应 Pydantic schema 字段使用 `Field(...)` 描述和示例；API 文档页会自动从 `/openapi.json` 中展示，不要在前端 API 文档页手写接口清单。
- OpenAPI 文档翻译集中维护在 `web/src/i18n/openapi.ts`，不要塞进通用页面语言包。翻译 key 约定为 `tag.<tag>`、`operation.<operationId>.summary`、`operation.<operationId>.description`、`parameter.<operationId>.<name>`、`parameter.common.<name>`、`schema.property.<field>`、`schema.property.<nested.field>` 和 `response.<status>`；页面优先取这些翻译，找不到时回退到 OpenAPI 原始说明。
- 若新增页面属于 API 功能整体开关管辖，在 `web/src/router/page-registry.ts` 的页面注册项中设置 `feature: "api"`，菜单、fallback 和路由守卫会统一处理显示与访问。
- Vite 开发代理只匹配 `/api/` 和 `/openapi.json`。不要把代理前缀改回宽泛的 `/api`，否则前端页面路径 `/api-docs` 会被误转发到后端并在刷新时显示 404。

## 页面内按钮

页面内新增、删除、修改、操作按钮优先复用 `PermissionButton`。按钮权限编码使用后端同一套 `action:<resource>:<action>` 规则，避免页面里发明临时权限名。

后续如果接入数据级权限，前端按钮先按功能权限显示，再叠加接口返回的行级能力字段；页面组件不要自行硬编码公司、部门、本人等数据范围规则。

## 本人和他人数据权限

功能权限只表达用户能否执行某类动作，不直接代表可以操作他人创建或上传的数据。没有额外授权时，`update`、`delete`、`operate` 默认只允许作用于当前用户本人创建、上传、负责或归属的数据。

- 需要允许操作他人数据时，按资源增加范围提升权限 `action:<resource>:manage_others`，例如 `action:announcement:manage_others` 表示可以操作他人公告。
- 操作他人数据必须同时满足基础动作权限和范围提升权限。例如修改他人公告需要 `action:announcement:update` 加 `action:announcement:manage_others`；删除他人公告需要 `action:announcement:delete` 加 `action:announcement:manage_others`。
- 未拥有范围提升权限时，后端遇到他人数据的编辑、删除、启停、发布、下载等受控动作必须返回权限不足，不能只依赖前端隐藏按钮。
- 前端行操作按钮先按基础功能权限显示，再根据后端返回的行级能力决定是否显示或禁用；不要在页面里自行比较账号、公司、部门来判断能否操作。
- 新增业务表默认保留创建人或归属人字段，优先使用用户 ID，如 `created_by`、`owner_user_id`；接口需要展示时再返回账号、姓名等冗余展示字段。
- 上传、导入、手工新增、脚本生成等会产生业务数据的入口，都要记录操作账号，便于审计和后续本人/他人权限划分。

## 操作日志

关键写操作和高风险操作需要通过 `record_audit(...)` 记录操作日志，至少包含当前操作人、动作编码、目标类型、目标 ID 和必要详情。动作编码保持稳定，例如 `user.create`、`role.assign_permissions`、`announcement.delete`，前端展示名通过语言包映射，后端不返回中文展示文案。

- 操作日志页面使用 `route:audit_logs` 控制菜单和页面进入，授予该路由后默认扩展 `action:audit_log:read`。
- 只有 `action:audit_log:read` 时，日志查询默认且只能查看当前登录账号自己的日志。
- 需要查看所有账号日志时，额外授予范围提升权限 `action:audit_log:manage_others`；后端接口必须强校验该权限，不能只依赖前端隐藏筛选项。
- 鉴权依赖会把请求来源写入当前数据库会话上下文，`record_audit(...)` 自动记录 `source = web/api` 和 API Token 前缀；业务 service 不要自己猜来源，也不要手写第二套审计逻辑。
- 新增或修改写操作时，优先使用 `audit_detail(...)` 和 `audit_changes(...)` 传入结构化详情，记录操作对象名、字段变更前后值和必要 `meta`；旧的 `detail` 只作为列表摘要和旧日志兜底。
- 结构化详情不得记录密码明文、完整 API Token、Token hash、系统密钥等敏感值；涉及密码或 Token 时只记录是否变更、Token 前缀、名称、过期时间等可审计但不泄密的信息。
- 操作日志页面表格只展示来源，不展示 Token 前缀；来源列需要支持表头筛选，详情列保持紧凑摘要，完整字段变化、对象信息和附加记录放在详情弹窗内查看。
- 日志下载使用 `/api/audit-logs/export` 返回 CSV 附件，必须复用列表的关键字、操作类型、目标类型、账号范围、时间范围和排序条件；CSV 只展示来源，不展示 API Token 前缀，未授权查看所有账号时，导出接口同样只能导出本人日志。
- 操作日志列表继续遵守后台表格规则：后端分页、顶部保留关键字和时间范围，操作类型、目标类型、账号范围等枚举条件优先放表头筛选。

## 列表滚动

后台主框架内的列表页必须保持页面标题、筛选区、操作区和表头固定，不允许因为数据过多让外层页面滚动并把这些区域顶走。

- 表格页使用 `work-card table-page-card` 作为页面卡片，`n-data-table` 使用 `class="page-data-table"` 和 `flex-height`。
- 表格只允许数据区在表格内部滚动，表头必须固定在表格顶部；不要用外层 `.app-content` 或 `.work-card` 承担表格数据滚动。
- 非表格列表页使用 `work-card list-page-card`，工具栏放在卡片顶部，实际列表容器设置 `min-height: 0`、`flex: 1` 和 `overflow-y: auto`。
- 新增列表、时间线、树、权限分组等可增长内容时，都要优先把滚动限制在数据容器内部，避免影响页面头部、页脚、卡片工具栏和字段表头。

## 表格筛选

状态、类型、范围、展示方式等枚举字段优先使用表头筛选，不要把所有下拉筛选都堆在页面顶部工具栏里。顶部工具栏只保留关键字、时间范围和确实需要横向组合查询的条件，避免筛选项过多导致按钮重叠或挤压。

- 表头筛选可以继续调用后端列表接口，不要求只做当前表格数据的本地过滤。
- 受控筛选值要和接口查询参数保持同一份状态，避免页面顶部和表格列头维护两套筛选条件。
- 新增批量操作按钮时放在工具栏操作区，窄屏下允许自然换行，不要压缩输入框或日期范围。

## 表格分页

数据量可能增长的后台列表页必须使用后端分页，不允许一次性加载全部数据后再由前端分页，避免后续数据变多时接口耗时和页面卡顿。

- `n-data-table` 使用 `remote`，分页、表头筛选和排序统一映射到后端列表接口参数。
- 分页大小统一使用 `20 / 50 / 100 / 500`，后端接口 `page_size` 上限保持 500。
- 查询按钮、表头筛选和排序变更时重置到第一页；普通翻页和修改分页大小只刷新当前列表接口。
- 后端分页响应统一使用 `items`、`total`、`page`、`page_size`，前端不要自行拼装不一致的数据结构。

## 表格横向滚动

字段较多的后台表格必须保证横向滚动能完整到达最后一列，尤其不能遮挡操作列。

- 表格列宽集中维护为常量，`scroll-x` 使用列宽总和计算，不要手写一个可能小于实际列宽的固定值。
- 列表表格的每个业务列都必须支持拖拽调整列宽；操作列不允许调整并优先固定在右侧，选择列和展开列保持组件默认行为。
- 新增 `n-data-table` 列表时优先复用 `web/src/utils/table.ts` 的 `withResizableColumns(...)`、`updateColumnWidth(...)` 和 `sumColumnWidths(...)`，不要在页面里重复写列宽拖拽逻辑。
- 行操作列优先设置 `fixed: "right"`，保证用户无需拖动到底也能编辑、删除或打开更多操作。
- 新增、删除或调整列宽后必须同步列宽常量，让 `scroll-x` 自动跟随变化。
- 选择列、固定列和操作列都要计入横向滚动宽度，避免滚动条到头后仍看不到完整操作区。
