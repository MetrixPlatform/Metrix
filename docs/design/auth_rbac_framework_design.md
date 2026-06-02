# 登录与 RBAC 框架设计

## 1. 目标

本阶段只实现一套轻量、清晰、可扩展的基础框架：

- Web 登录。
- Python 后端 API。
- SQLite 作为网站数据库。
- 管理员账号管理其他账号。
- RBAC 权限管理。
- 支持路由权限和功能权限。
- 前端根据权限显示菜单、页面和功能按钮。
- 后端对每个受保护 API 做权限校验。

第一版只做平台骨架，不接入文件处理、FTP/SFTP、数据库处理和任务调度等业务模块。

## 2. 技术选型

### 2.1 后端

建议：

- Python。
- FastAPI。
- Uvicorn。
- SQLite。
- SQLAlchemy。
- Pydantic。

选择理由：

- FastAPI 适合轻量 API 和自动 OpenAPI 文档。
- SQLite 适合第一阶段网站库，部署简单，不需要先搭 MySQL。
- SQLAlchemy 便于后续从 SQLite 平滑迁移到其他数据库。
- Pydantic 用于请求和响应结构校验。

第一版不要引入复杂依赖：

- 不引入 Celery。
- 不引入 Redis。
- 不引入复杂 ORM 插件。
- 不引入多租户。
- 不引入外部统一认证。

### 2.2 前端

建议：

- Vue 3。
- TypeScript。
- Vite。
- Naive UI。

前端只负责交互，不保存真实权限判断结果。权限判断必须以后端为准。

### 2.3 会话方式

建议第一版使用登录 Token：

- 登录成功后后端返回访问 Token。
- 前端保存在内存和本地存储中。
- API 请求通过 `Authorization: Bearer <token>` 发送。
- 后端解析 Token 后加载用户、角色和权限。

Token 可以使用 JWT 或服务端随机 Token。第一版建议使用 JWT，代码简单，状态较少。后续如果需要主动踢下线、会话列表和单设备控制，再切换或增加服务端会话表。

## 3. 目录结构

框架目录延续平台总体设计：

```text
Metrix/
  web/
    src/
      api/
      components/
      router/
      stores/
      views/
  server/
    app/
      api/
      core/
      db/
      models/
      schemas/
      services/
```

说明：

- `web/src/api`：前端 API 调用封装。
- `web/src/components`：通用组件。
- `web/src/router`：路由配置和路由守卫。
- `web/src/stores`：登录态、用户信息和权限缓存。
- `web/src/views`：页面视图。
- `server/app/api`：API 路由。
- `server/app/core`：配置、鉴权、权限依赖、异常处理。
- `server/app/db`：SQLite 连接、初始化和迁移入口。
- `server/app/models`：数据库模型。
- `server/app/schemas`：请求和响应结构。
- `server/app/services`：账号、角色、权限、登录等业务服务。

第一版不需要拆 submodule。先用单仓库目录跑通框架，后续模块稳定后再按职责拆分。

## 4. RBAC 设计

### 4.1 权限类型

权限分两类：

| 类型 | 说明 | 示例 |
| --- | --- | --- |
| 路由权限 | 决定用户能否访问某个前端页面或后端页面资源 | `route:users`, `route:settings` |
| 功能权限 | 决定用户能否执行某个按钮、操作或 API 动作 | `action:user:create`, `action:user:disable` |

命名规则：

- 路由权限使用 `route:<name>`。
- 功能权限使用 `action:<resource>:<operation>`。
- 权限编码只使用小写字母、数字、下划线和冒号。
- 权限编码由系统内置维护，管理员只负责分配，不手动输入编码。

### 4.2 角色

角色是权限集合。

建议内置角色：

| 角色 | 说明 |
| --- | --- |
| `admin` | 超级管理员，拥有所有权限，不允许删除最后一个管理员 |
| `user` | 普通用户，默认只拥有基础页面权限 |

管理员可以：

- 创建角色。
- 修改角色名称和说明。
- 给角色分配路由权限。
- 给角色分配功能权限。
- 给用户分配角色。
- 禁用用户。

第一版不支持角色继承，避免权限来源过于复杂。

### 4.3 用户

用户可以拥有多个角色。

用户字段建议：

- 用户名。
- 昵称。
- 密码哈希。
- 是否启用。
- 是否内置账号。
- 创建时间。
- 更新时间。
- 最近登录时间。

约束：

- 用户名唯一。
- 禁用用户不能登录。
- 不允许删除最后一个管理员账号。
- 不允许普通管理员把自己降权到失去管理员页面访问能力，除非后续有明确恢复机制。

### 4.4 权限判断规则

后端判断规则：

1. 未登录用户不能访问受保护 API。
2. 禁用用户不能访问任何受保护 API。
3. `admin` 角色默认拥有全部权限。
4. 非管理员用户的权限来自其所有角色权限合集。
5. 访问 API 时，后端根据 API 要求的权限编码判断是否允许。
6. 前端隐藏无权限菜单和按钮，但不能代替后端权限判断。

前端判断规则：

1. 登录后获取当前用户信息、角色和权限列表。
2. 路由守卫按 `route:*` 权限决定是否允许进入页面。
3. 按钮和操作入口按 `action:*` 权限决定是否显示或禁用。
4. 前端无权限时显示明确提示，不展示空白页面。

## 5. SQLite 数据表设计

第一版网站库只保存认证、用户、角色、权限和审计基础数据。

建议表：

| 表名 | 说明 |
| --- | --- |
| `users` | 用户 |
| `roles` | 角色 |
| `permissions` | 权限字典 |
| `user_roles` | 用户和角色关联 |
| `role_permissions` | 角色和权限关联 |
| `audit_logs` | 关键操作审计日志 |

### 5.1 `users`

字段：

- `id`。
- `username`。
- `display_name`。
- `password_hash`。
- `is_active`。
- `is_builtin`。
- `last_login_at`。
- `created_at`。
- `updated_at`。

### 5.2 `roles`

字段：

- `id`。
- `code`。
- `name`。
- `description`。
- `is_builtin`。
- `created_at`。
- `updated_at`。

### 5.3 `permissions`

字段：

- `id`。
- `code`。
- `name`。
- `type`。
- `group_name`。
- `description`。
- `sort_order`。
- `created_at`。

### 5.4 `user_roles`

字段：

- `user_id`。
- `role_id`。

### 5.5 `role_permissions`

字段：

- `role_id`。
- `permission_id`。

### 5.6 `audit_logs`

字段：

- `id`。
- `actor_user_id`。
- `action`。
- `target_type`。
- `target_id`。
- `detail`。
- `created_at`。

第一版审计只记录账号、角色、权限、登录失败等关键操作，不做复杂查询。

## 6. 内置权限清单

第一版建议内置以下权限。

路由权限：

| 编码 | 页面 |
| --- | --- |
| `route:dashboard` | 总览 |
| `route:users` | 用户管理 |
| `route:roles` | 角色管理 |
| `route:settings` | 系统设置 |

功能权限：

| 编码 | 功能 |
| --- | --- |
| `action:user:create` | 创建用户 |
| `action:user:update` | 修改用户 |
| `action:user:disable` | 启用或禁用用户 |
| `action:user:reset_password` | 重置用户密码 |
| `action:user:assign_roles` | 给用户分配角色 |
| `action:role:create` | 创建角色 |
| `action:role:update` | 修改角色 |
| `action:role:delete` | 删除角色 |
| `action:role:assign_permissions` | 给角色分配权限 |
| `action:settings:view` | 查看系统设置 |

后续业务模块新增页面和按钮时，只需要新增权限字典，不改变 RBAC 主体结构。

## 7. 后端 API 设计

API 按资源分组。

### 7.1 登录 API

| 接口 | 说明 |
| --- | --- |
| `POST /api/auth/login` | 登录 |
| `POST /api/auth/logout` | 退出登录 |
| `GET /api/auth/me` | 当前用户、角色和权限 |
| `POST /api/auth/change-password` | 修改自己的密码 |

### 7.2 用户 API

| 接口 | 权限 | 说明 |
| --- | --- | --- |
| `GET /api/users` | `route:users` | 用户列表 |
| `POST /api/users` | `action:user:create` | 创建用户 |
| `PUT /api/users/{id}` | `action:user:update` | 修改用户 |
| `POST /api/users/{id}/disable` | `action:user:disable` | 禁用用户 |
| `POST /api/users/{id}/enable` | `action:user:disable` | 启用用户 |
| `POST /api/users/{id}/reset-password` | `action:user:reset_password` | 重置密码 |
| `PUT /api/users/{id}/roles` | `action:user:assign_roles` | 分配角色 |

### 7.3 角色 API

| 接口 | 权限 | 说明 |
| --- | --- | --- |
| `GET /api/roles` | `route:roles` | 角色列表 |
| `POST /api/roles` | `action:role:create` | 创建角色 |
| `PUT /api/roles/{id}` | `action:role:update` | 修改角色 |
| `DELETE /api/roles/{id}` | `action:role:delete` | 删除角色 |
| `PUT /api/roles/{id}/permissions` | `action:role:assign_permissions` | 分配权限 |

### 7.4 权限 API

| 接口 | 权限 | 说明 |
| --- | --- | --- |
| `GET /api/permissions` | `route:roles` | 权限字典 |

权限字典第一版只读，由系统初始化写入。

### 7.5 系统 API

| 接口 | 权限 | 说明 |
| --- | --- | --- |
| `GET /api/health` | 无 | 健康检查 |
| `GET /api/settings` | `action:settings:view` | 查看系统设置 |

## 8. 前端页面设计

第一版页面：

| 页面 | 说明 |
| --- | --- |
| 登录页 | 用户名、密码登录 |
| 总览页 | 登录后默认页，展示框架状态 |
| 用户管理 | 用户列表、创建、编辑、启用禁用、重置密码、分配角色 |
| 角色管理 | 角色列表、创建、编辑、删除、分配权限 |
| 系统设置 | 第一版只放基础只读信息 |

前端行为：

- 登录成功后进入总览页。
- 无权限菜单不展示。
- 访问无权限路由时跳转到无权限页面。
- 操作按钮按功能权限展示。
- API 返回 401 时清理登录态并返回登录页。
- API 返回 403 时显示无权限提示。

## 9. 初始化策略

首次启动时初始化 SQLite。

初始化内容：

- 创建基础表。
- 写入内置权限。
- 写入内置 `admin` 角色。
- 写入内置 `user` 角色。
- 给 `admin` 角色分配全部权限。
- 创建默认管理员账号。

默认管理员账号建议通过环境变量或启动配置提供。若没有配置，可使用固定默认账号并强制首次登录后修改密码。

建议默认：

- 用户名：`admin`。
- 初始密码：由配置提供。

不要把真实密码写入文档或代码。

## 10. 安全约束

- 密码必须哈希保存，不能明文保存。
- 登录失败需要返回统一错误，不提示用户名是否存在。
- 禁用账号不能登录。
- 修改密码需要校验旧密码。
- 重置密码只能由有权限的用户操作。
- 不允许删除内置角色。
- 不允许删除或禁用最后一个管理员。
- 受保护 API 必须统一走鉴权依赖。
- 前端权限控制只是体验优化，后端必须再次校验。

## 11. 首版边界

第一版要做：

- 登录。
- 当前用户信息。
- 用户管理。
- 角色管理。
- 权限分配。
- 路由权限。
- 功能权限。
- SQLite 初始化。
- 基础审计日志。

第一版暂不做：

- 多组织、多租户。
- 数据权限。
- 单点登录。
- LDAP。
- 二次验证。
- 复杂密码策略。
- 在线用户管理。
- Token 黑名单。
- 审批流。
- 业务模块权限。

## 12. 实现顺序建议

后续进入实现时，建议按下面顺序：

1. 初始化 `server/` 和 `web/` 基础工程。
2. 实现 SQLite 连接和初始化。
3. 实现用户、角色、权限表。
4. 实现登录、当前用户和鉴权依赖。
5. 实现权限校验。
6. 实现用户管理 API。
7. 实现角色和权限 API。
8. 实现登录页和基础布局。
9. 实现路由守卫和权限菜单。
10. 实现用户管理和角色管理页面。

确认这份设计后，再开始实现代码。
