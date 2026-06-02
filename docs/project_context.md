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
