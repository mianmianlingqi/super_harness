#!/usr/bin/env python3
"""
Super Harness — 会话结束 Hook (Stop)

1. 自动同步当前 transcript → 会话记忆 DB
2. 清理临时 MCP（保留项目永久 MCP）
3. 检查 MEMORY.md 维护状态 + 项目资源库状态

用法:
  "Stop": [{
    "hooks": [{
      "type": "command",
      "command": "python a:/project/super harness/.claude/hooks/session_close.py"
    }]
  }]
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone


# ── 配置 ──────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent.parent
MEMORY_MD = PROJECT_ROOT / "MEMORY.md"
MEMORY_DIR = PROJECT_ROOT / "memory"
SYNC_SCRIPT = PROJECT_ROOT / "tools" / "memory" / "sync_session.py"
TOOLS_MEMORY = PROJECT_ROOT / "tools" / "memory"

SESSION_START = os.environ.get("CLAUDE_SESSION_START")


# ── 会话同步 ──────────────────────────────────────────

def sync_current_session():
    """读取 stdin hook input，提取 transcript_path 并后台同步"""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return None
        hook_input = json.loads(raw)
    except (json.JSONDecError, Exception):
        return None

    transcript_path = hook_input.get("transcript_path", "")
    if not transcript_path or not Path(transcript_path).exists():
        return None

    # 后台子进程同步（不阻塞 Stop）
    try:
        kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        if sys.platform == "win32":
            kwargs["creationflags"] = (
                subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )
        else:
            kwargs["start_new_session"] = True

        env = os.environ.copy()
        env["PYTHONPATH"] = str(TOOLS_MEMORY)

        subprocess.Popen(
            [sys.executable, str(SYNC_SCRIPT), transcript_path],
            env=env,
            **kwargs
        )
        return transcript_path
    except Exception:
        return None


# ── MEMORY.md 检查 ────────────────────────────────────

def get_last_modified(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return 0.0


def check_memory_updated() -> bool:
    mtime = get_last_modified(MEMORY_MD)
    if SESSION_START:
        try:
            return mtime >= float(SESSION_START)
        except (ValueError, TypeError):
            pass
    today = datetime.now(timezone.utc).date()
    mtime_date = datetime.fromtimestamp(mtime, tz=timezone.utc).date()
    return mtime_date == today


def detect_project_resources(project_root: Path) -> dict:
    """检测项目资源库中的永久 MCP 和 Skill"""
    resources_dir = project_root / ".super-harness" / "resources"
    result = {"mcp_count": 0, "skill_count": 0, "new_since_session": []}

    if not resources_dir.exists():
        return result

    mcp_dir = resources_dir / "mcp"
    if mcp_dir.exists():
        result["mcp_count"] = len(list(mcp_dir.glob("*.json")))

    skills_dir = resources_dir / "skills"
    if skills_dir.exists():
        result["skill_count"] = len([d for d in skills_dir.iterdir()
                                     if d.is_dir() and (d / "SKILL.md").exists()])

    return result


def print_maintenance_checklist(synced_path=None):
    print()
    print("=" * 60)
    print("  Super Harness — 会话结束检查")
    print("=" * 60)

    # 同步状态
    if synced_path:
        print(f"  🧠 会话已同步: {Path(synced_path).name}")
    else:
        print(f"  ⚠️  会话同步: 未检测到 transcript（手动: /sync-session）")

    print()

    # MEMORY.md 检查
    if check_memory_updated():
        print("  ✅ MEMORY.md 已在本次会话中更新")
    else:
        print("  ⚠️  MEMORY.md 尚未更新。请检查：")
        print()
        print("  📌 新的坑点 → Critical Gotchas")
        print("  📌 架构变更 → ADR 格式（正题→反题→合题）")
        print("  📌 新的编码模式 → Coding Conventions")
        print("  📌 经验教训 → memory/{}.md".format(datetime.now().strftime("%Y-%m-%d")))

    today_log = MEMORY_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.md"
    if not today_log.exists():
        print()
        print(f"  📝 今日日志: {today_log}（未创建）")

    # 项目资源库状态
    resources = detect_project_resources(PROJECT_ROOT)
    if resources["mcp_count"] or resources["skill_count"]:
        print()
        print(f"  📦 项目永久资源:")
        if resources["mcp_count"]:
            print(f"     🔌 {resources['mcp_count']} 个 MCP → .super-harness/resources/mcp/")
        if resources["skill_count"]:
            print(f"     🎯 {resources['skill_count']} 个 Skill → .super-harness/resources/skills/")
        print(f"     💡 下次 SessionStart 自动检测加载")

    # 资源库未创建提示
    resources_dir = PROJECT_ROOT / ".super-harness" / "resources"
    if not (resources_dir / "INDEX.md").exists():
        print()
        print(f"  🔰 项目资源库仍未创建。下次会话首个任务前，")
        print(f"     模型会主动提议初始化（根据 CLAUDE.md 资源库优先原则）。")

    print()
    print("  下次会话可用 MCP search_sessions 检索本次对话")
    print("=" * 60)
    print()


# ── 入口 ──────────────────────────────────────────────

def cleanup_temp_mcps():
    """清理临时安装的 MCP（不触及项目永久 MCP）"""
    try:
        from mcp_proxy import cleanup_temp_mcps as do_cleanup
        result = do_cleanup()
        return result.get("cleaned", 0)
    except Exception:
        return 0


if __name__ == "__main__":
    # 1. 尝试同步 transcript
    synced = sync_current_session()

    # 2. 清理临时 MCP（只清理 _temp_ 标记的，项目永久 MCP 保留）
    cleaned = cleanup_temp_mcps()
    if cleaned:
        print(f"  🧹 已清理 {cleaned} 个临时 MCP（项目永久 MCP 保留）")

    # 3. 输出维护清单
    print_maintenance_checklist(synced)
