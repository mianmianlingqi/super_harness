# /sync-session — 同步当前会话到 Super Harness 记忆库

将当前 Claude Code 会话的 transcript 入库，使其可通过 MCP `search_sessions` 检索。

## 执行流程

### Step 1: 找到当前 transcript 文件

当前 transcript 文件路径格式为：
```
~/.claude/projects/<project-key>/<session-uuid>.jsonl
```

用 Glob 查找最近修改的 JSONL 文件：
```
Glob: ~/.claude/projects/**/*.jsonl
按修改时间排序，取最新的一个
```

### Step 2: 运行同步脚本

```bash
cd a:/project/super-harness
PYTHONPATH=tools/memory python tools/memory/sync_session.py "<transcript路径>"
```

### Step 3: 验证

```bash
cd a:/project/super-harness
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_sessions","arguments":{"lens":"restore-context","limit":3}}}' | PYTHONPATH="tools/memory" python .claude/mcp/harness_search.py 2>/dev/null
```

如果返回了 context_summary 数据，说明同步成功。

### 备选：同步任意 transcript

```bash
# 查找所有项目
ls -d ~/.claude/projects/*/

# 同步特定项目的最近会话
python tools/memory/sync_session.py "$(ls -t ~/.claude/projects/<key>/*.jsonl | head -1)"
```
