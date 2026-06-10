# Super Harness

> 一套让任何 AI Agent 都能跨平台工作的增强协议框架

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## 什么是 Super Harness？

Super Harness 是一个**文档驱动的 Agent 增强协议框架**。核心理念是：

**文档即协议** — Agent 读取文档后自动遵守协议，无需任何代码集成。

### 解决的问题

| 问题 | Super Harness 的解决方案 |
|------|------------------------|
| Agent 每次会话都从零开始 | MEMORY.md 持续积累项目知识 |
| Agent 不会主动制定计划 | PLANNING.md 提供思维工具箱 |
| Agent 不会主动调研 | RESEARCH.md 定义研究协议 |
| 能力（Skill/MCP）太多记不住 | CAPABILITIES.md 按需检索 |
| 需要动态加载外部 MCP | proxy_mcp 热加载，本轮即用 |

### 支持的平台

| 平台 | 入口文件 | 状态 |
|------|---------|------|
| Claude Code | `.claude/CLAUDE.md` | ✅ |

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/mianmianlingqi/super_harness.git
cd super_harness
```

### 2. 初始化中央仓库

```bash
# 创建中央仓库目录
mkdir -p ~/.super-harness

# 复制全局协议文档
cp SOUL.md ~/.super-harness/
cp PLANNING.md ~/.super-harness/
cp RESEARCH.md ~/.super-harness/
cp CAPABILITIES.md ~/.super-harness/

# 复制研究源和能力注册表
cp -r sources ~/.super-harness/
cp -r capabilities ~/.super-harness/
```

### 3. 初始化向量数据库（可选）

```bash
cd tools/memory

# 安装依赖
pip install sentence-transformers sqlite-vec

# 初始化数据库
python init_db.py

# 测试检索
python semantic_search.py search "代码审查"
```

### 4. 在任何 Agent 平台中使用

打开项目目录，Agent 会自动加载对应的适配器文件，进而读取全局协议和项目记忆。

## 架构

### 两层架构

```
~/.super-harness/                    # 中央仓库（全局共享）
├── SOUL.md                          # Agent 身份和价值观
├── PLANNING.md                      # 思维工具箱
├── RESEARCH.md                      # 研究协议
├── CAPABILITIES.md                  # 能力发现协议
├── sources/                         # 研究源注册表
│   ├── _index.md
│   ├── arxiv.md
│   ├── deepwiki.md
│   ├── github.md
│   ├── pypi.md
│   ├── npm.md
│   └── semantic-scholar.md
├── capabilities/                    # 能力注册表
│   ├── _index.md
│   ├── _manifest.json
│   ├── skills/                      # Skill 注册
│   └── mcp/                         # MCP 注册
├── memory/                          # 全局记忆
└── vector-store/                    # 向量数据库
    └── harness.db

your-project/                        # 项目目录（项目特有）
├── SOUL.md                          # 项目级灵魂（覆盖全局）
├── MEMORY.md                        # 项目级记忆
├── .harness.json                    # 项目配置
├── memory/                          # 项目级日志
├── plans/                           # 计划
│   ├── active/
│   └── done/
└── .claude/CLAUDE.md                 # 协议入口
```

### 四层协议体系

```
┌─────────────────────────────────────────────────────────┐
│                      SOUL.md                             │
│                  "我是谁，我相信什么"                      │
└────────────────────────┬────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
 ┌─────────────┐  ┌────────────┐  ┌──────────────┐
 │ PLANNING.md │  │RESEARCH.md │  │CAPABILITIES  │
 │ "怎么做事"   │  │"怎么学习"   │  │.md           │
 │             │  │            │  │"能做什么"     │
 │ 思维工具     │  │ 研究策略    │  │              │
 │ 判断矩阵     │  │ 研究纪律    │  │ 能力发现     │
 │ 红线规则     │  │ 回流协议    │  │ 检索策略     │
 └──────┬──────┘  └─────┬──────┘  └──────┬───────┘
        │               │                │
        └───────────────┼────────────────┘
                        ▼
               ┌─────────────────┐
               │   MEMORY.md     │
               │  "我知道什么"    │
               │                 │
               │  蒸馏后的项目知识 │
               └─────────────────┘
```

### 知识飞轮

```
做计划 → 执行 → 记录 → 蒸馏到记忆 → 下一个计划更好 → 循环
```

## 核心协议

### SOUL.md — Agent 身份

定义 Agent 的价值观、人格和行为准则：

- **核心价值观**：先想后做、比例匹配、记录决策、持续学习、不重新发明轮子
- **Agent 人格**：直接、有主见、务实、诚实、主动
- **行为准则**：工具先行、验证闭环、事实审计、记忆维护
- **红线**：不猜测、不假装成功、破坏性操作前必须确认

### PLANNING.md — 思维工具箱

提供**原则驱动**的计划制定方法（而非固定流程）：

- **判断矩阵**：根据任务复杂度自动选择计划深度
- **五个思维工具**：任务分解、风险预判、Trade-off 分析、探针实验、检查点
- **记忆联动**：计划前查记忆、计划中记日志、计划后回流记忆

### RESEARCH.md — 研究协议

定义如何学习和调研：

- **四种研究策略**：广度优先、深度优先、对比调研、探针验证
- **研究源发现**：从 `sources/_index.md` 查找合适的研究源
- **研究纪律**：引用来源、区分事实观点、时效性标注、不过度研究

### CAPABILITIES.md — 能力发现协议

定义如何发现和使用能力（Skill + MCP）：

- **按需检索**：需要时才查找，不全部加载
- **语义匹配**：用自然语言描述需求，找到最相关的能力
- **能力生命周期**：注册 → 活跃 → 验证/失效

## 向量检索系统

基于 SQLite + BM25 的轻量级语义检索引擎：

### 三张表

| 表名 | 用途 | 数据来源 |
|------|------|---------|
| `memories` | 项目记忆 | MEMORY.md + memory/*.md |
| `capabilities` | 能力注册表 | skills/ + mcp/ |
| `sources` | 研究源 | sources/*.md |

### 使用方法

```bash
cd tools/memory

# 初始化数据库
python init_db.py

# 搜索能力
python semantic_search.py search "代码审查"

# 只搜索 Skill
python semantic_search.py search-skill "测试"

# 只搜索 MCP
python semantic_search.py search-mcp "GitHub"

# 列出所有能力
python harness_db.py list-caps

# 列出所有研究源
python harness_db.py list-sources
```

### Python API

```python
from semantic_search import SemanticSearch

# 初始化（自动加载嵌入模型）
search = SemanticSearch()

# 语义搜索能力
results = search.semantic_search_capabilities(
    query="如何审查代码质量",
    type="skill",  # 可选：skill 或 mcp
    limit=10,
    vector_weight=0.7  # 向量权重（0-1）
)

for r in results:
    print(f"{r['name']}: {r['description']}")
    print(f"  分数: {r['final_score']:.3f}")

search.close()
```

## 研究源

| 源 | 类型 | 擅长 |
|----|------|------|
| arXiv | 学术 | 最新论文、SOTA 方法 |
| Semantic Scholar | 学术 | 论文引用网络、影响力排序 |
| GitHub | 代码 | 开源项目、参考实现 |
| DeepWiki | 代码 | 项目架构文档、设计思路 |
| PyPI | 包生态 | Python 包发现 |
| npm | 包生态 | Node.js 包发现 |

添加新研究源：

1. 在 `sources/` 下创建 `{name}.md`（参考标准格式）
2. 更新 `sources/_index.md`
3. 做一次测试查询验证

## Claude Code 深度集成

Super Harness 在 Claude Code 中利用原生接口实现了深度增强：

### 接口利用一览

```
.claude/
├── CLAUDE.md              ← 协议入口（静态文档）
├── settings.json           ← Hooks + MCP Server 注册
├── hooks/
│   └── session_close.py   ← Stop Hook：会话结束提醒更新 MEMORY.md
├── commands/
│   ├── sh-research.md     ← /sh-research：研究协议
│   ├── sh-remember.md     ← /sh-remember：记忆维护
│   └── sh-reflect.md      ← /sh-reflect：会话反思
├── agents/
│   ├── sh-researcher.md   ← 研究型子 Agent
│   └── sh-curator.md      ← 记忆策展子 Agent
├── mcp/
│   └── harness_search.py  ← MCP Server：语义搜索
└── memory/
    ├── adr-001-doc-driven.md  ← ADR wikilink 记忆节点
    ├── adr-002-principle-driven.md
    ├── adr-003-centralized.md
    ├── adr-004-reme-memory.md
    ├── gotcha-mcp-language-match.md
    └── gotcha-db-init-before-mcp.md
```

### MCP Server — 语义搜索

MCP Server `super-harness` 将 `tools/memory/` 的检索能力暴露为 Claude Code 可调用的工具：

| 工具 | 功能 | 内部引擎 |
|------|------|---------|
| `search_memory` | 语义搜索项目记忆 | BM25 (FTS5) |
| `search_capability` | 语义搜索能力（Skill/MCP） | BM25 + 向量混合检索 |
| `search_source` | 语义搜索研究源 | BM25 (FTS5) |

### 斜杠命令

| 命令 | 协议 | 说明 |
|------|------|------|
| `/sh-research <topic>` | RESEARCH.md | 结构化调研，选择最佳研究源，输出可执行报告 |
| `/sh-remember` | MEMORY.md | 手动触发记忆维护，检查坑点/ADR/约定/状态变化 |
| `/sh-reflect` | MEMORY.md | 会话结束反思，蒸馏经验到长期记忆 |

### 自定义子 Agent

| Agent 类型 | 用途 |
|-----------|------|
| `sh-researcher` | 内置研究协议的子 Agent，自动查阅研究源注册表，输出有出处的研究报告 |
| `sh-curator` | 内置记忆维护协议的子 Agent，从会话中提取经验，输出格式化 MEMORY.md 更新建议 |

### 自动化

- **Stop Hook**: 会话结束时自动调用 `session_close.py`，检查 MEMORY.md 是否更新，输出维护清单
- **Wikilink 知识网络**: ADR 和 Gotcha 拆分为独立记忆文件，Claude Code 通过 `[[wikilink]]` 自动关联加载

---

## 如何扩展

### 添加新研究源

```markdown
# sources/new-source.md

## 元信息
- **类型**: 学术 / 代码 / 标准 / 包生态 / 社区
- **接入方式**: MCP Server / REST API / CLI / Web Search
- **认证**: 无需 / API Key / OAuth
- **速率限制**: X 次/分钟

## 何时使用
- 场景 1
- 场景 2

## 查询方法
{具体的查询语法/示例}
```

### 添加新能力（Skill/MCP）

```markdown
# capabilities/skills/new-skill.md

## 描述
{一段自然语言描述，这是向量检索的主要匹配字段}

## 触发场景
- 当用户说"..."时
- 当任务涉及...时

## 输入
| 参数 | 类型 | 必须 | 说明 |
|------|------|------|------|

## 输出
{这个能力产出什么}
```

## 关键决策记录

| ADR | 决策 | 理由 |
|-----|------|------|
| ADR-001 | 文档驱动而非代码驱动 | 任何 Agent 平台都能读 |
| ADR-002 | 原则驱动而非流程驱动 | 复杂任务需要灵活性 |
| ADR-003 | 中央化存储 | MCP/Skill/研究源是跨项目共享的 |
| ADR-004 | 基于 ReMe 的记忆系统 | 文件即记忆的理念最贴近需求 |
| ADR-005 | SQLite + BM25 作为检索基础 | 轻量级，向量检索作为可选增强 |

## 项目状态

| 模块 | 状态 | 说明 |
|------|------|------|
| 全局协议文档 | ✅ SHIPPED | SOUL + PLANNING + RESEARCH + CAPABILITIES |
| 研究源注册 | ✅ SHIPPED | 6 个初始源 |
| 能力注册表 | ✅ SHIPPED | 初始结构 |
| 向量检索系统 | ✅ SHIPPED | SQLite + BM25 |
| MCP 代理 | ✅ SHIPPED | proxy_mcp 动态热加载 |
| ReMe Fork | ✅ SHIPPED | tools/memory/ |

## 依赖

### 核心依赖（无需安装）

- Python 3.10+（SQLite 内置）
- Markdown 阅读器（任何文本编辑器）

### 可选依赖（向量检索）

```bash
pip install sentence-transformers sqlite-vec numpy
```

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 致谢

- [ReMe](https://github.com/agentscope-ai/ReMe) - 文件即记忆的理念
- [HwpForge](https://github.com/ai-screams/HwpForge) - MEMORY.md 结构设计
- [super-todo](https://github.com/slashwhy/super-todo) - Plan-Based Handoff
- [Nessie](https://github.com/UnlikeOtherAI/Nessie) - Plan + PlanStep 模型
- [pikakit/agent-skills](https://github.com/pikakit/agent-skills) - INPUT→OUTPUT→VERIFY

---

**Super Harness — 让任何 AI Agent 都能跨平台工作**
