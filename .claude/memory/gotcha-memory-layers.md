---
name: gotcha-memory-layers
description: 记忆系统分两层，验证时区分层级
metadata:
  type: project
  discovered: 2026-06-10
---

# 坑点: 记忆系统分两层，验证时分清层级

## 坑
`tools/memory/` 里的检索系统分两层：
- `harness_db.py` — SQLite + FTS5 基础检索（纯 Python，零额外依赖）
- `semantic_search.py` — 叠加向量检索（需要 sentence-transformers + sqlite-vec）

## 为什么是坑
代码语法检查通过 ≠ 端到端检索可用。如果没有安装 `sentence-transformers` 和 `sqlite-vec`，向量检索会静默降级到纯 BM25。你可能以为在做语义搜索，实际上只是关键词匹配。

## 正确的验证方法
1. 先跑 `python tools/memory/init_db.py` 确认数据库初始化
2. 跑 `python tools/memory/semantic_search.py search "代码审查"` 确认检索回路
3. 检查输出中是否有 `vec_score` 字段 — 有才是真正的向量检索
4. 没有 `vec_score` 说明在降级模式，需要安装依赖

## 关联
- [[adr-004-reme-memory]] — 向量检索是可选增强，降级方案是设计决策
