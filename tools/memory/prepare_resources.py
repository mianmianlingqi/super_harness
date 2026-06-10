#!/usr/bin/env python3
"""
Super Harness — 任务前资源库准备

用法: python prepare_resources.py <task_description>
      python prepare_resources.py --from-urls url1,url2,url3
      python prepare_resources.py --from-repos owner/repo1,owner/repo2

自动完成:
  1. 搜索 Web + 研究源 + 能力库
  2. 下载参考文档 (html2text)
  3. 克隆参考项目 (git clone --depth=1)
  4. 索引到临时向量库
  5. 输出准备报告
"""

import json
import sys
import subprocess
import hashlib
import tempfile
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

RESOURCES_DIR = Path("resources")
REFS_DIR = RESOURCES_DIR / "reference"
DOCS_DIR = RESOURCES_DIR / "docs"
TASK_FILE = RESOURCES_DIR / "PREPARE_REPORT.md"


def ensure_dirs():
    RESOURCES_DIR.mkdir(exist_ok=True)
    REFS_DIR.mkdir(exist_ok=True)
    DOCS_DIR.mkdir(exist_ok=True)


def download_doc(url: str) -> Path | None:
    """下载网页并转换为 Markdown"""
    import urllib.request
    name = hashlib.md5(url.encode()).hexdigest()[:12] + ".md"
    out = DOCS_DIR / name
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SuperHarness/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"     ⚠️ 下载失败: {url[:60]} — {e}")
        return None

    # 简单提取文本（去除 HTML 标签）
    import re
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 截断过长内容
    if len(text) > 50000:
        text = text[:50000] + "\n\n... (truncated)"

    out.write_text(f"# Source: {url}\n\n{text}", encoding='utf-8')
    return out


def clone_repo(repo: str) -> Path | None:
    """浅克隆 GitHub 仓库"""
    target = REFS_DIR / repo.split('/')[-1]
    if target.exists():
        print(f"     📎 {repo} 已存在，跳过")
        return target
    try:
        url = f"https://github.com/{repo}.git"
        subprocess.run(["git", "clone", "--depth=1", url, str(target)],
                       capture_output=True, timeout=120, check=True)
        print(f"     ✅ 克隆: {repo} → {target}")
        return target
    except Exception as e:
        print(f"     ⚠️ 克隆失败: {repo} — {e}")
        return None


def search_web(query: str, limit: int = 5) -> list:
    """Web 搜索"""
    from web_search import web_search
    return web_search(query, limit=limit)["results"]


def search_capabilities(query: str, limit: int = 5) -> list:
    """能力检索"""
    from harness_db import VectorStore
    db = VectorStore()
    results = db.search_capabilities(query, limit=limit)
    db.conn.close()
    return results


def search_sources(query: str, limit: int = 5) -> list:
    """研究源检索"""
    from harness_db import VectorStore
    db = VectorStore()
    results = db.search_sources(query, limit=limit)
    db.conn.close()
    return results


def index_to_temp_db(task_id: str):
    """将下载的资源索引到临时向量库"""
    try:
        from semantic_search import SemanticSearch
        sem = SemanticSearch()

        docs = list(DOCS_DIR.glob("*.md"))
        for doc in docs:
            content = doc.read_text(encoding='utf-8')[:5000]
            sem.add_capability_with_embedding(
                name=f"resource:{doc.stem}",
                type="skill",
                description=f"临时参考文档: {doc.name} — {content[:200]}",
                file_path=str(doc),
                category="临时资源",
                tags=[task_id, "temp", "resource"],
                version="1.0"
            )

        # 索引克隆项目的 README
        for proj in REFS_DIR.iterdir():
            if proj.is_dir():
                readme = proj / "README.md"
                if readme.exists():
                    content = readme.read_text(encoding='utf-8')[:5000]
                    sem.add_capability_with_embedding(
                        name=f"ref:{proj.name}",
                        type="skill",
                        description=f"参考项目: {proj.name} — {content[:200]}",
                        file_path=str(readme),
                        category="临时资源",
                        tags=[task_id, "temp", "reference"],
                        version="1.0"
                    )

        sem.close()
        return len(docs) + len(list(REFS_DIR.iterdir()))
    except Exception as e:
        print(f"     ⚠️ 索引失败: {e}")
        return 0


def generate_report(task: str, web_results: list, caps: list, sources: list,
                    docs: list, repos: list) -> str:
    """生成准备报告"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"# 资源库准备报告",
        f"",
        f"**任务**: {task}  ",
        f"**时间**: {now}  ",
        f"",
        f"## 📊 搜集统计",
        f"",
        f"| 来源 | 数量 |",
        f"|------|------|",
        f"| Web 搜索结果 | {len(web_results)} |",
        f"| 匹配的能力 | {len(caps)} |",
        f"| 推荐的研究源 | {len(sources)} |",
        f"| 下载的文档 | {len(docs)} |",
        f"| 克隆的参考项目 | {len(repos)} |",
        f"",
    ]

    if web_results:
        lines.append("## 🌐 Web 搜索结果")
        for r in web_results[:5]:
            lines.append(f"- [{r.get('title','')}]({r.get('url','')})")
            lines.append(f"  {r.get('snippet','')[:150]}")
        lines.append("")

    if caps:
        lines.append("## 🔧 可用的 Skill/MCP")
        for c in caps[:5]:
            lines.append(f"- **{c.get('name','')}** ({c.get('type','')}): {c.get('description','')[:120]}")
        lines.append("")

    if sources:
        lines.append("## 📚 推荐的研究源")
        for s in sources[:5]:
            lines.append(f"- **{s.get('name','')}** ({s.get('type','')}): {s.get('description','')[:120]}")
        lines.append("")

    if docs:
        lines.append("## 📄 下载的参考文档")
        for d in docs:
            lines.append(f"- `{d}`")
        lines.append("")

    if repos:
        lines.append("## 🗂️ 克隆的参考项目")
        for r in repos:
            lines.append(f"- `{r}`")
        lines.append("")

    lines.append("---")
    lines.append(f"*资源目录: `{RESOURCES_DIR.absolute()}`*")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("用法: python prepare_resources.py <task_description>")
        print("      python prepare_resources.py --from-urls url1,url2")
        print("      python prepare_resources.py --from-repos owner/repo1,owner/repo2")
        sys.exit(1)

    ensure_dirs()
    web_results = []
    docs_downloaded = []
    repos_cloned = []

    if sys.argv[1] == "--from-urls":
        urls = sys.argv[2].split(",")
        for url in urls:
            doc = download_doc(url.strip())
            if doc:
                docs_downloaded.append(str(doc))
    elif sys.argv[1] == "--from-repos":
        repos = sys.argv[2].split(",")
        for repo in repos:
            target = clone_repo(repo.strip())
            if target:
                repos_cloned.append(str(target))
    else:
        task = " ".join(sys.argv[1:])
        task_id = hashlib.md5(task.encode()).hexdigest()[:8]
        print(f"🔍 任务: {task}")
        print(f"   ID: {task_id}")
        print()

        # Phase 1: 搜索
        print("🌐 Phase 1: 信息搜集...")
        web_results = search_web(task, limit=5)
        caps = search_capabilities(task, limit=5)
        sources = search_sources(task, limit=5)
        print(f"   Web: {len(web_results)} 条 | 能力: {len(caps)} 个 | 源: {len(sources)} 个")

        # Phase 2: 下载文档
        print("📥 Phase 2: 下载参考文档...")
        for r in web_results:
            url = r.get("url", "")
            if url and ("github.com" not in url or "/blob/" in url):
                doc = download_doc(url)
                if doc:
                    docs_downloaded.append(str(doc))

        # Phase 3: 克隆相关项目
        print("🗂️ Phase 3: 发现参考项目...")
        for r in web_results:
            url = r.get("url", "")
            if "github.com" in url and "/blob/" not in url:
                # 提取 owner/repo
                import re
                m = re.search(r'github\.com/([^/]+/[^/]+)', url)
                if m:
                    repo = m.group(1).rstrip('/')
                    if '/' in repo and not repo.endswith('.git'):
                        target = clone_repo(repo)
                        if target:
                            repos_cloned.append(str(target))

        # Phase 4: 索引
        print("🔢 Phase 4: 索引到向量库...")
        indexed = index_to_temp_db(task_id)
        print(f"   已索引: {indexed} 个资源")

        # Phase 5: 生成报告
        print("📝 Phase 5: 生成报告...")
        report = generate_report(task, web_results, caps, sources,
                                 docs_downloaded, repos_cloned)
        TASK_FILE.write_text(report, encoding='utf-8')
        print(f"   报告: {TASK_FILE}")

    print()
    print("✅ 资源库准备完成")
    print(f"   文档: {len(docs_downloaded)} 个")
    print(f"   项目: {len(repos_cloned)} 个")
    print(f"   全部在: {RESOURCES_DIR.absolute()}")


if __name__ == "__main__":
    main()
