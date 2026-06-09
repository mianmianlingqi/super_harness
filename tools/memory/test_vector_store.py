#!/usr/bin/env python3
"""
Super Harness 向量检索系统测试脚本
验证所有核心功能是否正常工作
"""

import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from harness_db import VectorStore
from semantic_search import SemanticSearch


def test_basic_operations():
    """测试基础数据库操作"""
    print("=" * 60)
    print("测试 1: 基础数据库操作")
    print("=" * 60)
    
    store = VectorStore()
    
    # 测试添加记忆
    print("\n1.1 添加记忆...")
    memory_id = store.add_memory(
        content="项目使用 Python 3.10+ 和 FastAPI 框架",
        project_id="test-project"
    )
    print(f"✓ 记忆已添加: {memory_id}")
    
    # 测试搜索记忆
    print("\n1.2 搜索记忆...")
    results = store.search_memories("Python")
    print(f"✓ 找到 {len(results)} 个结果")
    for r in results[:3]:
        print(f"  - {r['content'][:50]}...")
    
    # 测试列出能力
    print("\n1.3 列出所有能力...")
    caps = store.get_all_capabilities()
    print(f"✓ 共有 {len(caps)} 个能力")
    for cap in caps[:3]:
        print(f"  - {cap['name']} [{cap['type']}]")
    
    # 测试列出研究源
    print("\n1.4 列出所有研究源...")
    sources = store.get_all_sources()
    print(f"✓ 共有 {len(sources)} 个研究源")
    for source in sources[:3]:
        print(f"  - {source['name']} [{source['type']}]")
    
    store.close()
    print("\n✓ 基础操作测试通过\n")


def test_semantic_search():
    """测试语义搜索"""
    print("=" * 60)
    print("测试 2: 语义搜索")
    print("=" * 60)
    
    search = SemanticSearch()
    
    # 测试搜索能力
    print("\n2.1 搜索能力（关键词: '测试'）...")
    results = search.semantic_search_capabilities("测试", limit=5)
    print(f"✓ 找到 {len(results)} 个结果")
    for r in results[:3]:
        print(f"  - {r['name']}: {r['description'][:40]}...")
        print(f"    分数: {r.get('final_score', 0):.3f}")
    
    # 测试按类型过滤
    print("\n2.2 搜索 Skill（关键词: '代码'）...")
    results = search.semantic_search_capabilities("代码", type="skill", limit=5)
    print(f"✓ 找到 {len(results)} 个 Skill")
    for r in results[:3]:
        print(f"  - {r['name']} [{r['type']}]")
    
    print("\n2.3 搜索 MCP（关键词: 'GitHub'）...")
    results = search.semantic_search_capabilities("GitHub", type="mcp", limit=5)
    print(f"✓ 找到 {len(results)} 个 MCP")
    for r in results[:3]:
        print(f"  - {r['name']} [{r['type']}]")
    
    search.close()
    print("\n✓ 语义搜索测试通过\n")


def test_database_stats():
    """测试数据库统计"""
    print("=" * 60)
    print("测试 3: 数据库统计")
    print("=" * 60)
    
    store = VectorStore()
    
    # 统计各表数据量
    cursor = store.conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM memories")
    memories_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM capabilities")
    caps_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM sources")
    sources_count = cursor.fetchone()[0]
    
    print(f"\n数据库统计:")
    print(f"  - 记忆: {memories_count} 条")
    print(f"  - 能力: {caps_count} 个")
    print(f"  - 研究源: {sources_count} 个")
    
    # 检查向量支持
    print(f"\n向量支持:")
    print(f"  - sqlite-vec: {'✓ 已安装' if store.has_vec else '✗ 未安装'}")
    
    search = SemanticSearch()
    print(f"  - sentence-transformers: {'✓ 已安装' if search.model else '✗ 未安装'}")
    print(f"  - 嵌入维度: {search.embedding_dim}")
    search.close()
    
    store.close()
    print("\n✓ 数据库统计测试通过\n")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Super Harness 向量检索系统测试")
    print("=" * 60 + "\n")
    
    try:
        test_basic_operations()
        test_semantic_search()
        test_database_stats()
        
        print("=" * 60)
        print("✓ 所有测试通过")
        print("=" * 60)
        print("\n下一步:")
        print("  1. 安装向量检索依赖（可选）:")
        print("     pip install sentence-transformers sqlite-vec")
        print("  2. 重新初始化数据库以启用向量检索:")
        print("     python init_db.py")
        print("  3. 测试语义搜索:")
        print("     python semantic_search.py search '代码审查'")
        print()
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
