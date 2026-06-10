# /sh-find-tool — 搜索并安装外部 MCP/Skill

用 `search_capability` 在能力库中搜索匹配的外部工具，找到后辅助安装。

## 执行流程

### Step 1: 搜索

```
MCP search_capability(query="$ARGUMENTS", type="mcp")
```

如果结果中标记为"外部注册"的排在前面，说明本地没有安装但可以安装。

### Step 2: 判断是否需要安装

- 本地已有同名工具？→ 直接用
- 本地没有但外部有匹配？→ 进入 Step 3
- 无匹配？→ 告知用户，建议去 mcpservers.org 搜索

### Step 3: 安装

外部 MCP 通常通过以下方式安装：

**npx (Node.js)**:
```bash
npx -y <package-name>
```
然后在 `.mcp.json` 中添加配置。

**pip (Python)**:
```bash
pip install <package-name>
```

**uvx (Python uv)**:
```bash
uvx <package-name>
```

### Step 4: 配置

更新 `~/.claude/.mcp.json`:
```json
{
  "<server-name>": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "<package-name>"]
  }
}
```

重启 Claude Code 后生效。

## 已知映射（常见 MCP → 安装命令）

| MCP 名称 | 安装命令 |
|---------|------|
| Postgres/SQLite/MySQL/Redis | `npx -y @anthropic/mcp-<db>` |
| Playwright | `npx -y @playwright/mcp` |
| GitHub | `npx -y @anthropic/mcp-github` |
| Brave Search | `npx -y @anthropic/mcp-brave-search` |
| Context7 | `npx -y @anthropic/mcp-context7` |
| Filesystem | `npx -y @anthropic/mcp-filesystem` |
| Memory | `npx -y @anthropic/mcp-memory` |
| Fetch | `pip install mcp-server-fetch` |
| Docker | `npx -y @anthropic/mcp-docker` |
| Slack | `npx -y @anthropic/mcp-slack` |
