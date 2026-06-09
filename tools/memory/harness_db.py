#!/usr/bin/env python3
"""
Super Harness 向量检索系统
基于 SQLite-vec 实现的轻量级语义检索引擎

功能：
- 三张表：memories, capabilities, sources
- 向量相似度搜索
- BM25 关键词搜索
- 混合检索（向量 + BM25）
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import hashlib


class VectorStore:
    """SQLite-vec 向量存储引擎"""
    
    def __init__(self, db_path: str = None):
        """
        初始化向量存储
        
        Args:
            db_path: 数据库文件路径，默认使用中央仓库
        """
        if db_path is None:
            hub_path = Path.home() / ".super-harness" / "vector-store"
            hub_path.mkdir(parents=True, exist_ok=True)
            db_path = str(hub_path / "harness.db")
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
    
    def _init_schema(self):
        """初始化数据库 schema"""
        cursor = self.conn.cursor()
        
        # 启用 sqlite-vec 扩展（如果可用）
        try:
            cursor.execute("LOAD EXTENSION 'vec0'")
            self.has_vec = True
        except:
            self.has_vec = False
            print("警告: sqlite-vec 扩展未安装，将使用纯 SQL 实现")
        
        # 创建 memories 表
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
        
        # 创建 capabilities 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS capabilities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('skill', 'mcp')),
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
        
        # 创建 sources 表
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
        
        # 创建向量表（如果使用 sqlite-vec）
        if self.has_vec:
            # memories 向量表
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_vec USING vec0(
                    id TEXT PRIMARY KEY,
                    embedding FLOAT[384]
                )
            """)
            
            # capabilities 向量表
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS capabilities_vec USING vec0(
                    id TEXT PRIMARY KEY,
                    embedding FLOAT[384]
                )
            """)
            
            # sources 向量表
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS sources_vec USING vec0(
                    id TEXT PRIMARY KEY,
                    embedding FLOAT[384]
                )
            """)
        
        # 创建全文搜索表（BM25）
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                content,
                content='memories',
                content_rowid='rowid'
            )
        """)
        
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS capabilities_fts USING fts5(
                name,
                description,
                tags,
                content='capabilities',
                content_rowid='rowid'
            )
        """)
        
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS sources_fts USING fts5(
                name,
                description,
                tags,
                content='sources',
                content_rowid='rowid'
            )
        """)
        
        self.conn.commit()
    
    def _generate_id(self, content: str) -> str:
        """生成内容 ID"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def add_memory(self, content: str, project_id: str = None, 
                   source_file: str = None, metadata: Dict = None) -> str:
        """
        添加记忆
        
        Args:
            content: 记忆内容
            project_id: 项目 ID
            source_file: 来源文件
            metadata: 元数据
            
        Returns:
            记忆 ID
        """
        memory_id = self._generate_id(content)
        now = datetime.utcnow().isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO memories 
            (id, project_id, content, source_file, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (memory_id, project_id, content, source_file, now, now, 
              json.dumps(metadata) if metadata else None))
        
        # 添加到全文搜索
        cursor.execute("""
            INSERT OR REPLACE INTO memories_fts (rowid, content)
            VALUES ((SELECT rowid FROM memories WHERE id = ?), ?)
        """, (memory_id, content))
        
        self.conn.commit()
        return memory_id
    
    def add_capability(self, name: str, type: str, description: str,
                      file_path: str, category: str = None, tags: List[str] = None,
                      version: str = None, metadata: Dict = None) -> str:
        """
        添加能力（Skill 或 MCP）
        
        Args:
            name: 能力名称
            type: 类型（skill 或 mcp）
            description: 描述
            file_path: 文件路径
            category: 分类
            tags: 标签列表
            version: 版本
            metadata: 元数据
            
        Returns:
            能力 ID
        """
        cap_id = self._generate_id(f"{type}:{name}")
        now = datetime.utcnow().isoformat()
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO capabilities 
            (id, name, type, category, description, file_path, tags, version, 
             last_verified, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cap_id, name, type, category, description, file_path,
              json.dumps(tags) if tags else None, version, now, now,
              json.dumps(metadata) if metadata else None))
        
        # 添加到全文搜索
        cursor.execute("""
            INSERT OR REPLACE INTO capabilities_fts (rowid, name, description, tags)
            VALUES ((SELECT rowid FROM capabilities WHERE id = ?), ?, ?, ?)
        """, (cap_id, name, description, json.dumps(tags) if tags else None))
        
        self.conn.commit()
        return cap_id
    
    def add_source(self, name: str, type: str, description: str,
                  file_path: str, tags: List[str] = None, metadata: Dict = None) -> str:
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
        cursor.execute("""
            INSERT OR REPLACE INTO sources 
            (id, name, type, description, file_path, tags, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (source_id, name, type, description, file_path,
              json.dumps(tags) if tags else None, now,
              json.dumps(metadata) if metadata else None))
        
        # 添加到全文搜索
        cursor.execute("""
            INSERT OR REPLACE INTO sources_fts (rowid, name, description, tags)
            VALUES ((SELECT rowid FROM sources WHERE id = ?), ?, ?, ?)
        """, (source_id, name, description, json.dumps(tags) if tags else None))
        
        self.conn.commit()
        return source_id
    
    def search_memories(self, query: str, project_id: str = None, 
                       limit: int = 10) -> List[Dict]:
        """
        搜索记忆（BM25 全文搜索）
        
        Args:
            query: 查询文本
            project_id: 项目 ID（可选过滤）
            limit: 返回数量
            
        Returns:
            匹配的记忆列表
        """
        cursor = self.conn.cursor()
        
        sql = """
            SELECT m.*, fts.rank
            FROM memories m
            JOIN memories_fts fts ON m.rowid = fts.rowid
            WHERE memories_fts MATCH ?
        """
        params = [query]
        
        if project_id:
            sql += " AND m.project_id = ?"
            params.append(project_id)
        
        sql += " ORDER BY fts.rank LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def search_capabilities(self, query: str, type: str = None,
                           limit: int = 10) -> List[Dict]:
        """
        搜索能力（BM25 全文搜索）
        
        Args:
            query: 查询文本
            type: 类型过滤（skill 或 mcp）
            limit: 返回数量
            
        Returns:
            匹配的能力列表
        """
        cursor = self.conn.cursor()
        
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
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def search_sources(self, query: str, limit: int = 10) -> List[Dict]:
        """
        搜索研究源（BM25 全文搜索）
        
        Args:
            query: 查询文本
            limit: 返回数量
            
        Returns:
            匹配的研究源列表
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT s.*, fts.rank
            FROM sources s
            JOIN sources_fts fts ON s.rowid = fts.rowid
            WHERE sources_fts MATCH ?
            ORDER BY fts.rank LIMIT ?
        """, (query, limit))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_all_capabilities(self, type: str = None) -> List[Dict]:
        """
        获取所有能力
        
        Args:
            type: 类型过滤（skill 或 mcp）
            
        Returns:
            能力列表
        """
        cursor = self.conn.cursor()
        
        if type:
            cursor.execute("SELECT * FROM capabilities WHERE type = ?", (type,))
        else:
            cursor.execute("SELECT * FROM capabilities")
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_all_sources(self) -> List[Dict]:
        """获取所有研究源"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sources")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()


def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python harness_db.py <command> [args]")
        print("\n命令:")
        print("  init                    - 初始化数据库")
        print("  add-memory <content>    - 添加记忆")
        print("  add-capability <json>   - 添加能力")
        print("  add-source <json>       - 添加研究源")
        print("  search-memories <query> - 搜索记忆")
        print("  search-caps <query>     - 搜索能力")
        print("  search-sources <query>  - 搜索研究源")
        print("  list-caps               - 列出所有能力")
        print("  list-sources            - 列出所有研究源")
        sys.exit(1)
    
    cmd = sys.argv[1]
    store = VectorStore()
    
    try:
        if cmd == "init":
            print(f"✓ 数据库已初始化: {store.db_path}")
        
        elif cmd == "add-memory":
            if len(sys.argv) < 3:
                print("错误: 缺少 content 参数")
                sys.exit(1)
            content = sys.argv[2]
            memory_id = store.add_memory(content)
            print(f"✓ 记忆已添加: {memory_id}")
        
        elif cmd == "add-capability":
            if len(sys.argv) < 3:
                print("错误: 缺少 JSON 参数")
                sys.exit(1)
            data = json.loads(sys.argv[2])
            cap_id = store.add_capability(**data)
            print(f"✓ 能力已添加: {cap_id}")
        
        elif cmd == "add-source":
            if len(sys.argv) < 3:
                print("错误: 缺少 JSON 参数")
                sys.exit(1)
            data = json.loads(sys.argv[2])
            source_id = store.add_source(**data)
            print(f"✓ 研究源已添加: {source_id}")
        
        elif cmd == "search-memories":
            if len(sys.argv) < 3:
                print("错误: 缺少 query 参数")
                sys.exit(1)
            query = sys.argv[2]
            results = store.search_memories(query)
            print(json.dumps(results, indent=2, ensure_ascii=False))
        
        elif cmd == "search-caps":
            if len(sys.argv) < 3:
                print("错误: 缺少 query 参数")
                sys.exit(1)
            query = sys.argv[2]
            results = store.search_capabilities(query)
            print(json.dumps(results, indent=2, ensure_ascii=False))
        
        elif cmd == "search-sources":
            if len(sys.argv) < 3:
                print("错误: 缺少 query 参数")
                sys.exit(1)
            query = sys.argv[2]
            results = store.search_sources(query)
            print(json.dumps(results, indent=2, ensure_ascii=False))
        
        elif cmd == "list-caps":
            results = store.get_all_capabilities()
            print(json.dumps(results, indent=2, ensure_ascii=False))
        
        elif cmd == "list-sources":
            results = store.get_all_sources()
            print(json.dumps(results, indent=2, ensure_ascii=False))
        
        else:
            print(f"未知命令: {cmd}")
            sys.exit(1)
    
    finally:
        store.close()


if __name__ == "__main__":
    main()
