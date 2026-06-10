#!/usr/bin/env python3
"""
Super Harness — Skill Scout (实时 Skill 商店侦察)

搜 Claude Code 官方/社区 Skill 注册表：
  - Claude Code Skills Registry (claudecode.ai/skills)
  - Awesome Claude Code Skills (GitHub)
  - Web 搜索社区 Skill

返回结果可直接 perm_skill_install 永久安装。
"""

import json
import sys
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional

# 已知的 Skill 商店和仓库
KNOWN_SKILL_SOURCES = [
    {
        "name": "Claude Code Skills Registry",
        "url": "https://claudecode.ai/skills",
        "type": "registry",
        "description": "Claude Code 官方 Skill 注册中心，可浏览、搜索、安装社区 Skill",
    },
    {
        "name": "Awesome Claude Code Skills",
        "url": "https://github.com/anthropics/claude-code",
        "type": "github",
        "description": "Anthropic 官方 Claude Code 仓库，内含示例 skills 和文档",
    },
    {
        "name": "Claude Code Plugins (Official)",
        "url": "https://github.com/anthropics/claude-plugins-official",
        "type": "github",
        "description": "Anthropic 官方 Claude Code 插件/Skill 集合 (30+)",
    },
]


# ── Web 搜索 Skill ────────────────────────────────────────

def _web_skill_search(query: str, limit: int = 10) -> list:
    """用 DuckDuckGo 搜索 Claude Code Skill"""
    from web_search import web_search

    full_query = f"claude code skill {query} site:github.com"
    result = web_search(full_query, backend="auto", limit=limit)
    if result.get("error"):
        return []

    results = []
    for r in result.get("results", []):
        title = r.get("title", "")
        url = r.get("url", "")
        snippet = r.get("snippet", "")

        # 提取 GitHub 仓库名
        import re
        repo_match = re.search(r'github\.com/([^/]+/[^/]+)', url)
        repo_name = repo_match.group(1).rstrip('/') if repo_match else ""

        results.append({
            "name": repo_name or title[:60],
            "type": "skill",
            "source": "web",
            "description": snippet[:300],
            "url": url,
            "install": {
                "note": "Web 搜索到的 Skill，可 clone 到项目后用 perm_skill_install 安装",
                "suggested_command": f"git clone https://github.com/{repo_name}" if repo_name else None,
            },
            "rank": 0.7,
        })

    return results


# ── 统一入口 ──────────────────────────────────────────────

def scout_skills(query: str, limit: int = 10) -> dict:
    """
    搜索 Claude Code Skill

    先返回已知的高质量 Skill 注册表，再用 Web 搜索补充。
    """
    results = []

    # 1. 已知源（始终返回，帮助模型知道去哪找）
    for src in KNOWN_SKILL_SOURCES:
        desc_lower = src["description"].lower() + src["name"].lower()
        if query.lower() in desc_lower or any(w in desc_lower for w in query.lower().split()):
            results.append({
                "name": src["name"],
                "type": "skill",
                "source": "known",
                "description": src["description"],
                "url": src["url"],
                "install": {
                    "note": "访问网站浏览和搜索 Skill，找到后可用 perm_skill_install 安装到项目",
                },
                "rank": 1.0,
            })

    # 始终返回已知源（作为参考）
    for src in KNOWN_SKILL_SOURCES:
        if not any(r["name"] == src["name"] for r in results):
            results.append({
                "name": src["name"],
                "type": "skill",
                "source": "known_reference",
                "description": src["description"],
                "url": src["url"],
                "install": {
                    "note": "Skill 注册表 — 访问网站找到合适的 Skill，用 perm_skill_install 安装",
                },
                "rank": 0.5,
            })

    # 2. Web 搜索补充
    web_results = _web_skill_search(query, limit=max(3, limit // 3))
    seen = {r["name"] for r in results}
    for r in web_results:
        if r["name"] not in seen:
            seen.add(r["name"])
            results.append(r)

    results.sort(key=lambda r: r.get("rank", 0), reverse=True)

    total = len(results)
    if limit and total > limit:
        results = results[:limit]

    return {
        "query": query,
        "sources_searched": ["known_registries", "web"],
        "total": total,
        "results": results,
        "hot_load": {
            "description": "找到需要的 Skill 后：",
            "explore": "访问 Skill 注册表网站浏览可用 Skill",
            "permanent": "用 perm_skill_install(name=..., description=..., content=...) 永久安装到项目",
            "note": "Skill 是 Markdown 文件，存放在 .super-harness/resources/skills/<name>/SKILL.md",
        }
    }


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "code review"
    result = scout_skills(query)
    print(json.dumps(result, ensure_ascii=False, indent=2))
