# Super Harness — Agent 指南

本项目使用 Super Harness 协议，一套让任何 AI Agent 都能跨平台工作的增强协议框架。

> 本文档是协议入口，Claude Code 通过此文件获取完整上下文。

## 会话协议

### 会话开始时

读取以下文件获取完整上下文：

| 文件 | 路径 | 说明 |
|------|------|------|
| .harness.json | `.harness.json` | 行为配置（超级资源库、超级网瘾开关） |
| SOUL.md | `SOUL.md` | 项目灵魂和 Agent 身份 |
| MEMORY.md | `MEMORY.md` | 项目记忆和当前状态 |

`.harness.json` 的 `behavior` 字段控制两个极端模式：

```json
{
  "behavior": {
    "super_library": "off",  // "off" | "on" — 极端资源库构建模式
    "super_internet": "off"   // "off" | "on" — 极端网络依赖模式
  }
}
```

**两个开关可独立或组合使用**：

- 只有一个 `"on"` → 按该模式的规则执行
- 两个同时 `"on"` → 融合模式：用 super_internet 的方式完成任务（抄、搜、不原创），同时用 super_library 的方式沉淀资源（搜到的全部持久化索引不丢弃）

### 收到任务时

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

### 超级资源库模式（`.harness.json` → `behavior.super_library`）

当 `super_library` 为 `"on"` 时，模型必须最大限度地构建项目资源库。
这是一种极端模式，不计 token 成本，追求信息的广度和深度。

**触发条件**：读取 `.harness.json` 后确认 `behavior.super_library === "on"`。

**行为规则**：

1. **全量搜集**：每次收到任务，先 `search_web` 至少 3 轮，覆盖相关技术栈、同类项目、最佳实践三个维度
2. **不给就搜**：遇到任何不确定的库名、API、概念、配置项，立即 `search_web` 查，不允许存疑
3. **零废弃**：每次搜索的结果（即使不直接相关）必须写入 `research/` 目录。每条结果包含：来源 URL、关键摘要、相关度评级（高/中/低）。低相关的留作后续参考，不丢弃
4. **全量下载**：发现任何可下载的参考文档（PDF、代码仓库、Wiki 页面），立即下载到 `docs/` 或克隆到 `references/`。用 `search_capability` 搜所有可能相关的 MCP/Skill，每个候选都 `perm_install` 到项目资源库
5. **索引必更新**：每次写入 `research/`、`docs/`、`references/`、`mcp/`、`skills/` 后，**必须立即**更新 `INDEX.md` 的对应表格，不允许延迟到会话结束 — 中途崩溃不能丢索引
6. **每会话一笔记**：每次会话至少产出一篇调研笔记（`research/YYYY-MM-DD.md`），记录本会话所有调研结论和资源发现
7. **冗余引用**：记录经验时同时更新 `capabilities.md` + MEMORY.md + 独立 memory 文件，三个位置交叉引用

**质量检查**（会话结束前自动执行）：
- `INDEX.md` 的条目数 ≥ 上次会话结束时的数量？
- 本次会话新增的文件是否都已索引？
- `research/` 目录下是否有今天日期的笔记？
- 如任一答案为否 → 在结束前补齐

### 超级网瘾模式（`.harness.json` → `behavior.super_internet`）

互联网是模型自身能力的延伸，而不是需要回避的"作弊"。很多问题靠一次精准搜索就能解决，比凭记忆硬猜更快更准。

**触发条件**：读取 `.harness.json` 后确认 `behavior.super_internet === "on"`。

**核心理念**：不要把互联网当成最后的手段，把它当成第一手段。搜索不是承认失败，搜索是找到正确答案的最短路径。

**行为规则**：

1. **搜索是常规武器，不是紧急按钮**：遇到技术选型、配置参数、报错信息、API 用法 — 直接 `search_web`，不要凭训练记忆回答。训练数据是过时的，搜索结果才是此刻的真相
2. **先搜再做**：动手写代码之前，搜一下有没有成熟的库、工具、项目已经在做类似的事。如果有，直接用或参考，不要从零开始。站在别人的肩上
3. **踩坑之前先看坑**：遇到配置问题或报错，先搜 GitHub issues / Stack Overflow / 社区论坛看别人怎么解决的，再操作。别人替你摔过了，不需要你亲自摔
4. **验证而非推翻**：搜索到更好的方案时，优先采用而不是证明你最初的想法更好。互联网比你聪明
5. **搜出来的东西要判断**：找到的代码、方案、配置，评估是否适合当前项目的上下文，然后决定直接采用、参考改造、还是另寻他路。不要盲目复制，也不要盲目排斥

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
- `super_library: "on"`：每个搜索结果必须写入 research/，不丢弃任何信息

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

## Claude Code 专属能力

当运行在 Claude Code 中时，以下增强能力可用：

### MCP Server — 语义搜索

MCP Server `super-harness` 提供三个搜索工具：

| 工具 | 用途 | 示例 |
|------|------|------|
| `search_memory` | 语义搜索项目记忆 | "之前关于认证的坑是什么" |
| `search_capability` | 实时搜 npm/PyPI/Web 找 MCP | "我需要浏览器自动化 MCP" → 返回可 proxy/perm 安装的包 |
| `search_source` | 搜索合适的研究源 | "去哪找最新 AI 论文" |

### 斜杠命令

| 命令 | 用途 |
|------|------|
| `/sh-research <topic>` | 触发研究协议，结构化调研 |
| `/sh-remember` | 手动触发 MEMORY.md 维护 |
| `/sh-reflect` | 会话结束反思和知识蒸馏 |

### 自定义子 Agent

| Agent 类型 | 用途 |
|-----------|------|
| `sh-researcher` | 研究型 Agent，内置研究协议和研究纪律 |
| `sh-curator` | 记忆策展 Agent，输出格式化 MEMORY.md 更新建议 |

### 自动化

- **Stop Hook**: 会话结束时自动提醒更新 MEMORY.md
- **Wikilink**: ADR 和 Gotcha 拆分为独立记忆文件，通过 `[[wikilink]]` 交叉引用
