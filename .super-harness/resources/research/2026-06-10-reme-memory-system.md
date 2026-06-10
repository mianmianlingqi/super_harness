# ReMe 记忆系统深度调研 (2026-06-10)

> 来源: Web 搜索 + GitHub: agentscope-ai/ReMe

## 核心架构

ReMe 将记忆管理视为 AI Agent 任务本身（而非简单数据存取）：

```
Agent Memory = Long-Term Memory + Short-Term Memory
             = (Personal + Procedural + Tool) Memory + Working Memory
```

## 四层记忆

| 类型 | 用途 | Super Harness 对应 |
|------|------|--------------------|
| Personal | 用户偏好、习惯 | ❌ 缺乏（仅项目级） |
| Procedural | 可复用任务知识 | Gotcha + ADR（部分） |
| Tool | 工具调用统计 | ❌ 缺乏 |
| Working | 上下文管理 | ❌ 缺乏 |

## 关键技术

- **when_to_use 解耦** — 场景标签 vs 内容向量分离 → 解决"内容 ≠ 检索意图"
- **Draft → Retrieve → Dedup → Write** — LLM 驱动的语义去重写
- **混合检索** — 语义 0.7 + BM25 0.3 → Super Harness 已有相同设计
- **文件 + 向量双轨** → Super Harness 也是

## 实验效果

- Qwen3-8B + ReMe > 无记忆 Qwen3-14B（Avg@4 +8.83%）
- 工具记忆提升工具选择成功率 +14.88%

## 对 Super Harness 的启示

1. **工具记忆**是 Super Harness 的明显缺口 — 应该自动记录 MCP 使用统计
2. **工作记忆管理**（Offload/Reload）是差异化方向
3. ReMe 的 "when_to_use" 设计比 Super Harness 当前的纯内容检索更精准
4. Super Harness 的 wikilink 网络 + ReMe 的 LLM 驱动策略可以互补
