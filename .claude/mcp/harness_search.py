#!/usr/bin/env python3
"""
Super Harness MCP Server — 语义搜索能力

Zero-dependency MCP server (JSON-RPC 2.0 over stdin/stdout).
将 tools/memory/ 的检索能力暴露为 Claude Code 可调用的 MCP 工具。

Exposed tools:
  - search_memory    : 语义搜索项目记忆（BM25 全文搜索）
  - search_capability: 语义搜索能力注册表（向量+BM25 混合检索）
  - search_source    : 语义搜索研究源（BM25 全文搜索）

Usage:
  在 settings.json 的 mcpServers 中注册:
  "super-harness": {
    "command": "python",
    "args": [".claude/mcp/harness_search.py"],
    "env": { "PYTHONPATH": "tools/memory" }
  }
"""

import sys
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


# ── 路径设置 ────────────────────────────────────────────

# 确保 tools/memory 在 Python 路径中
_TOOLS_MEMORY = Path(__file__).resolve().parent.parent.parent / "tools" / "memory"
if str(_TOOLS_MEMORY) not in sys.path:
    sys.path.insert(0, str(_TOOLS_MEMORY))


# ── 数据库初始化 ────────────────────────────────────────

_db = None       # VectorStore instance
_semantic = None  # SemanticSearch instance (optional, requires sentence-transformers)


def _get_db():
    """延迟初始化 VectorStore"""
    global _db
    if _db is None:
        from harness_db import VectorStore
        _db = VectorStore()
    return _db


def _get_semantic():
    """延迟初始化 SemanticSearch（可选向量支持）"""
    global _semantic
    if _semantic is None:
        try:
            from semantic_search import SemanticSearch
            _semantic = SemanticSearch()
        except Exception:
            pass  # 向量检索不可用，降级到纯 BM25
    return _semantic


# ── Tool 实现 ──────────────────────────────────────────

def search_memory(query: str, project_id: Optional[str] = None,
                  limit: int = 10) -> list:
    """语义搜索项目记忆（BM25 全文搜索）

    Args:
        query: 搜索查询文本
        project_id: 可选，按项目 ID 过滤
        limit: 返回结果数量（默认 10）

    Returns:
        匹配的记忆列表，每项含 id, content, source_file, rank 等字段
    """
    db = _get_db()
    results = db.search_memories(query, project_id=project_id, limit=limit)
    return results


def search_capability(query: str, type: Optional[str] = None,
                      limit: int = 10, vector_weight: float = 0.7,
                      sources: Optional[list] = None) -> dict:
    """实时搜索 MCP/Skill 商店（npm + PyPI + Web + Skill 注册表）

    不再查静态数据库，而是直接搜索真实注册表。
    找到的 MCP 可直接用 proxy_mcp 热加载本轮即用，或 perm_mcp_install 永久安装。
    找到的 Skill 可用 perm_skill_install 永久安装。

    Args:
        query: 自然语言搜索查询，描述你需要什么能力
        type: 可选过滤 "skill" 或 "mcp"，不传则返回全部
        limit: 返回结果数量（默认 10）
        vector_weight: 保留参数（兼容旧接口，scout 不使用）
        sources: 搜索源列表，默认 ["npm", "pypi", "web"]

    Returns:
        {
            "query": str,
            "sources_searched": [...],
            "total": int,
            "results": [{name, type, source, description, version, url, install, rank}, ...],
            "hot_load": {description, immediate, permanent, note}
        }
    """
    from capability_scout import scout
    from skill_scout import scout_skills

    kind = type  # old param name maps to scout's "kind"

    # MCP + Skill 都要
    mcp_results = {"results": [], "sources_searched": [], "total": 0}
    skill_results = {"results": [], "sources_searched": [], "total": 0}

    if not kind or kind == "mcp":
        mcp_results = scout(query, kind="mcp", limit=limit, sources=sources)

    if not kind or kind == "skill":
        skill_results = scout_skills(query, limit=limit)

    combined = mcp_results["results"] + skill_results["results"]
    # 按 rank 排序
    combined.sort(key=lambda r: r.get("rank", 0), reverse=True)

    total = len(combined)
    if limit and total > limit:
        combined = combined[:limit]

    return {
        "query": query,
        "sources_searched": mcp_results.get("sources_searched", []) + skill_results.get("sources_searched", []),
        "total": total,
        "results": combined,
        "hot_load": {
            "description": "找到需要的 MCP/Skill 后，两种方式热加载：",
            "mcp_immediate": '用 proxy_mcp(server_command="<install.proxy>", tool_name="<工具名>") 本轮立即可用',
            "mcp_permanent": "用 perm_mcp_install(name=..., command=..., args=..., description=...) 永久安装到项目",
            "skill_permanent": "用 perm_skill_install(name=..., description=..., content=...) 永久安装 Skill 到项目",
            "note": "proxy_mcp 启动 MCP 子进程 → JSON-RPC 握手 → 直接调用工具，无需重启 Claude Code",
        }
    }


def search_source(query: str, limit: int = 10) -> list:
    """语义搜索研究源

    在已注册的研究源中按相关性搜索。

    Args:
        query: 搜索查询文本
        limit: 返回结果数量（默认 10）

    Returns:
        匹配的研究源列表，每项含 name, type, description, rank 等字段
    """
    db = _get_db()
    results = db.search_sources(query, limit=limit)
    return results


def search_web(query: str, limit: int = 10, backend: str = "auto") -> dict:
    """Web 搜索（多后端：DuckDuckGo / Tavily / Brave / SearXNG）

    通过第三方搜索引擎进行实时 Web 搜索。默认自动选择可用后端。

    Args:
        query: 搜索查询文本
        limit: 返回结果数量（默认 10）
        backend: 搜索后端 — "auto"（自动选择）, "duckduckgo", "tavily", "brave", "searxng"

    Returns:
        {
            "query": str,
            "backend": str,
            "results": [{"title": str, "url": str, "snippet": str}, ...],
            "error": str | None
        }
    """
    from web_search import web_search
    return web_search(query=query, backend=backend, limit=limit)


# ── Lens queries ──────────────────────────────────────────

LENS_QUERIES = {
    "restore-context": None,       # special: return recent sessions directly
    "run-retro": None,             # special: return more sessions
    "find-gotchas": "confused struggling stuck problem help broken",
    "extract-decisions": "decided chose decision trade-off because",
    "find-antipatterns": "again same mistake repeated forgot",
    "review-process": "workflow process approach method",
    "extract-learnings": "learned discovered realized insight",
}


def search_sessions(query: str = "", lens: str = "restore-context",
                    project: str = "", limit: int = 10,
                    mode: str = "fts") -> list:
    """搜索历史会话（全文检索 + 透镜）

    Args:
        query: 搜索关键词（空字符串 = 返回最近会话）
        lens: 检索透镜 — restore-context/run-retro/find-gotchas/
              extract-decisions/find-antipatterns/review-process/extract-learnings
        project: 按项目名过滤（空 = 不过滤）
        limit: 返回数量

    Returns:
        匹配的会话列表，含 uuid, context_summary, exchange_count, ended_at
    """
    from session_memory.db import get_db_connection

    conn = get_db_connection()
    results = []

    try:
        # 透镜特殊处理
        if lens in ("restore-context",):
            limit = min(limit, 5)
        elif lens in ("run-retro",):
            limit = min(limit, 20)

        # 构建查询
        if lens in ("restore-context", "run-retro"):
            # 直接返回最近会话
            rows = conn.execute("""
                SELECT s.uuid, b.context_summary, b.exchange_count, b.ended_at,
                       b.files_modified, b.commits
                FROM branches b
                JOIN sessions s ON b.session_id = s.id
                WHERE b.is_active = 1
                  AND b.context_summary IS NOT NULL
                ORDER BY b.ended_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
        elif mode in ("vector", "hybrid") and query:
            # 向量语义搜索（复用已加载的 _semantic 实例）
            sem = _get_semantic()
            if sem is None:
                # 降级到 FTS
                from semantic_search import SemanticSearch
                sem = SemanticSearch()
            q_embed = sem._embed(query)
            rows = conn.execute("""
                SELECT s.uuid, b.context_summary, b.exchange_count, b.ended_at,
                       b.files_modified, b.commits,
                       MIN(vec_distance_cosine(v.embedding, ?)) as min_dist
                FROM session_messages_vec v
                JOIN session_messages m ON v.id = m.id
                JOIN branch_messages bm ON bm.message_id = m.id
                JOIN branches b ON bm.branch_id = b.id
                JOIN sessions s ON b.session_id = s.id
                WHERE b.is_active = 1
                GROUP BY s.uuid
                ORDER BY min_dist ASC
                LIMIT ?
            """, (q_embed.tobytes(), limit)).fetchall()
            sem.close()
        elif query or lens:
            # FTS5 全文搜索 + 透镜关键词
            search_q = query if query else LENS_QUERIES.get(lens, query)
            if not search_q:
                search_q = query
            try:
                rows = conn.execute("""
                    SELECT s.uuid, b.context_summary, b.exchange_count, b.ended_at,
                           b.files_modified, b.commits
                    FROM session_messages_fts fts
                    JOIN session_messages m ON fts.rowid = m.id
                    JOIN branch_messages bm ON bm.message_id = m.id
                    JOIN branches b ON bm.branch_id = b.id
                    JOIN sessions s ON b.session_id = s.id
                    WHERE session_messages_fts MATCH ?
                      AND b.is_active = 1
                    GROUP BY s.uuid
                    ORDER BY b.ended_at DESC
                    LIMIT ?
                """, (search_q, limit)).fetchall()
            except Exception:
                # FTS 失败降级到 LIKE
                like_q = f"%{search_q}%"
                rows = conn.execute("""
                    SELECT s.uuid, b.context_summary, b.exchange_count, b.ended_at,
                           b.files_modified, b.commits
                    FROM session_messages m
                    JOIN branch_messages bm ON bm.message_id = m.id
                    JOIN branches b ON bm.branch_id = b.id
                    JOIN sessions s ON b.session_id = s.id
                    WHERE m.content LIKE ?
                      AND b.is_active = 1
                    GROUP BY s.uuid
                    ORDER BY b.ended_at DESC
                    LIMIT ?
                """, (like_q, limit)).fetchall()
        else:
            rows = []

        for row in rows:
            results.append({
                "uuid": row[0],
                "context_summary": row[1] or "",
                "exchange_count": row[2] or 0,
                "ended_at": row[3] or "",
                "files_modified": row[4] or "",
                "commits": row[5] or "",
            })

    finally:
        conn.close()

    return results


# ── Tool 注册表 ─────────────────────────────────────────

def proxy_mcp(server_command: str, tool_name: str,
              tool_args: dict = None) -> dict:
    from mcp_proxy import proxy_mcp_call
    return proxy_mcp_call(server_command, tool_name, tool_args or {})


def temp_mcp_install(name: str, command: str) -> dict:
    from mcp_proxy import temp_install_mcp
    return temp_install_mcp(name, command)


def perm_mcp_install(name: str, command: str, args: list = None,
                     description: str = "", project_root: str = "") -> dict:
    """永久安装 MCP 到项目资源库 (.super-harness/resources/mcp/)"""
    from mcp_proxy import perm_install_mcp as _perm
    root = project_root if project_root else None
    return _perm(name, command, args, description, root)


def perm_skill_install(name: str, description: str, content: str,
                       project_root: str = "") -> dict:
    """永久安装 Skill 到项目资源库 (.super-harness/resources/skills/)"""
    from mcp_proxy import perm_install_skill as _perm_skill
    root = project_root if project_root else None
    return _perm_skill(name, description, content, root)


def list_project_tools(project_root: str = "") -> dict:
    """列出项目资源库中已安装的 MCP 和 Skill"""
    from mcp_proxy import list_project_mcps, list_project_skills
    root = project_root if project_root else None
    return {
        "mcps": list_project_mcps(root),
        "skills": list_project_skills(root),
    }


TOOLS = {
    "search_memory": {
        "fn": search_memory,
        "schema": {
            "name": "search_memory",
            "description": "语义搜索项目记忆库。在 MEMORY.md 和 memory/*.md 中搜索相关经验、坑点、架构决策。当你需要回忆之前学到的经验、查找历史决策、或了解项目约定时使用。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "自然语言搜索查询，描述你想查找的内容"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "可选，按项目 ID 过滤记忆"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量（默认 10）",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        }
    },
    "search_capability": {
        "fn": search_capability,
        "schema": {
            "name": "search_capability",
            "description": "实时搜 MCP/Skill 商店（npm + PyPI + Web）。找到的能力可直接 proxy_mcp 热加载（本轮即用）或 perm_mcp_install 永久安装。当你需要某个工具或技能但不确定是否可用时使用。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "自然语言搜索查询，描述你需要什么能力，如 'browser automation'、'PDF processing'"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["skill", "mcp"],
                        "description": "可选过滤：只搜索 Skill 或只搜索 MCP Server"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量（默认 10）",
                        "default": 10
                    },
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "搜索源列表，默认 ['npm', 'pypi', 'web']。只搜 npm 最快: ['npm']"
                    }
                },
                "required": ["query"]
            }
        }
    },
    "search_source": {
        "fn": search_source,
        "schema": {
            "name": "search_source",
            "description": "搜索研究源和 Skill/MCP 商店。内置 10 个源：5 个 MCP 注册中心 + 3 个插件市场 + 1 个 Skill 搜索引擎 + 1 个配方库 + arXiv/PyPI/npm/GitHub 学术源。当你需要调研技术问题或找 Skill 商店时使用。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "自然语言搜索查询，描述你想调研的领域/想找的商店类型"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量（默认 10）",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        }
    },
    "search_web": {
        "fn": search_web,
        "schema": {
            "name": "search_web",
            "description": "实时 Web 搜索。通过第三方搜索引擎查询互联网，获取最新信息。当你需要查找最新技术动态、当前事件、或任何超出训练数据的信息时使用。支持多后端：默认 DuckDuckGo（免费免 API Key），可选 Tavily/Brave/SearXNG。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询文本"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量（默认 10，最大 20）",
                        "default": 10
                    },
                    "backend": {
                        "type": "string",
                        "enum": ["auto", "duckduckgo", "tavily", "brave", "searxng"],
                        "description": "搜索后端（默认 auto 自动选择可用后端）"
                    }
                },
                "required": ["query"]
            }
        }
    },
    "search_sessions": {
        "fn": search_sessions,
        "schema": {
            "name": "search_sessions",
            "description": "搜索历史会话记录（全文检索 + 透镜过滤）。支持 7 种透镜：restore-context（恢复上下文）、run-retro（回顾反思）、find-gotchas（找坑点）、extract-decisions（提取决策）、find-antipatterns（发现反模式）、review-process（审查过程）、extract-learnings（提取经验）。会话数据在 Stop/SessionEnd 时自动同步。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词（留空则返回最近会话）"
                    },
                    "lens": {
                        "type": "string",
                        "enum": ["restore-context", "run-retro", "find-gotchas", "extract-decisions", "find-antipatterns", "review-process", "extract-learnings"],
                        "description": "检索透镜（默认 restore-context）"
                    },
                    "project": {
                        "type": "string",
                        "description": "按项目名过滤（可选）"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量（默认 10）",
                        "default": 10
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["fts", "vector", "hybrid"],
                        "description": "检索模式：fts=全文关键词（默认），vector=语义向量（用自然语言搜），hybrid=向量（暂用vector）"
                    }
                },
                "required": []
            }
        }
    },
    "proxy_mcp": {
        "fn": proxy_mcp,
        "schema": {
            "name": "proxy_mcp",
            "description": "动态代理调用外部 MCP Server — 无需预先安装，本轮对话立即可用。启动 MCP 子进程 → 握手 → 调用工具 → 返回结果。会话结束后自动清理。用于临时试用外部 MCP 工具。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "server_command": {
                        "type": "string",
                        "description": "启动命令，如 'npx -y @playwright/mcp' 或 'uvx mcp-server-fetch'"
                    },
                    "tool_name": {
                        "type": "string",
                        "description": "要调用的工具名，如 'browser_navigate'"
                    },
                    "tool_args": {
                        "type": "object",
                        "description": "工具参数（JSON object）"
                    }
                },
                "required": ["server_command", "tool_name"]
            }
        }
    },
    "temp_mcp_install": {
        "fn": temp_mcp_install,
        "schema": {
            "name": "temp_mcp_install",
            "description": "临时安装 MCP 到配置文件（带 _temp 标记）。重启 Claude Code 后生效，会话结束后 Stop hook 自动清理卸载。适合临时试用外部 MCP。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "MCP 名称（如 'playwright'）"
                    },
                    "command": {
                        "type": "string",
                        "description": "启动命令（如 'npx -y @playwright/mcp'）"
                    }
                },
                "required": ["name", "command"]
            }
        }
    },
    "perm_mcp_install": {
        "fn": perm_mcp_install,
        "schema": {
            "name": "perm_mcp_install",
            "description": "永久安装 MCP 到项目资源库 (.super-harness/resources/mcp/)。跨会话保留，可 Git 版本控制，团队共享。SessionStart hook 自动检测并提示激活。适合项目长期依赖的 MCP。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "MCP Server 名称（如 'playwright'）"
                    },
                    "command": {
                        "type": "string",
                        "description": "启动命令（如 'npx' 或 'python'）"
                    },
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "命令参数列表（如 ['-y', '@playwright/mcp']）"
                    },
                    "description": {
                        "type": "string",
                        "description": "用途描述（如 '浏览器自动化测试'）"
                    },
                    "project_root": {
                        "type": "string",
                        "description": "项目根目录路径（默认当前目录）"
                    }
                },
                "required": ["name", "command"]
            }
        }
    },
    "perm_skill_install": {
        "fn": perm_skill_install,
        "schema": {
            "name": "perm_skill_install",
            "description": "永久安装 Skill 到项目资源库 (.super-harness/resources/skills/<name>/SKILL.md)。跨会话保留，可 Git 版本控制，团队共享。SessionStart hook 自动检测并报告。适合项目专用 Skill。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Skill 名称（如 'my-deploy'）"
                    },
                    "description": {
                        "type": "string",
                        "description": "Skill 用途描述"
                    },
                    "content": {
                        "type": "string",
                        "description": "SKILL.md 完整内容（含 frontmatter），不提供则自动生成"
                    },
                    "project_root": {
                        "type": "string",
                        "description": "项目根目录路径（默认当前目录）"
                    }
                },
                "required": ["name", "description"]
            }
        }
    },
    "list_project_tools": {
        "fn": list_project_tools,
        "schema": {
            "name": "list_project_tools",
            "description": "列出项目资源库中已永久安装的 MCP Server 和 Skill。返回名称、描述、安装时间、使用次数等信息。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_root": {
                        "type": "string",
                        "description": "项目根目录路径（默认当前目录）"
                    }
                },
                "required": []
            }
        }
    }
}


# ── JSON-RPC 2.0 实现 ───────────────────────────────────

def _rpc_response(id: Any, result: Any) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": id, "result": result}, ensure_ascii=False)


def _rpc_error(id: Any, code: int, message: str, data: Any = None) -> str:
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return json.dumps({"jsonrpc": "2.0", "id": id, "error": err}, ensure_ascii=False)


def _rpc_notification(method: str, params: Any = None) -> str:
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    return json.dumps(msg, ensure_ascii=False)


def handle_request(msg: Dict[str, Any]) -> Optional[str]:
    """处理单个 JSON-RPC 请求，返回响应 JSON 字符串或 None（通知不回应）"""
    req_id = msg.get("id")
    method = msg.get("method", "")
    params = msg.get("params", {})

    # ── initialize ──
    if method == "initialize":
        return _rpc_response(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "super-harness",
                "version": "0.1.0"
            }
        })

    # ── notifications/initialized ──
    if method == "notifications/initialized":
        return None  # 通知，不回应

    # ── tools/list ──
    if method == "tools/list":
        tools = [t["schema"] for t in TOOLS.values()]
        return _rpc_response(req_id, {"tools": tools})

    # ── tools/call ──
    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if tool_name not in TOOLS:
            return _rpc_error(req_id, -32601,
                            f"Tool not found: {tool_name}",
                            {"available_tools": list(TOOLS.keys())})

        try:
            fn = TOOLS[tool_name]["fn"]
            result = fn(**arguments)

            # 将结果转为可序列化的格式
            if isinstance(result, list):
                # 处理 sqlite3.Row 对象
                clean = []
                for item in result:
                    if hasattr(item, 'keys'):
                        clean.append({k: _sanitize(v) for k, v in dict(item).items()})
                    elif isinstance(item, dict):
                        clean.append({k: _sanitize(v) for k, v in item.items()})
                    else:
                        clean.append(str(item))
                result = clean

            return _rpc_response(req_id, {
                "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
            })
        except Exception as e:
            return _rpc_error(req_id, -32603, f"Tool execution error: {str(e)}")

    # ── 未知方法 ──
    if req_id is not None:
        return _rpc_error(req_id, -32601, f"Method not found: {method}")
    return None


def _sanitize(value: Any) -> Any:
    """将非 JSON 可序列化的值转换"""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8')
        except Exception:
            return value.hex()
    return str(value)


# ── 主循环 ──────────────────────────────────────────────

def main():
    """MCP Server 主循环：读取 stdin 的 JSON-RPC 请求，写入 stdout 响应"""

    # 初始化数据库（提前加载，避免首次调用延迟）
    try:
        _get_db()
        # _get_semantic() 延迟到首次需要向量检索时调用
        # 模型加载 ~28s，启动时加载会超时导致 MCP 连接失败
    except Exception as e:
        # 用 stderr 记录初始化错误（stdout 被 MCP 协议占用）
        print(f"[super-harness] DB init warning: {e}", file=sys.stderr)

    # JSON-RPC 主循环
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except json.JSONDecodeError as e:
            # 无法解析的消息，尝试返回错误
            err = _rpc_error(None, -32700, f"Parse error: {e}")
            print(err, flush=True)
            continue

        response = handle_request(msg)
        if response is not None:
            print(response, flush=True)


if __name__ == "__main__":
    main()
