#!/usr/bin/env python3
"""
Super Harness 数据库初始化脚本
将研究源和能力导入向量数据库
"""

import json
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from semantic_search import SemanticSearch


def init_sources():
    """初始化研究源"""
    print("=" * 60)
    print("初始化研究源")
    print("=" * 60)
    
    search = SemanticSearch()
    
    sources = [
        {
            "name": "arXiv",
            "type": "academic",
            "description": "最新学术论文、SOTA 方法、前沿研究",
            "file_path": "sources/arxiv.md",
            "tags": ["论文", "学术", "AI", "机器学习"]
        },
        {
            "name": "DeepWiki",
            "type": "code",
            "description": "开源项目架构文档、设计思路、代码解析",
            "file_path": "sources/deepwiki.md",
            "tags": ["代码", "架构", "文档", "开源"]
        },
        {
            "name": "GitHub",
            "type": "code",
            "description": "开源项目、参考实现、代码趋势、Star 排行",
            "file_path": "sources/github.md",
            "tags": ["代码", "开源", "项目", "实现"]
        },
        {
            "name": "PyPI",
            "type": "package",
            "description": "Python 包发现、版本管理、依赖信息",
            "file_path": "sources/pypi.md",
            "tags": ["Python", "包", "依赖", "版本"]
        },
        {
            "name": "npm",
            "type": "package",
            "description": "Node.js 包发现、版本管理、依赖信息",
            "file_path": "sources/npm.md",
            "tags": ["Node.js", "JavaScript", "包", "依赖"]
        },
        {
            "name": "Semantic Scholar",
            "type": "academic",
            "description": "论文引用网络、影响力排序、相关论文发现",
            "file_path": "sources/semantic-scholar.md",
            "tags": ["论文", "引用", "学术", "影响力"]
        }
    ]
    
    for source in sources:
        try:
            source_id = search.add_source(**source)
            print(f"✓ {source['name']} ({source_id})")
        except Exception as e:
            print(f"✗ {source['name']}: {e}")
    
    search.close()
    print(f"\n✓ 已导入 {len(sources)} 个研究源\n")


def init_capabilities():
    """初始化能力（从 manifest.json）"""
    print("=" * 60)
    print("初始化能力")
    print("=" * 60)
    
    manifest_path = Path.home() / ".super-harness" / "capabilities" / "_manifest.json"
    
    if not manifest_path.exists():
        print(f"警告: manifest 文件不存在: {manifest_path}")
        print("跳过能力初始化")
        return
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    capabilities = manifest.get('capabilities', [])
    
    if not capabilities:
        print("manifest 中没有能力定义")
        return
    
    search = SemanticSearch()
    
    for cap in capabilities:
        try:
            cap_id = search.add_capability_with_embedding(
                name=cap['name'],
                type=cap['type'],
                description=cap['description'],
                file_path=cap['file'],
                category=cap.get('category'),
                tags=cap.get('tags'),
                version=cap.get('version')
            )
            print(f"✓ {cap['name']} ({cap_id})")
        except Exception as e:
            print(f"✗ {cap['name']}: {e}")
    
    search.close()
    print(f"\n✓ 已导入 {len(capabilities)} 个能力\n")


def init_sample_capabilities():
    """初始化示例能力（用于测试）"""
    print("=" * 60)
    print("初始化示例能力")
    print("=" * 60)
    
    search = SemanticSearch()
    
    sample_caps = [
        {
            "name": "代码审查",
            "type": "skill",
            "description": "审查代码质量、安全性、性能问题，提供改进建议",
            "file_path": "capabilities/skills/code-review.md",
            "category": "quality",
            "tags": ["代码", "审查", "质量", "安全"]
        },
        {
            "name": "GitHub PR 管理",
            "type": "mcp",
            "description": "创建、审查、合并 GitHub Pull Request，管理代码评审流程",
            "file_path": "capabilities/mcp/github.md",
            "category": "devops",
            "tags": ["GitHub", "PR", "代码评审", "版本控制"]
        },
        {
            "name": "数据库查询",
            "type": "mcp",
            "description": "执行 SQL 查询、分析数据库结构、优化查询性能",
            "file_path": "capabilities/mcp/database.md",
            "category": "data",
            "tags": ["数据库", "SQL", "查询", "分析"]
        },
        {
            "name": "单元测试生成",
            "type": "skill",
            "description": "自动生成单元测试、提高代码覆盖率、测试边界情况",
            "file_path": "capabilities/skills/test-generation.md",
            "category": "testing",
            "tags": ["测试", "单元测试", "覆盖率", "自动化"]
        },
        {
            "name": "文档生成",
            "type": "skill",
            "description": "生成 API 文档、README、技术文档，支持多种格式",
            "file_path": "capabilities/skills/doc-generation.md",
            "category": "documentation",
            "tags": ["文档", "API", "README", "生成"]
        }
    ]
    
    for cap in sample_caps:
        try:
            cap_id = search.add_capability_with_embedding(**cap)
            print(f"✓ {cap['name']} ({cap_id})")
        except Exception as e:
            print(f"✗ {cap['name']}: {e}")
    
    search.close()
    print(f"\n✓ 已导入 {len(sample_caps)} 个示例能力\n")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Super Harness 数据库初始化")
    print("=" * 60 + "\n")
    
    # 初始化数据库
    print("初始化数据库 schema...")
    search = SemanticSearch()
    print(f"✓ 数据库路径: {search.db_path}")
    print(f"✓ 嵌入维度: {search.embedding_dim}")
    print(f"✓ 向量支持: {search.has_vec}\n")
    search.close()
    
    # 初始化研究源
    init_sources()
    
    # 初始化能力
    init_capabilities()
    
    # 如果没有真实能力，导入示例
    manifest_path = Path.home() / ".super-harness" / "capabilities" / "_manifest.json"
    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        if not manifest.get('capabilities'):
            init_sample_capabilities()
    else:
        init_sample_capabilities()
    
    print("=" * 60)
    print("✓ 初始化完成")
    print("=" * 60)
    print("\n下一步:")
    print("  1. 测试语义搜索: python semantic_search.py search '代码审查'")
    print("  2. 查看研究源: python harness_db.py list-sources")
    print("  3. 查看能力: python harness_db.py list-caps")
    print()


if __name__ == "__main__":
    main()
