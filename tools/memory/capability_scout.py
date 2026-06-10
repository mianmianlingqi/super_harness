#!/usr/bin/env python3
"""
Super Harness — Capability Scout (实时 MCP/Skill 商店侦察)

取代静态 capabilities 数据库查询。每次调用都实时搜索真实商店：
  - npm registry: @anthropic-ai/*, mcp-server-*, @anthropic/*, modelcontextprotocol/*
  - PyPI registry: mcp-server-*, claude-mcp-*
  - Web fallback: 通用搜索 + 已知优质 MCP 列表

返回结果直接可用于 proxy_mcp（热加载本轮即用）或 perm_mcp_install（永久安装）。

原理：npm search / PyPI search 都是公开 API，无需认证。
Web fallback 可以补充官方列表和社区推荐。
"""

import json
import sys
import os
import urllib.request
import urllib.parse
import urllib.error
import re
from pathlib import Path
from typing import Optional

# ── npm registry search ───────────────────────────────────

def _npm_search(query: str, limit: int = 10) -> list:
    """搜索 npm registry，找 MCP server / Claude Code 插件包

    npm search API: https://registry.npmjs.org/-/v1/search?text=...&size=...
    返回包名、描述、版本、npm 链接。
    """
    url = f"https://registry.npmjs.org/-/v1/search?text={urllib.parse.quote(query)}&size={limit}"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return []

    results = []
    for obj in data.get("objects", []):
        pkg = obj.get("package", {})
        name = pkg.get("name", "")
        desc = pkg.get("description", "") or ""
        version = pkg.get("version", "")
        npm_url = pkg.get("links", {}).get("npm", f"https://www.npmjs.com/package/{name}")
        keywords = pkg.get("keywords", []) or []

        # 后过滤：必须包含 mcp, model-context-protocol, 或 claude 相关标记
        name_lower = name.lower()
        desc_lower = desc.lower()
        kw_lower = " ".join(keywords).lower()
        combined = f"{name_lower} {desc_lower} {kw_lower}"

        is_mcp = (
            "mcp" in name_lower or
            "mcp" in kw_lower or
            "model-context-protocol" in combined or
            "mcp-server" in combined or
            "mcp server" in desc_lower or
            "mcp client" in desc_lower or
            "mcp tool" in desc_lower
        )
        if not is_mcp:
            continue

        results.append({
            "name": name,
            "type": "mcp",
            "source": "npm",
            "description": desc[:300],
            "version": version,
            "url": npm_url,
            "keywords": keywords[:10],
            "install": {
                "proxy": f"npx -y {name}",
                "perm": {
                    "command": "npx",
                    "args": ["-y", name],
                    "description": desc[:200],
                }
            }
        })

    return results


# ── PyPI registry search ──────────────────────────────────

def _pypi_search(query: str, limit: int = 10) -> list:
    """搜索 PyPI，找 MCP server / Claude 相关 Python 包

    PyPI search API: https://pypi.org/search/?q=...
    返回 JSON 格式。
    """
    url = f"https://pypi.org/search/?q={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return []

    results = []
    for item in data.get("results", [])[:limit]:
        name = item.get("name", "")
        desc = item.get("description", "") or item.get("summary", "") or ""
        version = item.get("version", "")
        pypi_url = f"https://pypi.org/project/{name}/"

        results.append({
            "name": name,
            "type": "mcp",
            "source": "pypi",
            "description": desc[:300],
            "version": version,
            "url": pypi_url,
            "keywords": [],
            "install": {
                "proxy": f"uvx {name}" if "mcp-server" in name else f"python -m {name}",
                "perm": {
                    "command": "uvx" if "mcp-server" in name else "python",
                    "args": [name] if "mcp-server" in name else ["-m", name],
                    "description": desc[:200],
                }
            }
        })

    return results


# ── Web fallback (DuckDuckGo-based) ───────────────────────

def _web_mcp_search(query: str, limit: int = 5) -> list:
    """用 Web 搜索补充 MCP 发现（已知源 + 搜索结果）"""
    from web_search import web_search

    # 搜索 "mcp server <query>"
    full_query = f"mcp server {query} site:github.com OR site:npmjs.com OR site:pypi.org"
    result = web_search(full_query, backend="auto", limit=limit)
    if result.get("error"):
        return []

    results = []
    for r in result.get("results", []):
        results.append({
            "name": r.get("title", "")[:80],
            "type": "mcp",
            "source": "web",
            "description": r.get("snippet", "")[:300],
            "url": r.get("url", ""),
            "keywords": [],
            "install": {
                "note": "Web 搜索结果，需手动确认安装方式"
            }
        })

    return results


# ── 统一入口 ──────────────────────────────────────────────

def scout(query: str, kind: str = None, limit: int = 10,
           sources: list = None) -> dict:
    """
    实时搜索 MCP/Skill 商店

    Args:
        query: 自然语言搜索查询，如 "browser automation"、"PDF processing"、"git tools"
        kind: 可选过滤 — "mcp" 或 "skill"，不传返回全部
        limit: 每个源返回数量上限
        sources: 要搜索的源列表，默认全部 ["npm", "pypi", "web"]
                 传 ["npm"] 只搜 npm，避免慢

    Returns:
        {
            "query": str,
            "sources_searched": [...],
            "total": int,
            "results": [
                {
                    "name": str,
                    "type": "mcp"|"skill",
                    "source": "npm"|"pypi"|"web",
                    "description": str,
                    "version": str,
                    "url": str,
                    "keywords": [...],
                    "install": {
                        "proxy": "npx -y @playwright/mcp",   # 一行命令，给 proxy_mcp 用
                        "perm": { ... }                      # 给 perm_mcp_install 用
                    },
                    "rank": float
                }
            ],
            "hot_load": {
                "description": "如何立即使用这些结果",
                "example": 'proxy_mcp(server_command="npx -y @xxx/mcp", tool_name="...")'
            }
        }
    """
    if sources is None:
        sources = ["npm", "pypi", "web"]

    all_results = []
    searched = []

    # npm 搜索（MCP 相关关键词）
    if "npm" in sources and (not kind or kind == "mcp"):
        searched.append("npm")
        # 多关键词搜索提高覆盖率
        npm_queries = [
            f"mcp server {query}",
            f"claude mcp {query}",
        ]
        seen = set()
        for nq in npm_queries[:2]:  # 最多 2 轮，避免太慢
            for r in _npm_search(nq, limit=max(3, limit // 2)):
                if r["name"] not in seen:
                    seen.add(r["name"])
                    all_results.append(r)

    # PyPI 搜索
    if "pypi" in sources and (not kind or kind == "mcp"):
        searched.append("pypi")
        seen = {r["name"] for r in all_results}
        for r in _pypi_search(f"mcp server {query}", limit=max(3, limit // 2)):
            if r["name"] not in seen:
                seen.add(r["name"])
                all_results.append(r)

    # Web fallback
    if "web" in sources and (not kind or kind == "mcp"):
        searched.append("web")
        seen = {r["name"] for r in all_results}
        for r in _web_mcp_search(query, limit=max(3, limit // 3)):
            name = r["name"]
            if name not in seen:
                seen.add(name)
                all_results.append(r)

    # 简单 rank：npm > pypi > web
    source_rank = {"npm": 1.0, "pypi": 0.9, "web": 0.6}
    for r in all_results:
        r["rank"] = source_rank.get(r.get("source", "web"), 0.5)

    all_results.sort(key=lambda r: r.get("rank", 0), reverse=True)

    total = len(all_results)
    if limit and total > limit:
        all_results = all_results[:limit]

    return {
        "query": query,
        "sources_searched": searched,
        "total": total,
        "results": all_results,
        "hot_load": {
            "description": "找到需要的 MCP 后，两种方式热加载：",
            "immediate": '用 proxy_mcp(server_command="<install.proxy>", tool_name="<工具名>") 本轮立即可用',
            "permanent": "用 perm_mcp_install(name=..., command=..., args=..., description=...) 永久安装到项目",
            "note": "proxy_mcp 启动 MCP 子进程 → JSON-RPC 握手 → 直接调用工具，无需重启 Claude Code",
        }
    }


# ── 命令行 ────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python capability_scout.py <query> [--kind mcp|skill] [--limit N] [--sources npm,pypi,web]")
        print()
        print("示例:")
        print("  python capability_scout.py 'browser automation'")
        print("  python capability_scout.py 'PDF processing' --sources npm")
        print("  python capability_scout.py 'git tools' --kind mcp --limit 5")
        sys.exit(1)

    query = sys.argv[1]

    kind = None
    limit = 10
    sources = None

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--kind" and i + 1 < len(args):
            kind = args[i + 1]
            i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
        elif args[i] == "--sources" and i + 1 < len(args):
            sources = args[i + 1].split(",")
            i += 2
        else:
            i += 1

    result = scout(query, kind=kind, limit=limit, sources=sources)
    print(json.dumps(result, ensure_ascii=False, indent=2))
