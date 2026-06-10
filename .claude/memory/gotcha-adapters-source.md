---
name: gotcha-adapters-source
description: 适配器维护只有一份真源
metadata:
  type: project
  discovered: 2026-06-10
---

# 坑点: 适配器维护只有一份真源

## 坑
各平台入口文件（`.claude/CLAUDE.md`、`AGENTS.md`、`.cursorrules` 等）虽然内容相同，但它们是**生成产物**，不是手动维护的。

## 为什么是坑
如果直接修改某个平台文件（比如 `GEMINI.md`），下次运行 `adapters/generate.py` 时会被覆盖。如果不运行生成器，不同平台的内容会漂移。

## 正确的做法
1. 修改 `adapters/template.md`（唯一真源）
2. 运行 `python adapters/generate.py` 重新生成所有适配器
3. 确认所有平台文件内容一致

## 关联
- [[adr-001-doc-driven]] — 单模板驱动的设计是文档驱动的具体体现
