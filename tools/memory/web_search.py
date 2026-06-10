#!/usr/bin/env python3
"""
Super Harness — 统一 Web 搜索模块

提供多后端 Web 搜索，统一接口。按优先级自动选择可用后端。

支持的后端：
  1. DuckDuckGo  — 免费，无需 API Key，即时可用（via duckduckgo_search 库）
  2. Tavily       — AI 优化，需 TAVILY_API_KEY（免费额度 1000/月）
  3. Brave        — 需 BRAVE_API_KEY（免费额度 2000/月）
  4. SearXNG      — 自托管，需 SEARXNG_BASE_URL

用法：
  from web_search import web_search
  results = web_search("Python vector database", backend="auto", limit=10)
"""

import os
import json
from typing import List, Dict, Optional, Literal

Backend = Literal["auto", "duckduckgo", "tavily", "brave", "searxng"]


# ── 结果格式 ──────────────────────────────────────────────

def _make_result(title: str, url: str, snippet: str, **extra) -> Dict:
    """标准化搜索结果"""
    r = {"title": title, "url": url, "snippet": snippet}
    r.update(extra)
    return r


# ── DuckDuckGo ────────────────────────────────────────────

def _get_ddgs():
    """尝试导入 DDGS（支持新旧包名）"""
    try:
        from ddgs import DDGS  # 新包名
        return DDGS
    except ImportError:
        pass
    try:
        from duckduckgo_search import DDGS  # 旧包名
        return DDGS
    except ImportError:
        pass
    raise ImportError(
        "DDGS 未安装。运行: pip install ddgs"
    )


def _search_duckduckgo(query: str, limit: int = 10) -> List[Dict]:
    """通过 DuckDuckGo 搜索（免费，无需 API Key）"""
    DDGS = _get_ddgs()
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=limit))
        return [
            _make_result(
                title=r["title"],
                url=r["href"],
                snippet=r.get("body", ""),
            )
            for r in results
        ]


# ── Tavily ────────────────────────────────────────────────

def _search_tavily(query: str, limit: int = 10) -> List[Dict]:
    """通过 Tavily API 搜索（AI 优化搜索）"""
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        raise ValueError("TAVILY_API_KEY 未设置")

    try:
        from tavily import TavilyClient
    except ImportError:
        raise ImportError("tavily-python 未安装。运行: pip install tavily-python")

    client = TavilyClient(api_key=api_key)
    response = client.search(query=query, max_results=limit)

    return [
        _make_result(
            title=r.get("title", ""),
            url=r.get("url", ""),
            snippet=r.get("content", ""),
            score=r.get("score"),
        )
        for r in response.get("results", [])
    ]


# ── Brave ─────────────────────────────────────────────────

def _search_brave(query: str, limit: int = 10) -> List[Dict]:
    """通过 Brave Search API 搜索"""
    api_key = os.environ.get("BRAVE_API_KEY", "")
    if not api_key:
        raise ValueError("BRAVE_API_KEY 未设置")

    import urllib.request
    import urllib.parse

    url = "https://api.search.brave.com/res/v1/web/search"
    params = {"q": query, "count": min(limit, 20)}
    req = urllib.request.Request(
        f"{url}?{urllib.parse.urlencode(params)}",
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        },
    )

    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())

    return [
        _make_result(
            title=r.get("title", ""),
            url=r.get("url", ""),
            snippet=r.get("description", ""),
        )
        for r in data.get("web", {}).get("results", [])
    ]


# ── SearXNG ───────────────────────────────────────────────

def _search_searxng(query: str, limit: int = 10) -> List[Dict]:
    """通过自托管 SearXNG 实例搜索"""
    base_url = os.environ.get("SEARXNG_BASE_URL", "")
    if not base_url:
        raise ValueError("SEARXNG_BASE_URL 未设置")

    import urllib.request
    import urllib.parse

    url = f"{base_url.rstrip('/')}/search"
    params = {"q": query, "format": "json", "categories": "general"}
    req = urllib.request.Request(
        f"{url}?{urllib.parse.urlencode(params)}"
    )

    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    return [
        _make_result(
            title=r.get("title", ""),
            url=r.get("url", ""),
            snippet=r.get("content", ""),
            engine=r.get("engine", ""),
        )
        for r in data.get("results", [])[:limit]
    ]


# ── 后端优先级 ────────────────────────────────────────────

def _check_available(backend: str) -> bool:
    """检查指定后端是否可用"""
    if backend == "duckduckgo":
        try:
            _get_ddgs()
            return True
        except ImportError:
            return False
    elif backend == "tavily":
        return bool(os.environ.get("TAVILY_API_KEY"))
    elif backend == "brave":
        return bool(os.environ.get("BRAVE_API_KEY"))
    elif backend == "searxng":
        return bool(os.environ.get("SEARXNG_BASE_URL"))
    return False


BACKEND_PRIORITY: List[Backend] = ["duckduckgo", "tavily", "brave", "searxng"]


# ── 统一入口 ──────────────────────────────────────────────

def web_search(
    query: str,
    backend: Backend = "auto",
    limit: int = 10,
) -> Dict:
    """
    统一 Web 搜索接口

    Args:
        query: 搜索查询
        backend: 后端选择
            - "auto": 按可用性自动选择（DuckDuckGo → Tavily → Brave → SearXNG）
            - "duckduckgo": 仅 DuckDuckGo
            - "tavily": 仅 Tavily
            - "brave": 仅 Brave
            - "searxng": 仅 SearXNG
        limit: 返回结果数（默认 10）

    Returns:
        {
            "query": str,
            "backend": str,
            "results": [{"title": str, "url": str, "snippet": str, ...}, ...],
            "error": str | None
        }
    """

    SEARCHERS = {
        "duckduckgo": _search_duckduckgo,
        "tavily": _search_tavily,
        "brave": _search_brave,
        "searxng": _search_searxng,
    }

    if backend == "auto":
        for b in BACKEND_PRIORITY:
            if _check_available(b):
                backend = b
                break
        else:
            return {
                "query": query,
                "backend": "none",
                "results": [],
                "error": "无可用搜索后端。请安装 duckduckgo_search 或设置 API Key。\n"
                         "  pip install duckduckgo_search\n"
                         "  或设置: TAVILY_API_KEY / BRAVE_API_KEY / SEARXNG_BASE_URL",
            }

    try:
        results = SEARCHERS[backend](query, limit=limit)
        return {
            "query": query,
            "backend": backend,
            "results": results,
            "error": None,
        }
    except Exception as e:
        return {
            "query": query,
            "backend": backend,
            "results": [],
            "error": str(e),
        }


# ── 命令行测试 ────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "Python vector database"
    result = web_search(query)
    print(json.dumps(result, ensure_ascii=False, indent=2))
