---
name: gotcha-db-init-before-mcp
description: MCP Server 启动前需确保数据库已初始化
metadata:
  type: project
  discovered: 2026-06-10
---

# 坑点: MCP Server 启动前需确保数据库已初始化

## 坑
MCP Server `harness_search.py` 在启动时自动创建数据库 schema（`_init_schema`），但不会自动导入数据。如果 `init_db.py` 从未运行过，`search_capability` 和 `search_source` 会返回空结果，`search_memory` 也查不到任何记忆。

## 为什么是坑
MCP Server 启动没有报错，工具列表也正常，但查什么都是空。你会以为是搜索算法有问题，其实是数据库是空的。

## 正确的做法
1. 部署时先运行 `python tools/memory/init_db.py` 一次
2. 可以写一个 `pre_startup` hook 自动检查数据库是否有数据
3. 在没有数据时，MCP 工具应该在结果中附带提示：「数据库可能未初始化」

## 关联
- [[gotcha-memory-layers]] — 同样是「能跑」≠ 「数据到位」
