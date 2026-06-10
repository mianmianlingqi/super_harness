---
name: adr-005-zero-dep-mcp
description: ADR-005: 选择零依赖自实现 MCP Server
metadata:
  type: project
  date: 2026-06-10
  status: accepted
---

# ADR-005: 选择零依赖自实现 MCP Server

- **日期**: 2026-06-10
- **状态**: ✅ accepted

## 正题
使用官方 `mcp` Python SDK 可以更快开发，API 更规范，有社区支持。

## 反题
`mcp` SDK 在 Python 3.9 下不可用（pip 找不到匹配版本）。引入 SDK 依赖意味着不是所有环境都能跑。Super Harness 的核心哲学是「零依赖可用」。

## 合题
在 `.claude/mcp/harness_search.py` 中自实现最小化的 JSON-RPC 2.0 over stdin/stdout 协议（~100 行），直接调用已有的 `VectorStore` 和 `SemanticSearch` 类。MCP 协议足够简单，不需要 SDK。

## 影响
- `harness_search.py` 零第三方依赖，仅需 Python 3.9+ 标准库
- JSON-RPC 实现简洁透明，出问题容易调试
- 向量检索仍是可选的（需要 sentence-transformers），降级到纯 BM25
- 如果未来 MCP SDK 可用，可以无痛迁移

## 关联
- [[adr-001-doc-driven]] — 零依赖是文档驱动哲学的延伸
- [[adr-004-reme-memory]] — 同样选择了降级方案优先的设计
