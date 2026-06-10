---
name: adr-003-centralized
description: ADR-003: 选择中央化存储
metadata:
  type: project
  date: 2026-06-09
  status: accepted
---

# ADR-003: 选择中央化存储

- **日期**: 2026-06-09
- **状态**: ✅ accepted

## 正题
项目内嵌更方便，所有文件都在一个仓库里，不需要额外的全局路径。

## 反题
MCP Server、Skill、研究源是跨项目共享的资源。如果每个项目都内嵌一份，维护成本 N×M，且无法全局升级。

## 合题
中央仓库 `~/.super-harness/` 存放全局共享的协议、研究源、能力注册表、记忆和向量索引。项目目录通过 `.harness.json` 指向中央仓库，项目级 SOUL.md 和 MEMORY.md 可覆盖全局配置。

## 影响
- 中央仓库位于 `~/.super-harness/`
- 项目通过 `.harness.json` 中的 `hub` 字段连接
- 全局升级一次，所有项目受益
- MCP/Skill/研究源不重复维护

## 关联
- [[adr-004-reme-memory]] — ReMe 的记忆系统也采用中央化思路
