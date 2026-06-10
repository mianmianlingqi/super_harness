# /sh-prepare — 任务前资源库准备

在执行任务之前，先完成知识储备。五阶段流水线：

## 执行流程

### Phase 1: 信息搜集（并行）

同时启动以下搜索：

**Web 搜索**（了解领域现状和最佳实践）:
```
MCP search_web(query="$ARGUMENTS 最佳实践 最新方案", limit=10)
MCP search_web(query="$ARGUMENTS tutorial guide 2025 2026", limit=10)
```

**研究源匹配**（找论文和参考实现）:
```
MCP search_source(query="$ARGUMENTS")
```

**能力发现**（找可用的 skill 和 MCP）:
```
MCP search_capability(query="$ARGUMENTS")
```

### Phase 2: 资源下载（→ 项目 .super-harness/resources/）

所有资源永久存储在项目中：

```
项目根/.super-harness/resources/
├── INDEX.md           # 自动维护的资源索引
├── docs/              # 下载的参考文档
├── references/        # 克隆的参考项目
├── mcp/               # 项目级 MCP 配置（永久）
│   └── <name>.json    # 每个 MCP 一个配置文件
├── skills/            # 项目级 Skill（永久）
│   └── <name>/SKILL.md
├── capabilities.md    # 本项目常用 skill/MCP 映射
└── research/          # 调研笔记 (YYYY-MM-DD.md)
```

**下载参考文档**:
```bash
mkdir -p .super-harness/resources/docs
for url in <top_urls>; do
  name=$(echo "$url" | md5sum | cut -c1-12)
  curl -sL "$url" | python -c "
import sys, re
html = sys.stdin.read()
html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL)
html = re.sub(r'<[^>]+>', ' ', html)
print(re.sub(r'\s+', ' ', html)[:30000])
" > ".super-harness/resources/docs/${name}.md"
done
```

**克隆参考项目**:
```bash
mkdir -p .super-harness/resources/references
cd .super-harness/resources/references
git clone --depth=1 <repo_url>
```

### Phase 3: 工具永久沉淀（核心改造）

发现有用的外部 MCP 和 Skill → **永久安装到项目资源库**：

```
# 永久安装 MCP
MCP perm_mcp_install(
  name="playwright", 
  command="npx", 
  args=["-y","@playwright/mcp"], 
  description="浏览器自动化测试"
)

# 永久安装 Skill  
MCP perm_skill_install(
  name="my-deploy",
  description="项目部署脚本",
  content="---\nname: my-deploy\ndescription: 部署到生产环境\n---\n\n# 部署检查清单\n..."
)
```

**决策矩阵**：
| 场景 | 做法 |
|------|------|
| 项目反复使用的工具 | → `perm_mcp_install` (永久) |
| 仅本次试用的工具 | → `proxy_mcp` (本轮即用，不存储) |
| 需要全局跨项目使用 | → 手动加到 `~/.claude/.mcp.json` |
| 项目专用的工作流 | → `perm_skill_install` (永久) |

**存储位置**：`.super-harness/resources/mcp/` 和 `.super-harness/resources/skills/`
**生命周期**：跨会话永久保留，SessionStart 自动检测，可 Git 版本控制

### Phase 4: 能力映射更新

将新安装的工具记录到 `capabilities.md`：

```bash
# 自动更新能力映射（扫描 mcp/ 和 skills/ 目录）
cd a:/project/super-harness
PYTHONPATH=tools/memory python -c "
from mcp_proxy import list_project_mcps, list_project_skills
from pathlib import Path

root = Path('项目根路径')
mcps = list_project_mcps(str(root))
skills = list_project_skills(str(root))

# 更新 capabilities.md
lines = ['# 本项目常用能力\n']
lines.append(f'\n## 项目 MCP ({len(mcps)})\n')
lines.append('| MCP | 安装命令 | 用途 |\n|-----|---------|------|\n')
for m in mcps:
    cmd = f\"{m['command']} {' '.join(m.get('args',[]))}\"
    lines.append(f\"| {m['name']} | {cmd} | {m.get('description','')} |\n\")

lines.append(f'\n## 项目 Skill ({len(skills)})\n')
lines.append('| Skill | 用途 |\n|-------|------|\n')
for s in skills:
    lines.append(f\"| {s['name']} | {s.get('description','')} |\n\")

(root / '.super-harness/resources/capabilities.md').write_text(''.join(lines))
print(f'✅ 能力映射已更新: {len(mcps)} MCP + {len(skills)} Skill')
"
```

### Phase 5: 知识索引

将收集到的文档和新工具索引到向量库：

```bash
cd a:/project/super-harness
PYTHONPATH=tools/memory python -c "
from semantic_search import SemanticSearch
from pathlib import Path
import hashlib

sem = SemanticSearch()
task_id = '$TASK_ID'
docs_dir = Path('resources')

for md_file in docs_dir.glob('*.md'):
    content = md_file.read_text(encoding='utf-8')
    chunks = [content[i:i+1000] for i in range(0, len(content), 1000)]
    for j, chunk in enumerate(chunks[:5]):  # 最多 5 块
        sem.add_memory(
            content=chunk,
            project_id=f'temp:{task_id}',
            source_file=str(md_file)
        )
sem.close()
"
```

### Phase 6: 准备就绪报告

输出结构化报告：

```markdown
## 资源库准备完成: $ARGUMENTS

### 搜集到的信息
- Web 搜索结果: N 条
- 研究源推荐: [列表]
- 参考项目: [列表]
- 文档: [列表]

### 可用的工具
- 本地 Skill: [列表]
- 热加载 MCP: [列表]  

### 参考代码
- [项目 1] — [相关文件/模块]
- [项目 2] — [相关文件/模块]

### 关键发现
1. [发现 1]
2. [发现 2]

### 建议方案
[基于搜集信息的推荐方案]

---
开始执行任务。
```

## 永久存储（全部在项目中）

**所有资源存储在项目 `.super-harness/resources/` 中，跨会话保留，可 Git 追踪。**

| 目录 | 内容 | 生命周期 |
|------|------|---------|
| `docs/` | 参考文档 | 永久（6月后标注过时） |
| `references/` | 克隆项目 (`git pull` 更新) | 永久 |
| `mcp/` | MCP 配置 (`.json`) | 永久，SessionStart 检测 |
| `skills/` | Skill 定义 (`SKILL.md`) | 永久，SessionStart 检测 |
| `research/` | 调研笔记 (`YYYY-MM-DD.md`) | 永久 |
| `capabilities.md` | 能力映射总览 | 自动更新 |

下次打开项目时 SessionStart hook 自动：
- 加载 INDEX.md 索引
- 列出项目 MCP（含使用次数）
- 列出项目 Skill（含描述摘要）
- 提示激活方式

```bash
# 查看项目资源库
cat .super-harness/resources/INDEX.md
ls .super-harness/resources/mcp/
ls .super-harness/resources/skills/
python a:/project/super-harness/tools/memory/mcp_proxy.py list
```
