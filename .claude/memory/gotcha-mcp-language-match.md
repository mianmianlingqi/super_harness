---
name: gotcha-mcp-language-match
description: MCP 搜索语言必须和数据库内容语言匹配
metadata:
  type: project
  discovered: 2026-06-10
---

# 坑点: MCP 搜索语言必须和数据库内容语言匹配

## 坑
MCP Server `search_capability` 和 `search_source` 使用 SQLite FTS5 全文搜索（BM25）。FTS5 的 `MATCH` 是基于词匹配的，用英文查询搜中文内容会返回空结果。

## 为什么是坑
你可能以为搜索 "code review" 能找到「代码审查」，但 FTS5 不做语义翻译。中文内容需要用中文查询。

## 正确的做法
1. 查询时使用与数据库中内容一致的语言
2. 安装 `sentence-transformers` 后，向量检索可以在一定程度上跨越语言障碍
3. 未来可以考虑在 FTS5 查询前做关键词翻译

## 关联
- [[gotcha-memory-layers]] — 没有向量检索时就是纯 BM25 关键词匹配
- [[adr-004-reme-memory]] — 向量检索作为可选增强可以缓解这个问题
