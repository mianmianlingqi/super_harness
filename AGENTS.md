# Super Harness — OpenCode Agent 指南

本项目使用 Super Harness 协议，一套让任何 AI Agent 都能跨平台工作的增强协议框架。

## 核心原则

- **先想后做** — 重大变更前花 10% 时间思考
- **比例匹配** — 简单任务轻处理，复杂任务深处理
- **不要重新发明轮子** — 先调研顶级方案
- **不猜测** — 不确定时用工具确认
- **不假装成功** — 没验证就不算完成
- **记录决策** — 重要的不是做了什么，而是为什么这么做

## 会话协议

### 会话开始时

读取以下文件获取完整上下文：

| 文件 | 路径 | 说明 |
|------|------|------|
| SOUL.md | `SOUL.md` | 项目灵魂和 Agent 身份 |
| MEMORY.md | `MEMORY.md` | 项目记忆和当前状态 |

### 收到任务时

参考 `PLANNING.md` 判断矩阵决定计划深度：

| 任务特征 | 计划深度 | 做法 |
|---------|---------|------|
| 改一个 bug、改个文案 | 无需计划 | 直接做 |
| 改一个函数、加个小功能 | 脑内计划 | 想 30 秒，直接做 |
| 涉及 3+ 文件、需要设计决策 | 轻量计划 | 列出步骤，确认后做 |
| 架构变更、新功能、跨模块 | 完整计划 | 写 `plans/{slug}.md`，分步执行 |
| 探索性/研究性任务 | 探针模式 | 先做小实验，根据结果决定方向 |

**计划纪律**：
- 破坏性操作前必须确认
- 不确定时问，不要猜
- 没验证就不算完成

### 需要调研时

查阅中央研究源目录：先读 `~/.super-harness/sources/_index.md`。

可用研究源：

| 源 | 类型 | 擅长 |
|----|------|------|
| arXiv | 学术论文 | 最新论文、SOTA 方法 |
| DeepWiki | 项目文档 | 开源项目架构和设计思路 |
| GitHub | 代码搜索 | 参考实现、项目趋势 |
| PyPI | Python 包 | 包发现和版本 |
| npm | Node.js 包 | 包发现和版本 |
| Semantic Scholar | 论文引用 | 引用网络、影响力排序 |

**研究纪律**：
- 引用来源 — 每个结论有出处
- 区分事实和观点
- 标记调研日期
- 研究结果要落地到可执行步骤

### 需要能力时

检索 `~/.super-harness/capabilities/` 中的 Skill 和 MCP。

或用 SQLite 数据库进行语义检索：
```bash
cd tools/memory
python semantic_search.py search "你需要什么能力"
```

### 会话结束时

更新 MEMORY.md：
- 新的坑点 → Critical Gotchas
- 架构变更 → Architecture
- 新的编码模式 → Coding Conventions
- 项目状态变化 → 模块状态表
- 经验教训 → 记入 `memory/YYYY-MM-DD.md`

## 协议文档索引

### 核心协议（中央仓库）

| 协议 | 路径 | 说明 |
|------|------|------|
| SOUL.md | `~/.super-harness/SOUL.md` | Agent 身份和价值观 |
| PLANNING.md | `~/.super-harness/PLANNING.md` | 思维工具箱 |
| RESEARCH.md | `~/.super-harness/RESEARCH.md` | 研究协议 |
| CAPABILITIES.md | `~/.super-harness/CAPABILITIES.md` | 能力发现协议 |

### 项目文档

| 文档 | 路径 | 说明 |
|------|------|------|
| SOUL.md | `SOUL.md` | 项目级灵魂 |
| MEMORY.md | `MEMORY.md` | 项目级记忆 |
| README.md | `README.md` | 项目说明 |

### 向量检索系统

| 文件 | 路径 | 说明 |
|------|------|------|
| harness_db.py | `tools/memory/harness_db.py` | 数据库基础操作 |
| semantic_search.py | `tools/memory/semantic_search.py` | 语义检索引擎 |

### 研究源注册

| 文件 | 路径 | 说明 |
|------|------|------|
| source index | `~/.super-harness/sources/_index.md` | 源目录 |
| arXiv | `~/.super-harness/sources/arxiv.md` | arXiv 接入配置 |
| DeepWiki | `~/.super-harness/sources/deepwiki.md` | DeepWiki 接入配置 |
| GitHub | `~/.super-harness/sources/github.md` | GitHub 接入配置 |

## 工作流

1. **会话开始** → 读 SOUL.md + MEMORY.md
2. **收到任务** → 判断复杂度 → 简单直接做，复杂先做计划
3. **需要决策** → 先调研，再决定，记录理由
4. **需要能力** → 检索能力注册表
5. **执行** → 按计划做，记日志
6. **完成** → 验证，更新记忆，归档计划

## 记忆维护协议

MEMORY.md 由 Agent 自动维护，每次会话结束时更新相关板块。

格式：
- 关键坑点 → bullet list
- 架构决策 → ADR 格式（正题→反题→合题）
- 编码约定 → 具体可执行的规则
- Dev Commands → `bash` code block
- 模块状态 → 表格

## 与 Claude Code 的区别

OpenCode 使用 `AGENTS.md` 作为入口，不支持 `@import` 语法。
因此本文件内联了关键协议内容，详细内容请显式读取对应文件。
