# 页面开发指南

这份文档只记录新增主框架页面的最短路径。当前系统还处于开发阶段，不考虑旧安装数据的权限补偿；新增权限以初始化播种为准。

## 新增页面

1. 在 `web/src/views` 新建页面组件，页面内部只写当前页面需要的交互和布局。
2. 在 `web/src/router/page-registry.ts` 的 `appPages` 中添加页面注册项。
3. 注册项统一维护页面 `key`、`path`、`title`、懒加载组件、路由权限、菜单位置和 fallback 顺序。
4. 需要显示到侧边栏时配置 `menu`；不需要显示菜单的页面不配置 `menu`。
5. 需要收纳到二级菜单时使用已有 `group`，新增分组时维护同文件的 `menuGroups`。

`page-registry.ts` 会自动派生主框架子路由、页面标题、侧边栏菜单、父级展开状态和无权限 fallback，不要在 `router/index.ts` 或 `AppShell.vue` 里重复维护页面列表。

## 新增权限

1. 在 `server/app/core/permissions.py` 使用 `route_code(page)` 定义页面路由权限。
2. 业务资源需要增删改查操作时，使用 `action_code(resource, action)` 定义功能权限。
3. 在 `PAGE_PERMISSION_SPECS` 中添加页面权限规格。
4. 在 `RESOURCE_PERMISSION_SPECS` 中添加资源功能权限规格。
5. 路由权限授予后需要默认拥有查询能力时，在页面权限规格里填写对应 `read_permission`。

权限管理页面读取后端权限字典，不需要在前端再维护一份权限列表。受保护 API 必须在后端使用权限依赖做强校验，前端按钮只负责显示体验。

## 页面内按钮

页面内新增、删除、修改、操作按钮优先复用 `PermissionButton`。按钮权限编码使用后端同一套 `action:<resource>:<action>` 规则，避免页面里发明临时权限名。

后续如果接入数据级权限，前端按钮先按功能权限显示，再叠加接口返回的行级能力字段；页面组件不要自行硬编码公司、部门、本人等数据范围规则。
