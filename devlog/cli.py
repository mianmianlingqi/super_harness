#!/usr/bin/env python3
"""
devlog — 开发者工作日志 CLI 工具

零依赖，纯标准库实现。
Super Harness 协议的"文档驱动" + "单一真源"原则的应用示例：
  - 所有日志存为 Markdown 文件（文档驱动）
  - .devlog/ 为项目级日志，~/.devlog/ 为全局日志（中央存储）
  - JSON 索引加速查询（类似 harness_db.py 的 SQLite 设计）

用法:
  devlog start "修复登录 bug"     # 开始一项工作
  devlog done                     # 标记当前工作完成
  devlog note "发现一个坑"        # 追加笔记
  devlog today                    # 查看今天的工作
  devlog report --week            # 本周工作总结
  devlog search "认证"            # 搜索日志
  devlog stats                    # 统计
"""

from typing import Optional, Union, Dict, List, Any

import json
import os
import re
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

# ── 路径 ──────────────────────────────────────────────────

def _devlog_dir(global_: bool = False) -> Path:
    if global_:
        return Path.home() / ".devlog"
    return Path.cwd() / ".devlog"


def _today_file(global_: bool = False) -> Path:
    return _devlog_dir(global_) / f"{date.today().isoformat()}.md"


# ── 核心读写 ──────────────────────────────────────────────

def _ensure_dir(global_: bool = False):
    d = _devlog_dir(global_)
    d.mkdir(parents=True, exist_ok=True)


def _read_entries(filepath: Path) -> list:
    """读取日志文件，解析为条目列表"""
    if not filepath.exists():
        return []
    text = filepath.read_text(encoding="utf-8")
    entries = []
    # 按 ## 标题分割
    parts = re.split(r"\n(?=## )", text)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        entry = _parse_block(part)
        if entry:
            entries.append(entry)
    return entries


def _parse_block(block: str) -> Optional[Dict]:
    """解析一个条目块"""
    lines = block.strip().split("\n")
    header = lines[0].strip()
    # ## 10:30-11:45 | [done] 修复登录 bug | [tags:前端,紧急]
    m = re.match(
        r"^##\s+(\d{1,2}:\d{2})(?:-(\d{1,2}:\d{2}))?\s*"
        r"(?:\|\s*\[(\w+)\])?\s*"
        r"(?:\|\s*(.+?))?\s*"
        r"(?:\|\s*\[tags:(.+?)\])?\s*$",
        header,
    )
    if not m:
        return None

    start = m.group(1)
    end = m.group(2)
    status = m.group(3) or "active"
    title = (m.group(4) or "").strip()
    tags = [t.strip() for t in (m.group(5) or "").split(",") if t.strip()]

    body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

    return {
        "start": start,
        "end": end,
        "status": status,
        "title": title,
        "tags": tags,
        "body": body,
    }


def _append_entry(filepath: Path, entry: dict):
    """追加条目到文件尾"""
    _ensure_dir()
    tags_str = f"[tags:{','.join(entry['tags'])}]" if entry["tags"] else ""
    status_str = f"[{entry['status']}]" if entry["status"] != "active" else ""

    header_parts = [entry["start"]]
    if entry.get("end"):
        header_parts[0] = f"{header_parts[0]}-{entry['end']}"
    if status_str:
        header_parts.append(status_str)
    header_parts.append(f"| {entry['title']}")
    if tags_str:
        header_parts.append(tags_str)

    header = f"## {' | '.join(header_parts)}"

    body = entry.get("body", "").strip()
    block = f"\n{header}\n\n{body}\n" if body else f"\n{header}\n"

    with open(filepath, "a", encoding="utf-8") as f:
        f.write(block)


def _active_file() -> Path:
    return _devlog_dir() / "_active.json"


def _read_active() -> Optional[Dict]:
    """读取当前活跃任务"""
    af = _active_file()
    if not af.exists():
        return None
    return json.loads(af.read_text(encoding="utf-8"))


def _write_active(data):
    _ensure_dir()
    af = _active_file()
    if data is None:
        af.unlink(missing_ok=True)
    else:
        af.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ── 命令实现 ──────────────────────────────────────────────

def cmd_start(title: str, tags: list[str] = None, global_: bool = False):
    """开始一项新工作"""
    active = _read_active()
    if active:
        print(f"已有进行中的任务: {active['title']} (从 {active['start']} 开始)")
        print("先用 'devlog done' 结束当前任务，或用 'devlog cancel' 取消")
        return

    now = datetime.now().strftime("%H:%M")
    entry = {
        "start": now,
        "status": "active",
        "title": title,
        "tags": tags or [],
        "body": "",
    }
    _write_active(entry)
    print(f"✅ 开始: {title}")


def cmd_done(global_: bool = False):
    """完成当前活跃任务"""
    active = _read_active()
    if not active:
        print("没有进行中的任务")
        return

    now = datetime.now().strftime("%H:%M")
    active["end"] = now
    active["status"] = "done"
    duration = _duration_minutes(active["start"], now)
    active["body"] = active.get("body", "") + f"\n\n⏱ 耗时: {duration} 分钟"

    filepath = _today_file(global_)
    _append_entry(filepath, active)
    _write_active(None)
    print(f"✅ 完成: {active['title']} ({duration} 分钟)")


def cmd_note(text: str, global_: bool = False):
    """追加笔记到当前活跃任务"""
    active = _read_active()
    if not active:
        # 无活跃任务，直接写一条独立笔记
        active = {
            "start": datetime.now().strftime("%H:%M"),
            "status": "note",
            "title": "快速笔记",
            "tags": [],
            "body": text,
        }
        filepath = _today_file(global_)
        _append_entry(filepath, active)
        _write_active(None)
        print("📝 已记录")
        return

    timestamp = datetime.now().strftime("%H:%M")
    active["body"] = active.get("body", "") + f"\n\n[{timestamp}] {text}"
    _write_active(active)
    print(f"📝 已追加到: {active['title']}")


def cmd_cancel(global_: bool = False):
    """取消当前活跃任务（不记录）"""
    active = _read_active()
    if not active:
        print("没有进行中的任务")
        return
    title = active["title"]
    _write_active(None)
    print(f"❌ 已取消: {title}")


def cmd_today(global_: bool = False):
    """查看今天的工作日志"""
    filepath = _today_file(global_)
    if not filepath.exists():
        print("今天还没有日志")
        active = _read_active()
        if active:
            print(f"\n当前进行中: {active['title']} (从 {active['start']} 开始)")
        return

    # 检查活跃任务
    active = _read_active()
    entries = _read_entries(filepath)
    total = sum(_duration_minutes(e["start"], e.get("end")) for e in entries if e["end"])
    done = sum(1 for e in entries if e["status"] == "done")

    status_map = {"done": "✅", "active": "🔄", "note": "📝", "cancelled": "❌"}

    print(f"📅 {date.today().isoformat()}")
    print(f"   已完成: {done} 项 | 总耗时: {total} 分钟")
    if active:
        print(f"   🔄 进行中: {active['title']} (从 {active['start']} 开始)")
    print()

    for e in entries:
        icon = status_map.get(e["status"], "❓")
        time_range = f"{e['start']}-{e.get('end', '...')}"
        tags = f" [{', '.join(e['tags'])}]" if e.get("tags") else ""
        print(f"  {icon} {time_range} | {e['title']}{tags}")
        if e.get("body"):
            for line in e["body"].strip().split("\n")[:3]:
                print(f"      {line.strip()}")


def cmd_search(query: str, global_: bool = False, days: int = 30):
    """搜索日志"""
    d = _devlog_dir(global_)
    if not d.exists():
        print("暂无日志")
        return

    cutoff = date.today() - timedelta(days=days)
    matches = []
    for f in sorted(d.glob("*.md"), reverse=True):
        if f.name.startswith("_"):
            continue
        try:
            file_date = date.fromisoformat(f.stem)
            if file_date < cutoff:
                continue
        except ValueError:
            continue

        entries = _read_entries(f)
        for e in entries:
            needle = query.lower()
            in_title = needle in e["title"].lower()
            in_body = needle in e.get("body", "").lower()
            in_tags = any(needle in t.lower() for t in e.get("tags", []))
            if in_title or in_body or in_tags:
                matches.append((f.stem, e, in_title, in_body, in_tags))

    if not matches:
        print(f"未找到匹配 \"{query}\" 的日志 (最近 {days} 天)")
        return

    print(f"🔍 搜索 \"{query}\" — {len(matches)} 条结果\n")
    for file_date, e, *flags in matches[:20]:
        icon = "✅" if e["status"] == "done" else "📝"
        print(f"  {icon} [{file_date}] {e['start']} | {e['title']}")
        body = e.get("body", "").strip()
        if body:
            snippet = body[:120].replace("\n", " ")
            print(f"      {snippet}...")
        print()


def cmd_report(period: str = "week", global_: bool = False):
    """生成工作报告"""
    if period == "week":
        days = 7
        title = "本周工作总结"
    elif period == "month":
        days = 30
        title = "本月工作总结"
    else:
        days = 1
        title = "今日工作总结"

    d = _devlog_dir(global_)
    if not d.exists():
        print("暂无日志")
        return

    cutoff = date.today() - timedelta(days=days)
    all_entries = []
    tags_count = {}
    total_minutes = 0

    for f in sorted(d.glob("*.md")):
        if f.name.startswith("_"):
            continue
        try:
            file_date = date.fromisoformat(f.stem)
            if file_date < cutoff:
                continue
        except ValueError:
            continue

        entries = _read_entries(f)
        for e in entries:
            if e["status"] != "done":
                continue
            all_entries.append((f.stem, e))
            duration = _duration_minutes(e["start"], e.get("end"))
            total_minutes += duration
            for t in e.get("tags", []):
                tags_count[t] = tags_count.get(t, 0) + 1

    print(f"📊 {title}")
    print(f"   日期范围: {cutoff.isoformat()} ~ {date.today().isoformat()}")
    print(f"   完成任务: {len(all_entries)} 项")
    print(f"   总耗时: {total_minutes} 分钟 ({total_minutes / 60:.1f} 小时)")
    print()

    if tags_count:
        print("🏷️  标签统计:")
        for tag, count in sorted(tags_count.items(), key=lambda x: -x[1]):
            bar = "█" * min(count, 20)
            print(f"   {tag:<15} {bar} {count}")
        print()

    if all_entries:
        print("📋 完成任务:")
        for file_date, e in all_entries[:30]:
            duration = _duration_minutes(e["start"], e.get("end"))
            print(f"   [{file_date}] {e['title']} ({duration} 分钟)")


def cmd_stats(global_: bool = False):
    """显示统计信息"""
    d = _devlog_dir(global_)
    if not d.exists():
        print("暂无日志")
        return

    total_entries = 0
    total_done = 0
    total_minutes = 0
    days_with_logs = 0
    streak = 0
    current_streak = 0
    tags = {}

    today = date.today()
    for i in range(365):
        check_date = today - timedelta(days=i)
        f = d / f"{check_date.isoformat()}.md"
        if f.exists():
            if i == 0 or (i > 0 and (d / f"{(today - timedelta(days=i - 1)).isoformat()}.md").exists()):
                current_streak += 1
            else:
                current_streak = 1
            streak = max(streak, current_streak)
            days_with_logs += 1
            entries = _read_entries(f)
            total_entries += len(entries)
            for e in entries:
                if e["status"] == "done":
                    total_done += 1
                    total_minutes += _duration_minutes(e["start"], e.get("end"))
                for t in e.get("tags", []):
                    tags[t] = tags.get(t, 0) + 1
        else:
            current_streak = 0

    active = _read_active()

    print("📊 devlog 统计")
    print(f"   总条目: {total_entries}")
    print(f"   已完成: {total_done}")
    print(f"   总耗时: {total_minutes} 分钟 ({total_minutes / 60:.1f} 小时)")
    print(f"   有日志的天数: {days_with_logs}")
    print(f"   最长连续天数: {streak}")
    if active:
        print(f"   🔄 进行中: {active['title']}")
    print()

    if tags:
        print("🏷️  最常用标签:")
        for tag, count in sorted(tags.items(), key=lambda x: -x[1])[:10]:
            print(f"   {tag}: {count}")


# ── 工具函数 ──────────────────────────────────────────────

def _duration_minutes(start: str, end: Optional[str]) -> int:
    """计算两时间之间的分钟数"""
    if not end:
        return 0
    try:
        sh, sm = map(int, start.split(":"))
        eh, em = map(int, end.split(":"))
        return max(0, (eh * 60 + em) - (sh * 60 + sm))
    except (ValueError, AttributeError):
        return 0


# ── CLI 入口 ──────────────────────────────────────────────

USAGE = """devlog — 开发者工作日志

用法:
  devlog start <标题> [--tags tag1,tag2]  # 开始一项工作
  devlog done                                # 完成当前工作
  devlog note <内容>                        # 追加笔记
  devlog cancel                              # 取消当前工作
  devlog today                               # 查看今天日志
  devlog search <关键词> [--days N]         # 搜索日志
  devlog report [--week|--month]             # 工作总结
  devlog stats                               # 统计信息

文件结构:
  .devlog/YYYY-MM-DD.md    — 每日日志
  .devlog/_active.json     — 当前活跃任务
  ~/.devlog/               — 全局日志（跨项目）"""


def main():
    args = sys.argv[1:]
    if not args:
        print(USAGE)
        return

    cmd = args[0]
    global_ = "--global" in args
    args = [a for a in args if a != "--global"]

    try:
        if cmd == "start":
            title_parts = []
            tags = []
            i = 1
            while i < len(args):
                if args[i] == "--tags" and i + 1 < len(args):
                    tags = [t.strip() for t in args[i + 1].split(",")]
                    i += 2
                else:
                    title_parts.append(args[i])
                    i += 1
            title = " ".join(title_parts)
            if not title:
                print("用法: devlog start <标题> [--tags tag1,tag2]")
                return
            cmd_start(title, tags, global_)

        elif cmd == "done":
            cmd_done(global_)

        elif cmd == "note":
            text = " ".join(args[1:])
            if not text:
                print("用法: devlog note <内容>")
                return
            cmd_note(text, global_)

        elif cmd == "cancel":
            cmd_cancel(global_)

        elif cmd == "today":
            cmd_today(global_)

        elif cmd == "search":
            query_parts = []
            days = 30
            i = 1
            while i < len(args):
                if args[i] == "--days" and i + 1 < len(args):
                    days = int(args[i + 1])
                    i += 2
                else:
                    query_parts.append(args[i])
                    i += 1
            query = " ".join(query_parts)
            if not query:
                print("用法: devlog search <关键词> [--days N]")
                return
            cmd_search(query, global_, days)

        elif cmd == "report":
            period = "week"
            if "--month" in args:
                period = "month"
            elif "--week" in args:
                period = "week"
            cmd_report(period, global_)

        elif cmd == "stats":
            cmd_stats(global_)

        else:
            print(f"未知命令: {cmd}")
            print(USAGE)

    except KeyboardInterrupt:
        print("\n已取消")


if __name__ == "__main__":
    main()
