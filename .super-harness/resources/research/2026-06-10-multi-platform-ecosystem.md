# 多平台 Agent 适配器生态调研 (2026-06-10)

> 来源: Web 搜索 "Claude Code Cursor Windsurf Copilot multi-platform agent adapter rules SDK"

## 竞品对比

| 工具 | 平台数 | 核心特性 |
|------|--------|---------|
| **agent-framework-cli** v3.6.0 | 5 | Spec 驱动 + 5-Agent 团队 |
| **agent-rules-kit** v3.8.1 | 9+ | 栈感知规则 + MCP 集成 |
| **ai-rulez** v4.1.1 | 18-19 | 单一 YAML → 多平台 |
| **rule-porter** v2.0.5 | 6 | 双向转换，零依赖 |
| **dotagent** v2.10.0 | 15 | 统一 .agent/ 目录格式 |

## 趋势

行业方向明确是 **"写一次，到处部署"** — 单一真源生成所有平台的 native 格式。

## Super Harness 的定位

Super Harness 走的是**协议优先**路线，差异在于：

- 竞品：工具做适配（CLI 做转换）
- Super Harness：文档即协议（Agent 读了就遵守，无需转换工具）

**优势**: 零工具门槛，Agent 自己读
**劣势**: 依赖 Agent 的阅读能力，无法做复杂的格式转换
