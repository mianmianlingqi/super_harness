---
name: adr-002-principle-driven
description: ADR-002: 选择原则驱动而非流程驱动
metadata:
  type: project
  date: 2026-06-09
  status: accepted
---

# ADR-002: 选择原则驱动而非流程驱动

- **日期**: 2026-06-09
- **状态**: ✅ accepted

## 正题
固定流程保证一致性，每个 Agent 每次做同样的事得到同样的结果。

## 反题
复杂任务千变万化，固定流程要么过于繁琐（简单任务），要么不够用（复杂任务）。Agent 需要的是判断框架而非死流程。

## 合题
提供思维工具箱和判断矩阵，让 Agent 根据任务复杂度自己决定怎么做。PLANNING.md 提供五个思维工具（任务分解、风险预判、Trade-off 分析、探针实验、检查点），Agent 按需取用。

## 影响
- 不对 Agent 的执行流程做硬性约束
- 不同复杂度的任务获得不同深度的处理
- 对 Agent 自身能力要求较高（需要能判断复杂度）

## 关联
- [[adr-001-doc-driven]] — 同样是「信任 Agent 的判断」优于「强制执行」
