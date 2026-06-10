---
name: adr-001-doc-driven
description: ADR-001: 选择文档驱动而非代码驱动
metadata:
  type: project
  date: 2026-06-09
  status: accepted
---

# ADR-001: 选择文档驱动而非代码驱动

- **日期**: 2026-06-09
- **状态**: ✅ accepted

## 正题
代码框架可以强制执行规则，保证约束不被绕过。

## 反题
文档更灵活，任何 Agent 平台都能读，不需要特定 SDK 集成。核心是 Agent 理解了就会遵守。

## 合题
文档即协议，工具是可选增强。Super Harness 的核心是 Markdown 文件，向量检索、MCP 等都是可选增强，不是必须依赖。

## 影响
- 所有协议文档用 Markdown 编写
- 不同平台的适配器只是同一份模板的生成结果
- 不需要任何 SDK 或运行时依赖
- 软约束而非硬约束：Agent 读了自觉遵守，Agent 忽略了就失去效力

## 关联
- [[adr-002-principle-driven]] — 同样选择了灵活性优于强制
- [[adr-003-centralized]] — 中央仓库同样是文档驱动的产物
