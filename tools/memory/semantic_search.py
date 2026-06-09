#!/usr/bin/env python3
"""
Super Harness 语义检索引擎
支持向量嵌入 + BM25 混合检索

依赖：
- sentence-transformers (用于文本嵌入)
- sqlite-vec (用于向量相似度搜索)
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import hashlib

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    HAS_EMBEDDING = True
except ImportError:
    HAS_EMBEDDING = False
    np = None  # 占位符，避免 NameError
    print("警告: sentence-transformers 未安装，向量检索不可用")
    print("安装: pip install sentence-transformers")


class SemanticSearch:
    """语义检索引擎"""
    
    def __init__(self, db_path: str = None, model_name: str = "all-MiniLM-L6-v2"):
        """
        初始化语义检索引擎
        
        Args:
            db_path: 数据库路径
            model_name: 嵌入模型名称（默认使用轻量级模型）
        """
        if db_path is None:
            hub_path = Path.home() / ".super-harness" / "vector-store"
            hub_path.mkdir(parents=True, exist_ok=True)
            db_path = str(hub_path / "harness.db")
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        # 加载嵌入模型
        if HAS_EMBEDDING:
            print(f"加载嵌入模型: {model_name}")
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
        else:
            self.model = None
            self.embedding_dim = 384  # 默认维度
        
        self._init_schema()
    
    def _init_schema(self):
        """初始化数据库 schema（包含向量表）"""
        cursor = self.conn.cursor()
        
        # 创建基础表（如果不存在）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                content TEXT NOT NULL,
                source_file TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS capabilities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                category TEXT,
                description TEXT NOT NULL,
                file_path TEXT NOT NULL,
                tags TEXT,
                version TEXT,
                last_verified TEXT,
                created_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT NOT NULL,
                file_path TEXT NOT NULL,
                tags TEXT,
                created_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # 创建向量表（使用 sqlite-vec）
        try:
            # memories 向量表
            cursor.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_vec USING vec0(
                    id TEXT PRIMARY KEY,
                    embedding FLOAT[{self.embedding_dim}]
                )
            """)
            
            # capabilities 向量表
            cursor.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS capabilities_vec USING vec0(
                    id TEXT PRIMARY KEY,
                    embedding FLOAT[{self.embedding_dim}]
                )
            """)
            
            # sources 向量表
            cursor.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS sources_vec USING vec0(
                    id TEXT PRIMARY KEY,
                    embedding FLOAT[{self.embedding_dim}]
                )
            """)
            
            self.has_vec = True
        except Exception as e:
            print(f"警告: 无法创建向量表: {e}")
            self.has_vec = False
        
        # 创建全文搜索表
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                content,
                content='memories',
                content_rowid='rowid'
            )
        """)
        
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS capabilities_fts USING fts5(
                name, description, tags,
                content='capabilities',
                content_rowid='rowid'
            )
        """)
        
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS sources_fts USING fts5(
                name, description, tags,
                content='sources',
                content_rowid='rowid'
            )
        """)
        
        self.conn.commit()
    
    def _embed(self, text: str):
        """生成文本嵌入向量"""
        if not HAS_EMBEDDING:
            raise RuntimeError("sentence-transformers 未安装")
        return self.model.encode(text)
    
    def _generate_id(self, content: str) -> str:
        """生成内容 ID"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def add_capability_with_embedding(self, name: str, type: str, description: str,
                                     file_path: str, category: str = None,
                                     tags: List[str] = None, version: str = None,
                                     metadata: Dict = None) -> str:
        """添加能力并生成嵌入向量"""
        cap_id = self._generate_id(f"{type}:{name}")
        now = datetime.utcnow().isoformat()
        
        cursor = self.conn.cursor()
        
        # 插入主表
        cursor.execute("""
            INSERT OR REPLACE INTO capabilities 
            (id, name, type, category, description, file_path, tags, version,
             last_verified, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cap_id, name, type, category, description, file_path,
              json.dumps(tags) if tags else None, version, now, now,
              json.dumps(metadata) if metadata else None))
        
        # 插入全文搜索表
        cursor.execute("""
            INSERT OR REPLACE INTO capabilities_fts (rowid, name, description, tags)
            VALUES ((SELECT rowid FROM capabilities WHERE id = ?), ?, ?, ?)
        """, (cap_id, name, description, json.dumps(tags) if tags else None))
        
        # 生成并插入嵌入向量
        if HAS_EMBEDDING and self.has_vec:
            embedding = self._embed(f"{name} {description}")
            cursor.execute("""
                INSERT OR REPLACE INTO capabilities_vec (id, embedding)
                VALUES (?, ?)
            """, (cap_id, embedding.tobytes()))
        
        self.conn.commit()
        return cap_id
    
    def add_source(self, name: str, type: str, description: str,
                   file_path: str, tags: List[str] = None,
                   metadata: Dict = None) -> str:
        """
        添加研究源
        
        Args:
            name: 源名称
            type: 类型
            description: 描述
            file_path: 文件路径
            tags: 标签列表
            metadata: 元数据
            
        Returns:
            源 ID
        """
        source_id = self._generate_id(f"source:{name}")
        now = datetime.utcnow().isoformat()
        
        cursor = self.conn.cursor()
        
        # 插入主表
        cursor.execute("""
            INSERT OR REPLACE INTO sources 
            (id, name, type, description, file_path, tags, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (source_id, name, type, description, file_path,
              json.dumps(tags) if tags else None, now,
              json.dumps(metadata) if metadata else None))
        
        # 插入全文搜索表
        cursor.execute("""
            INSERT OR REPLACE INTO sources_fts (rowid, name, description, tags)
            VALUES ((SELECT rowid FROM sources WHERE id = ?), ?, ?, ?)
        """, (source_id, name, description, json.dumps(tags) if tags else None))
        
        # 生成并插入嵌入向量（如果可用）
        if HAS_EMBEDDING and self.has_vec:
            embedding = self._embed(f"{name} {description}")
            cursor.execute("""
                INSERT OR REPLACE INTO sources_vec (id, embedding)
                VALUES (?, ?)
            """, (source_id, embedding.tobytes()))
        
        self.conn.commit()
        return source_id
    
    def semantic_search_capabilities(self, query: str, type: str = None,
                                    limit: int = 10, 
                                    vector_weight: float = 0.7) -> List[Dict]:
        """
        语义搜索能力（混合检索：向量 + BM25）
        
        Args:
            query: 查询文本
            type: 类型过滤（skill 或 mcp）
            limit: 返回数量
            vector_weight: 向量搜索权重（0-1），BM25 权重为 1-vector_weight
            
        Returns:
            匹配的能力列表（按相关性排序）
        """
        if not HAS_EMBEDDING or not self.has_vec:
            # 降级到纯 BM25 搜索
            return self._bm25_search_capabilities(query, type, limit)
        
        cursor = self.conn.cursor()
        
        # 1. 向量相似度搜索
        query_embedding = self._embed(query)
        
        vec_sql = """
            SELECT c.*, 
                   1 - vec_distance_cosine(cv.embedding, ?) as vec_score
            FROM capabilities c
            JOIN capabilities_vec cv ON c.id = cv.id
        """
        vec_params = [query_embedding.tobytes()]
        
        if type:
            vec_sql += " WHERE c.type = ?"
            vec_params.append(type)
        
        vec_sql += " ORDER BY vec_score DESC LIMIT ?"
        vec_params.append(limit * 2)  # 多取一些用于混合排序
        
        cursor.execute(vec_sql, vec_params)
        vec_results = {row['id']: dict(row) for row in cursor.fetchall()}
        
        # 2. BM25 全文搜索
        bm25_sql = """
            SELECT c.*, fts.rank as bm25_score
            FROM capabilities c
            JOIN capabilities_fts fts ON c.rowid = fts.rowid
            WHERE capabilities_fts MATCH ?
        """
        bm25_params = [query]
        
        if type:
            bm25_sql += " AND c.type = ?"
            bm25_params.append(type)
        
        bm25_sql += " ORDER BY fts.rank LIMIT ?"
        bm25_params.append(limit * 2)
        
        cursor.execute(bm25_sql, bm25_params)
        bm25_results = {row['id']: dict(row) for row in cursor.fetchall()}
        
        # 3. 混合排序（RRF - Reciprocal Rank Fusion）
        all_ids = set(vec_results.keys()) | set(bm25_results.keys())
        scored_results = []
        
        for cap_id in all_ids:
            vec_score = vec_results.get(cap_id, {}).get('vec_score', 0)
            bm25_score = bm25_results.get(cap_id, {}).get('bm25_score', 0)
            
            # 归一化 BM25 分数（rank 是负数，越小越好）
            bm25_normalized = 1 / (1 + abs(bm25_score)) if bm25_score else 0
            
            # 加权混合
            final_score = (vector_weight * vec_score + 
                          (1 - vector_weight) * bm25_normalized)
            
            result = vec_results.get(cap_id) or bm25_results.get(cap_id)
            result['final_score'] = final_score
            result['vec_score'] = vec_score
            result['bm25_score'] = bm25_score
            scored_results.append(result)
        
        # 按最终分数排序
        scored_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return scored_results[:limit]
    
    def _bm25_search_capabilities(self, query: str, type: str = None,
                                 limit: int = 10) -> List[Dict]:
        """纯 BM25 搜索（降级方案）"""
        cursor = self.conn.cursor()
        
        # 尝试 FTS5 搜索
        try:
            sql = """
                SELECT c.*, fts.rank
                FROM capabilities c
                JOIN capabilities_fts fts ON c.rowid = fts.rowid
                WHERE capabilities_fts MATCH ?
            """
            params = [query]
            
            if type:
                sql += " AND c.type = ?"
                params.append(type)
            
            sql += " ORDER BY fts.rank LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            # 如果 FTS5 返回结果，直接返回
            if results:
                return results
        except Exception:
            pass  # FTS5 搜索失败，降级到 LIKE 搜索
        
        # 降级到 LIKE 搜索（支持中文）
        sql = """
            SELECT c.*
            FROM capabilities c
            WHERE (c.name LIKE ? OR c.description LIKE ? OR c.tags LIKE ?)
        """
        like_query = f"%{query}%"
        params = [like_query, like_query, like_query]
        
        if type:
            sql += " AND c.type = ?"
            params.append(type)
        
        sql += " LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()


def init_from_manifest(manifest_path: str = None):
    """
    从 manifest.json 初始化数据库
    
    Args:
        manifest_path: manifest 文件路径
    """
    if manifest_path is None:
        manifest_path = Path.home() / ".super-harness" / "capabilities" / "_manifest.json"
    
    if not Path(manifest_path).exists():
        print(f"错误: manifest 文件不存在: {manifest_path}")
        return
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    search = SemanticSearch()
    
    print(f"从 manifest 导入 {len(manifest.get('capabilities', []))} 个能力...")
    
    for cap in manifest.get('capabilities', []):
        try:
            cap_id = search.add_capability_with_embedding(
                name=cap['name'],
                type=cap['type'],
                description=cap['description'],
                file_path=cap['file'],
                category=cap.get('category'),
                tags=cap.get('tags'),
                version=cap.get('version'),
                metadata=cap.get('metadata')
            )
            print(f"  ✓ {cap['name']} ({cap_id})")
        except Exception as e:
            print(f"  ✗ {cap['name']}: {e}")
    
    search.close()
    print("✓ 导入完成")


def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python semantic_search.py <command> [args]")
        print("\n命令:")
        print("  init                    - 初始化数据库")
        print("  import-manifest         - 从 manifest.json 导入能力")
        print("  search <query>          - 语义搜索能力")
        print("  search-skill <query>    - 搜索 Skill")
        print("  search-mcp <query>      - 搜索 MCP")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "init":
        search = SemanticSearch()
        print(f"✓ 数据库已初始化: {search.db_path}")
        print(f"  嵌入维度: {search.embedding_dim}")
        print(f"  向量支持: {search.has_vec}")
        search.close()
    
    elif cmd == "import-manifest":
        init_from_manifest()
    
    elif cmd in ["search", "search-skill", "search-mcp"]:
        if len(sys.argv) < 3:
            print("错误: 缺少 query 参数")
            sys.exit(1)
        
        query = sys.argv[2]
        type_filter = None
        
        if cmd == "search-skill":
            type_filter = "skill"
        elif cmd == "search-mcp":
            type_filter = "mcp"
        
        search = SemanticSearch()
        results = search.semantic_search_capabilities(query, type=type_filter)
        
        print(f"\n找到 {len(results)} 个结果:\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. {r['name']} [{r['type']}]")
            print(f"   描述: {r['description']}")
            print(f"   分数: {r.get('final_score', 0):.3f}")
            print(f"   文件: {r['file_path']}")
            print()
        
        search.close()
    
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
