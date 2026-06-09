# Super Harness — 项目记忆

> 最后更新: 2026-06-09
> 本文档由 Agent 自动维护，记录项目状态、决策和经验。

## 项目身份

| 字段 | 值 |
|------|-----|
| 名称 | Super Harness |
| 定位 | Agent 增强协议框架 |
| 语言 | 中文为主 |
| 许可证 | MIT |
| 记忆系统 | ReMe (计划 Fork) |
| 中央仓库 | ~/.super-harness/ |

## 架构概览

Super Harness 是一个两层架构：

1. **全局层**（中央仓库）：共享协议、研究源、能力、全局记忆
2. **项目层**（各项目目录）：项目特有的灵魂、记忆、计划

核心协议：
- SOUL.md — Agent 身份和价值观
- PLANNING.md — 思维工具箱（原则驱动，非固定流程）
- RESEARCH.md — 研究协议（可扩展研究源）
- CAPABILITIES.md — 能力发现协议（向量检索 Skill + MCP）

## 模块状态

| 模块 | 状态 | 说明 |
|------|------|------|
| 全局 SOUL.md | ✅ SHIPPED | Agent 身份和价值观 |
| 全局 PLANNING.md | ✅ SHIPPED | 思维工具箱 |
| 全局 RESEARCH.md | ✅ SHIPPED | 研究协议 |
| 全局 CAPABILITIES.md | ✅ SHIPPED | 能力发现协议 |
| 研究源注册 | ✅ SHIPPED | 6 个初始源（arXiv, DeepWiki, GitHub, PyPI, npm, Semantic Scholar） |
| 能力注册表 | ✅ SHIPPED | 初始结构（空） |
| 项目模板 | ✅ SHIPPED | .harness.json + 项目级文档 |
| 平台适配器 | ✅ SHIPPED | 6 个适配器（Claude, Codex, Cursor, Windsurf, Copilot, Gemini） |
| 向量索引 | ✅ SHIPPED | SQLite + BM25 全文搜索（向量检索可选） |
| 端到端验证 | ✅ SHIPPED | 文件结构验证通过（23 个文件创建成功） |

## 关键决策记录 (ADR)

### ADR-001: 选择文档驱动而非代码驱动
- **日期**: 2026-06-09
- **正题**: 代码框架可以强制执行规则
- **反题**: 文档更灵活，任何 Agent 平台都能读
- **合题**: 文档即协议，工具是可选增强

### ADR-002: 选择原则驱动而非流程驱动
- **日期**: 2026-06-09
- **正题**: 固定流程保证一致性
- **反题**: 复杂任务需要灵活性
- **合题**: 提供思维工具和判断矩阵，让 Agent 自己决定

### ADR-003: 选择中央化存储
- **日期**: 2026-06-09
- **正题**: 项目内嵌更方便
- **反题**: MCP/Skill/研究源是跨项目共享的
- **合题**: 中央仓库 + 项目级覆盖

### ADR-004: 选择 ReMe 作为记忆系统基础
- **日期**: 2026-06-09
- **正题**: ReMe 文件即记忆的理念最贴近需求
- **反题**: 依赖 agentscope 框架
- **合题**: Fork ReMe，保留核心，封装隔离

## 关键坑点 (Critical Gotchas)

> 暂无。执行任务时自动积累。

## 编码约定

- 文档用中文
- 技术术语可用英文
- Markdown 格式
- 文件命名用 kebab-case

## Dev Commands

```bash
# 查看中央仓库
ls ~/.super-harness/

# 查看项目结构
ls "A:\project\super harness\"

# 查看研究源
cat ~/.super-harness/sources/_index.md

# 查看能力注册表
cat ~/.super-harness/capabilities/_index.md
```

## 文档地图

| 路径 | 用途 |
|------|------|
| ~/.super-harness/SOUL.md | 全局 Agent 身份 |
| ~/.super-harness/PLANNING.md | 思维工具箱 |
| ~/.super-harness/RESEARCH.md | 研究协议 |
| ~/.super-harness/CAPABILITIES.md | 能力发现协议 |
| ~/.super-harness/sources/ | 研究源注册表 |
| ~/.super-harness/capabilities/ | 能力注册表 |
| ./SOUL.md | 项目级灵魂 |
| ./MEMORY.md | 项目级记忆（本文件） |
| ./memory/ | 项目级日志 |
| ./plans/ | 计划 |
