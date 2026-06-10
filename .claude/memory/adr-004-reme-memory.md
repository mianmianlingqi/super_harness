---
name: adr-004-reme-memory
description: ADR-004: 选择 ReMe 作为记忆系统基础
metadata:
  type: project
  date: 2026-06-09
  status: accepted
---

# ADR-004: 选择 ReMe 作为记忆系统基础

- **日期**: 2026-06-09
- **状态**: ✅ accepted

## 正题
ReMe 的文件即记忆（一个文件一个事实）理念非常契合 Super Harness 的文档驱动哲学。

## 反题
ReMe 依赖 agentscope 框架，这个依赖可能限制了可用性。

## 合题
Fork ReMe 的核心思想（文件即记忆 + SQLite 索引 + 向量检索），保留核心逻辑但封装隔离，不引入 agentscope 依赖。实现为 `tools/memory/harness_db.py`（SQLite+FTS5）和 `semantic_search.py`（可选向量检索）。

## 影响
- 记忆系统分两层：`harness_db.py` 基础检索 + `semantic_search.py` 语义增强
- 三张表：memories、capabilities、sources
- 向量检索通过 sentence-transformers 和 sqlite-vec 可选启用
- 降级方案：纯 BM25 全文搜索（零额外依赖）

## 关联
- [[adr-003-centralized]] — 记忆数据库存储在中央仓库的 vector-store/
- [[gotcha-memory-layers]] — 验证时要分清楚「语法可解析」和「端到端跑通」
