# /sh-research — Super Harness 研究协议

触发研究协议，对 `$ARGUMENTS` 进行结构化调研。

## 执行流程

### Step 1: 选择研究源

先读 `~/.super-harness/sources/_index.md`，根据主题类型选择最合适的源：

| 主题类型 | 推荐源 | 查询方式 |
|---------|--------|---------|
| 最新算法/方法 | arXiv → Semantic Scholar | WebSearch + WebFetch |
| 参考实现/开源项目 | GitHub → DeepWiki | WebSearch + WebFetch |
| 选技术栈/库 | PyPI/npm → GitHub | WebSearch |
| 理解项目架构 | DeepWiki → GitHub | WebFetch |
| 评估论文影响力 | Semantic Scholar → arXiv | WebSearch |

也可以用 MCP 工具 `search_source` 查询匹配的研究源：
```
search_source(query="$ARGUMENTS")
```

### Step 2: 执行研究

根据选定的源执行研究：
- 学术类：搜索最新论文、SOTA 方法、引用网络
- 代码类：搜索开源项目、参考实现、架构文档
- 包生态：搜索可用库、版本对比、社区活跃度

### Step 3: 输出报告

按研究纪律输出结构化报告：

```markdown
# 调研报告: $ARGUMENTS

**日期**: YYYY-MM-DD
**研究源**: [列出使用的源]

## 结论（先说结论）

[1-3 句话的核心发现]

## 详细发现

### [发现 1]
- **事实**: ...
- **来源**: [URL/引用]
- **观点**: ...（标注为观点）

### [发现 2]
...

## 可执行建议

1. [具体可执行的下一步]
2. ...

## 局限

- [本次调研未覆盖的方面]
```

**研究纪律**：
- 每个结论必须有出处（URL 或引用）
- 区分「事实」和「观点」
- 标注调研日期
- 研究结果要落地到可执行步骤
- 不过度研究 — 找到足够决策的信息就停
