# Gemini CLI Agent 指南

本项目使用 Super Harness 协议。

## 全局协议（从中央仓库加载）

@C:\Users\35928\.super-harness\SOUL.md
@C:\Users\35928\.super-harness\PLANNING.md
@C:\Users\35928\.super-harness\RESEARCH.md
@C:\Users\35928\.super-harness\CAPABILITIES.md

## 项目文档

@SOUL.md
@MEMORY.md

## 会话协议

1. **会话开始时**：读取 SOUL.md + MEMORY.md
2. **收到任务时**：检查是否需要制定计划（见 PLANNING.md 判断矩阵）
3. **需要调研时**：查阅 RESEARCH.md 和 sources/_index.md
4. **需要能力时**：检索 capabilities/ 中的 Skill 和 MCP
5. **会话结束时**：更新 MEMORY.md 中的相关板块

## 记忆维护

每次会话结束时，检查 MEMORY.md 是否需要更新：
- 新的坑点 → Critical Gotchas
- 架构变更 → Architecture
- 新的编码模式 → Coding Conventions
- 项目状态变化 → 模块状态表
- 经验教训 → 记入当日日志 memory/YYYY-MM-DD.md

## 能力检索

当需要某个能力时，查询 `~/.super-harness/capabilities/` 中的 Skill 和 MCP。

## 研究源检索

当需要调研时，查询 `~/.super-harness/sources/_index.md` 找到合适的研究源。
