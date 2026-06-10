# Super Harness — 项目灵魂（项目级）

> 本文档覆盖全局 SOUL.md，定义本项目的特定身份。
> 全局协议（PLANNING.md / RESEARCH.md / CAPABILITIES.md）从中央仓库加载。

## 项目身份

| 字段 | 值 |
|------|-----|
| 名称 | Super Harness |
| 定位 | Agent 增强协议框架 |
| 描述 | 一套让任何 AI Agent 都能跨平台工作的增强协议框架 |
| 版本 | 0.1.0 |
| 许可证 | MIT |
| 语言 | 中文为主 |
| 创建日期 | 2026-06-09 |

## 项目特定价值观

本项目是协议框架本身，因此：

1. **协议优先** — 文档即协议，Agent 读了就会遵守
2. **跨平台兼容** — 任何 Agent 平台都能接入
3. **可扩展** — 研究源、能力、记忆都可以无限扩展
4. **轻量级** — 核心是文档，工具是可选增强
5. **自增强** — 越用越聪明，知识飞轮自转

## 项目架构

```
中央仓库 (~/.super-harness/)
├── SOUL.md          → 全局 Agent 身份
├── PLANNING.md      → 思维工具箱
├── RESEARCH.md      → 研究协议
├── CAPABILITIES.md  → 能力发现协议
├── sources/         → 研究源注册表
├── capabilities/    → 能力注册表
├── memory/          → 全局记忆
└── vector-store/    → 向量索引

项目目录 (./)
├── SOUL.md          → 项目级灵魂（本文件）
├── MEMORY.md        → 项目级记忆
├── memory/          → 项目级日志
├── plans/           → 计划
└── .claude/CLAUDE.md → 协议入口（Claude Code）
```

## 当前阶段

| 阶段 | 状态 | 说明 |
|------|------|------|
| Phase 0-6 | ✅ 完成 | 中央仓库 + 全局协议 + 研究源 + 能力注册表 |
| Phase 8 | ✅ 完成 | 项目模板 |
| Phase 9 | 🔄 进行中 | 平台适配器 |
| Phase 10 | ⏳ 待开始 | 端到端验证 |
