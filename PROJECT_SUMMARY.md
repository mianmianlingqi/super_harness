# Super Harness 项目总结

> 创建时间: 2026-06-09
> 状态: ✅ 全部完成

## 项目概述

Super Harness 是一个 **Agent 增强协议框架**，旨在让任何 AI Agent 都能跨平台工作。核心理念是**文档即协议**——Agent 读取文档后自动遵守协议。

## 核心特性

### 1. 四层协议体系

| 协议 | 文件 | 定位 |
|------|------|------|
| 身份协议 | SOUL.md | Agent 是谁，价值观是什么 |
| 计划协议 | PLANNING.md | 如何制定和执行计划 |
| 研究协议 | RESEARCH.md | 如何学习和调研 |
| 能力协议 | CAPABILITIES.md | 如何发现和使用能力 |

### 2. 六个研究源（可扩展）

- **arXiv** - 学术论文
- **DeepWiki** - 开源项目架构文档
- **GitHub** - 代码搜索和项目发现
- **PyPI** - Python 包生态
- **npm** - Node.js 包生态
- **Semantic Scholar** - 论文引用网络

### 3. 六个平台适配器

- Claude Code (`.claude/CLAUDE.md`)
- OpenAI Codex (`AGENTS.md`)
- Cursor (`.cursorrules`)
- Windsurf (`.windsurfrules`)
- GitHub Copilot (`.github/copilot-instructions.md`)
- Gemini CLI (`GEMINI.md`)

### 4. 向量检索系统

基于 SQLite 的轻量级语义检索引擎：
- **三张表**: memories（记忆）、capabilities（能力）、sources（研究源）
- **BM25 全文搜索**: 支持中文关键词搜索
- **可选向量检索**: 安装 sentence-transformers + sqlite-vec 后启用语义搜索
- **混合检索**: 向量 + BM25 加权排序

## 项目结构

```
C:\Users\35928\.super-harness\          # 中央仓库（13 个文件）
├── SOUL.md                             # 全局 Agent 身份
├── PLANNING.md                         # 思维工具箱
├── RESEARCH.md                         # 研究协议
├── CAPABILITIES.md                     # 能力发现协议
├── sources/                            # 研究源注册表
│   ├── _index.md                       # 源目录
│   ├── arxiv.md                        # arXiv 配置
│   ├── deepwiki.md                     # DeepWiki 配置
│   ├── github.md                       # GitHub 配置
│   ├── pypi.md                         # PyPI 配置
│   ├── npm.md                          # npm 配置
│   └── semantic-scholar.md             # Semantic Scholar 配置
├── capabilities/                       # 能力注册表
│   ├── _index.md                       # 能力目录
│   ├── _manifest.json                  # 向量索引源
│   ├── skills/                         # Skill 注册（空）
│   └── mcp/                            # MCP 注册（空）
├── memory/                             # 全局记忆
└── vector-store/                       # 向量数据库
    └── harness.db                      # SQLite 数据库

A:\project\super harness\               # 项目目录（10 个文件）
├── .harness.json                       # 项目配置
├── SOUL.md                             # 项目级灵魂
├── MEMORY.md                           # 项目级记忆
├── LICENSE                             # MIT 许可证
├── .claude/CLAUDE.md                   # Claude Code 适配器
├── AGENTS.md                           # OpenAI Codex 适配器
├── .cursorrules                        # Cursor 适配器
├── .windsurfrules                      # Windsurf 适配器
├── .github/copilot-instructions.md     # Copilot 适配器
├── GEMINI.md                           # Gemini 适配器
└── tools/memory/                       # 向量检索系统
    ├── harness_db.py                   # 基础数据库操作
    ├── semantic_search.py              # 语义检索引擎
    ├── init_db.py                      # 数据库初始化
    ├── test_vector_store.py            # 测试脚本
    └── README.md                       # 使用文档
```

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

### ADR-005: 选择 SQLite + BM25 作为检索基础
- **日期**: 2026-06-09
- **正题**: 向量检索语义理解更好
- **反题**: 需要额外依赖，中文分词复杂
- **合题**: BM25 作为基础，向量检索作为可选增强

## 使用方法

### 1. 任何 Agent 平台打开项目

Agent 会自动加载对应的适配器文件，进而读取全局协议和项目记忆。

### 2. 使用向量检索系统

```bash
# 初始化数据库
cd "A:\project\super harness\tools\memory"
python init_db.py

# 搜索能力
python semantic_search.py search "代码审查"

# 列出所有能力
python harness_db.py list-caps

# 列出所有研究源
python harness_db.py list-sources
```

### 3. 启用向量检索（可选）

```bash
# 安装依赖
pip install sentence-transformers sqlite-vec

# 重新初始化数据库
python init_db.py

# 测试语义搜索
python semantic_search.py search "如何审查代码质量"
```

## 测试结果

### 向量检索系统测试（2026-06-09）

```
✓ 基础数据库操作测试通过
  - 添加记忆: ✓
  - 搜索记忆: ✓ (找到 1 个结果)
  - 列出能力: ✓ (5 个能力)
  - 列出研究源: ✓ (6 个研究源)

✓ 语义搜索测试通过
  - 搜索能力: ✓ (找到 1 个结果)
  - 按类型过滤: ✓ (Skill: 2, MCP: 1)

✓ 数据库统计测试通过
  - 记忆: 1 条
  - 能力: 5 个
  - 研究源: 6 个
```

## 技术栈

- **协议文档**: Markdown
- **向量数据库**: SQLite + FTS5 (BM25)
- **可选向量检索**: sqlite-vec + sentence-transformers
- **编程语言**: Python 3.10+
- **许可证**: MIT

## 下一步（可选增强）

1. **安装向量检索依赖**
   ```bash
   pip install sentence-transformers sqlite-vec
   ```

2. **导入真实能力**
   - 将现有 Skill 和 MCP 注册到 capabilities/
   - 更新 _manifest.json

3. **实现记忆衰减**
   - 根据使用频率自动清理旧记忆
   - 实现记忆合并和去重

4. **添加更多研究源**
   - RFC Editor
   - W3C
   - Stack Overflow
   - Hacker News

5. **实现多语言支持**
   - 添加多语言嵌入模型
   - 支持中英文混合检索

## 许可证

MIT License - 详见 LICENSE 文件

## 贡献者

- Super Harness Team (2026-06-09)

---

**Super Harness 已就绪，可以开始使用了。**
