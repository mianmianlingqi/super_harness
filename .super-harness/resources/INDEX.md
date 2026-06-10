# Super Harness — 项目资源库索引

> 最后更新: 2026-06-10
> 自动由 /sh-prepare 和 SessionStart hook 维护

## 目录结构

```
.super-harness/resources/
├── INDEX.md              ← 本文件
├── capabilities.md       ← 能力映射
├── docs/                 ← 参考文档
├── mcp/                  ← 项目级 MCP 配置（永久）
├── skills/               ← 项目级 Skill（永久）
├── references/           ← 克隆的参考项目
└── research/             ← 调研笔记
```

## 调研笔记

| 日期 | 主题 | 文件 |
|------|------|------|
| 2026-06-10 | MEMORY.md 最佳实践 | research/2026-06-10-memory-best-practices.md |
| 2026-06-10 | 多平台适配器生态 | research/2026-06-10-multi-platform-ecosystem.md |
| 2026-06-10 | ReMe 记忆系统 | research/2026-06-10-reme-memory-system.md |

## 参考文档

（待下载）

## 参考项目

（待克隆）

## 项目安装的工具

详见 [capabilities.md](capabilities.md)

## 快速命令

```bash
# 查看所有资源
ls .super-harness/resources/

# 列出项目 MCP
ls .super-harness/resources/mcp/

# 列出项目 Skill
ls .super-harness/resources/skills/

# 查看最新调研
ls -t .super-harness/resources/research/ | head -5
```

| 2026-06-10 | mcp | playwright | 本地 | browser automation |
| 2026-06-10 | skill | my-code-review | 本地 | code review skill |