# Super Harness — 项目记忆

> 最后更新: 2026-06-10
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
| 平台适配器 | ✅ REMOVED | 零适配器模式，仅保留 AGENTS.md 作为统一入口 |
| 向量索引 | ✅ SHIPPED | SQLite + BM25 全文搜索（向量检索可选） |
| 端到端验证 | ✅ SHIPPED | 文件结构验证通过 |
| Claude Code 深度集成 | ✅ SHIPPED | 5 接口填满：hooks + MCP + commands + agents + wikilink memory |
| 平台适配器 | ✅ UPDATED | 模板新增 Claude Code 专属能力章节，8 平台全部重新生成 |

## 关键决策记录 (ADR)

> 详见独立记忆文件，Claude Code 会自动关联加载。

- [[adr-001-doc-driven]] — 选择文档驱动而非代码驱动
- [[adr-002-principle-driven]] — 选择原则驱动而非流程驱动
- [[adr-003-centralized]] — 选择中央化存储
- [[adr-004-reme-memory]] — 选择 ReMe 作为记忆系统基础
- [[adr-005-zero-dep-mcp]] — 选择零依赖自实现 MCP Server

## 关键坑点 (Critical Gotchas)

> 详见独立记忆文件，Claude Code 会自动关联加载。

- [[gotcha-adapters-source]] — 适配器维护只有一份真源
- [[gotcha-memory-layers]] — 记忆系统分两层，验证时分清层级
- [[gotcha-mcp-language-match]] — MCP 搜索语言必须和数据库内容语言匹配
- [[gotcha-db-init-before-mcp]] — MCP Server 启动前需确保数据库已初始化

## Claude Code 深度集成

Super Harness 在 Claude Code 中提供了以下增强能力：

| 接口 | 类型 | 说明 |
|------|------|------|
| MCP Server `super-harness` | 工具 | 语义搜索记忆/能力/研究源 |
| `/sh-research` | 斜杠命令 | 触发研究协议，结构化调研 |
| `/sh-remember` | 斜杠命令 | 手动触发记忆维护 |
| `/sh-reflect` | 斜杠命令 | 会话结束反思 |
| `sh-researcher` | 子 Agent | 研究型 Agent，内置研究协议 |
| `sh-curator` | 子 Agent | 记忆策展 Agent，格式化记忆更新建议 |
| Stop Hook | 自动化 | 会话结束时提醒更新 MEMORY.md |

详见 `.claude/settings.json`、`.claude/commands/`、`.claude/agents/`、`.claude/mcp/`。

## 编码约定

- 文档用中文
- 技术术语可用英文
- Markdown 格式
- 文件命名用 kebab-case
- MCP Server 零依赖原则：优先使用 Python stdlib，避免强制第三方依赖
- 适配器模板是唯一真源：改 `adapters/template.md` → 运行 `generate.py`

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

# 初始化记忆数据库
cd tools/memory && python init_db.py

# 测试语义搜索
cd tools/memory && python semantic_search.py search "代码审查"

# 测试 MCP Server（直接 JSON-RPC）
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python .claude/mcp/harness_search.py

# 重新生成所有平台适配器
python adapters/generate.py

# 测试会话结束 hook
python .claude/hooks/session_close.py
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
