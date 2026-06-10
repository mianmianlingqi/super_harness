# MEMORY.md 最佳实践调研 (2026-06-10)

> 来源: Web 搜索 "AI coding agent enhancement protocol framework MEMORY.md best practices 2025 2026"

## 核心发现

### MEMORY.md 已成为行业标准模式

Claude Code v2.1.33 (2026年2月) 原生支持 MEMORY.md，200 行自动注入 agent system prompt。

### 三层记忆架构（最佳实践）

| 层 | 内容 | 检索策略 |
|----|------|---------|
| Tier 1: MEMORY.md | 精选长期记忆，200行硬上限 | 每次会话加载 |
| Tier 2: 每日笔记 | 时间边界事件日志 | 今天+昨天 |
| Tier 3: JSON 状态 | 结构化机器可读数据 | 按需加载 |

### 关键原则

1. **精选胜过数量** — 2K token 精选 > 25K token 全部 dump
2. **MEMORY.md 是索引** — 指向详细主题文件
3. **每次会话前后强制读/写** — 否则 agent 不知道自己有记忆
4. **Pre-compact hook 至关重要** — 上下文压缩前保存状态

### 常见失败模式

1. 记忆肥胖 — MEMORY.md 2000+ 行噪音
2. 记忆过期 — 旧模式从不清理
3. 失忆仍发生 — Agent 不读自己的记忆
4. 并发编辑冲突 — 多窗口编辑同一文件

### 与 Super Harness 的对比

| 特性 | MLM MEMORY.md 标准 | Super Harness |
|------|-------------------|---------------|
| 记忆存储 | 单文件 200 行 | 分散 wikilink 节点 |
| 检索方式 | 线性读取前 200 行 | BM25 + 向量混合检索 |
| 跨平台 | 依赖平台原生支持 | 适配器统一入口 |
| 知识组织 | 索引 + 主题文件 | ADR + Gotcha + 模块状态 |

## 行动建议

- Super Harness 的分散 wikilink + 向量检索方案在大型项目上比单文件方案有扩展性优势
- 可借鉴 "MEMORY.md 作为索引" 的模式 — MEMORY.md 指向独立文件
- 考虑加入 "记忆过期/清理" 机制（当前版本缺失）
