# Super Harness 向量检索系统

基于 SQLite-vec 的轻量级语义检索引擎，支持记忆、能力、研究源的向量化检索。

## 架构

```
vector-store/harness.db (SQLite 数据库)
├── memories          # 项目记忆
├── capabilities      # 能力注册表（Skill + MCP）
├── sources           # 研究源
├── *_vec             # 向量表（sqlite-vec）
└── *_fts             # 全文搜索表（BM25）
```

## 安装依赖

### 基础依赖（必需）

```bash
# SQLite 已内置于 Python
# 无需额外安装即可使用 BM25 全文搜索
```

### 向量检索依赖（推荐）

```bash
# 安装 sentence-transformers（用于文本嵌入）
pip install sentence-transformers

# 安装 sqlite-vec（用于向量相似度搜索）
pip install sqlite-vec
```

### 完整安装

```bash
pip install sentence-transformers sqlite-vec numpy
```

## 使用方法

### 1. 初始化数据库

```bash
cd "A:\project\super harness\tools\memory"
python init_db.py
```

这将：
- 创建数据库 schema
- 导入研究源（arXiv, DeepWiki, GitHub 等）
- 导入能力（从 manifest.json 或示例数据）

### 2. 语义搜索

```bash
# 搜索能力（混合检索：向量 + BM25）
python semantic_search.py search "代码审查"

# 只搜索 Skill
python semantic_search.py search-skill "测试"

# 只搜索 MCP
python semantic_search.py search-mcp "GitHub"
```

### 3. 基础数据库操作

```bash
# 添加记忆
python harness_db.py add-memory "项目使用 Python 3.10+"

# 搜索记忆
python harness_db.py search-memories "Python"

# 列出所有能力
python harness_db.py list-caps

# 列出所有研究源
python harness_db.py list-sources
```

## Python API

### 基础使用

```python
from harness_db import VectorStore

# 初始化
store = VectorStore()

# 添加记忆
memory_id = store.add_memory(
    content="项目使用 React + TypeScript",
    project_id="my-project"
)

# 搜索记忆
results = store.search_memories("React", project_id="my-project")
print(results)

store.close()
```

### 语义搜索

```python
from semantic_search import SemanticSearch

# 初始化（自动加载嵌入模型）
search = SemanticSearch()

# 语义搜索能力
results = search.semantic_search_capabilities(
    query="如何审查代码质量",
    type="skill",  # 可选：skill 或 mcp
    limit=10,
    vector_weight=0.7  # 向量权重（0-1）
)

for r in results:
    print(f"{r['name']}: {r['description']}")
    print(f"  分数: {r['final_score']:.3f}")

search.close()
```

## 检索策略

### 混合检索（推荐）

默认使用向量 + BM25 混合检索：
- **向量搜索**（70% 权重）：语义相似度，理解意图
- **BM25 搜索**（30% 权重）：关键词匹配，精确查找

```python
results = search.semantic_search_capabilities(
    query="代码审查",
    vector_weight=0.7  # 可调整
)
```

### 纯 BM25 检索

如果未安装 sentence-transformers，自动降级到 BM25：

```python
results = store.search_capabilities("代码审查")
```

## 数据模型

### memories（记忆）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 记忆 ID（自动生成） |
| project_id | TEXT | 项目 ID |
| content | TEXT | 记忆内容 |
| source_file | TEXT | 来源文件 |
| created_at | TEXT | 创建时间 |
| confidence | REAL | 置信度（0-1） |
| metadata | TEXT | 元数据（JSON） |

### capabilities（能力）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 能力 ID |
| name | TEXT | 能力名称 |
| type | TEXT | 类型（skill 或 mcp） |
| category | TEXT | 分类 |
| description | TEXT | 描述 |
| file_path | TEXT | 文件路径 |
| tags | TEXT | 标签（JSON 数组） |
| version | TEXT | 版本 |

### sources（研究源）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 源 ID |
| name | TEXT | 源名称 |
| type | TEXT | 类型 |
| description | TEXT | 描述 |
| file_path | TEXT | 文件路径 |
| tags | TEXT | 标签（JSON 数组） |

## 性能优化

### 嵌入模型选择

默认使用 `all-MiniLM-L6-v2`（轻量级，384 维）：
- 速度快
- 内存占用小
- 适合本地部署

如需更高精度，可切换到更大模型：

```python
search = SemanticSearch(model_name="all-mpnet-base-v2")  # 768 维
```

### 批量导入

大量数据导入时，建议使用事务：

```python
store = VectorStore()
for item in items:
    store.add_capability_with_embedding(**item)
store.close()  # 自动提交
```

## 故障排除

### sqlite-vec 扩展加载失败

```bash
# Windows
pip install sqlite-vec

# 如果仍然失败，系统会自动降级到纯 BM25 搜索
```

### sentence-transformers 模型下载慢

```bash
# 使用国内镜像
export HF_ENDPOINT=https://hf-mirror.com
python init_db.py
```

### 数据库锁定

```python
# 确保正确关闭连接
store = VectorStore()
try:
    # 操作
    pass
finally:
    store.close()
```

## 下一步

- [ ] 实现向量相似度搜索（需安装 sqlite-vec）
- [ ] 添加增量更新机制
- [ ] 支持多语言嵌入模型
- [ ] 实现记忆衰减和清理

## 许可证

MIT License
