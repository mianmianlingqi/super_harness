#!/usr/bin/env python3
"""
Super Harness — 手动会话同步

将 Claude Code transcript JSONL 文件导入会话记忆 DB。
用法: python sync_session.py <transcript.jsonl> [--project-key <key>]
"""

import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

from session_memory.db import get_db_connection
from session_memory.parsing import is_task_notification, is_teammate_message
from session_memory.formatting import get_project_key, normalize_cwd
from session_memory.summarizer import compute_context_summary


def hash_file(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def import_transcript(transcript_path, project_key=None):
    transcript = Path(transcript_path)
    if not transcript.exists():
        print(f"❌ 文件不存在: {transcript}")
        return False

    print(f"📄 读取: {transcript.name} ({transcript.stat().st_size / 1024:.0f} KB)")

    # 解析 JSONL
    entries = []
    with open(transcript, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    print(f"   解析到 {len(entries)} 条记录")

    # 提取会话 UUID（文件名 stem 去 agent- 前缀）
    stem = transcript.stem
    if stem.startswith("agent-"):
        stem = stem[6:]
    session_uuid = stem

    # 确定项目 key
    cwd = normalize_cwd(str(Path.cwd()))
    if not project_key:
        project_key = get_project_key(cwd)

    conn = get_db_connection()

    # 检查是否已导入
    file_hash = hash_file(transcript)
    existing = conn.execute(
        "SELECT id FROM import_log WHERE file_path = ?", (str(transcript),)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE import_log SET file_hash = ? WHERE file_path = ?",
            (file_hash, str(transcript))
        )
        print(f"   ⚠️  文件已导入过，更新 hash")
    else:
        conn.execute(
            "INSERT INTO import_log (file_path, file_hash) VALUES (?, ?)",
            (str(transcript), file_hash)
        )

    # 创建/查找项目
    proj = conn.execute(
        "SELECT id FROM session_projects WHERE key = ?", (project_key,)
    ).fetchone()
    if not proj:
        conn.execute(
            "INSERT INTO session_projects (path, key, name) VALUES (?, ?, ?)",
            (cwd, project_key, Path(cwd).name)
        )
        proj_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    else:
        proj_id = proj[0]

    # 创建/查找会话
    sess = conn.execute(
        "SELECT id FROM sessions WHERE uuid = ?", (session_uuid,)
    ).fetchone()
    if not sess:
        conn.execute(
            "INSERT INTO sessions (uuid, project_id, cwd) VALUES (?, ?, ?)",
            (session_uuid, proj_id, cwd)
        )
        session_db_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        is_new = True
    else:
        session_db_id = sess[0]
        is_new = False

    print(f"   项目: {project_key} | 会话: {session_uuid[:8]}... | {'🆕 新' if is_new else '📎 已有'}")

    # 导入消息
    msg_count = 0
    user_count = 0
    assistant_count = 0
    messages = []

    for entry in entries:
        msg_type = entry.get("type", "")
        if msg_type not in ("user", "assistant"):
            continue

        uuid = entry.get("uuid", "")
        if not uuid:
            continue

        # 检查是否已存在
        existing_msg = conn.execute(
            "SELECT id FROM session_messages WHERE session_id = ? AND uuid = ?",
            (session_db_id, uuid)
        ).fetchone()
        if existing_msg:
            continue

        content = ""
        role = msg_type

        if msg_type == "user":
            # 用户消息内容在 message.content 中
            msg = entry.get("message", {})
            if isinstance(msg, dict):
                content = msg.get("content", "")
            if isinstance(content, list):
                # Anthropic content blocks
                parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        parts.append(block.get("text", ""))
                content = " ".join(parts)
            user_count += 1
        elif msg_type == "assistant":
            # Assistant 消息在 message.content 中
            msg = entry.get("message", {})
            if isinstance(msg, dict):
                c = msg.get("content", "")
                if isinstance(c, list):
                    parts = []
                    for block in c:
                        if isinstance(block, dict) and block.get("type") == "text":
                            parts.append(block.get("text", ""))
                    content = " ".join(parts)
                else:
                    content = str(c)
            assistant_count += 1

        if not content or not content.strip():
            continue

        timestamp = entry.get("timestamp", datetime.now(timezone.utc).isoformat())
        parent_uuid = entry.get("parent_uuid", "")
        is_notif = 1 if is_task_notification(content) or is_teammate_message(content) else 0

        conn.execute("""
            INSERT OR IGNORE INTO session_messages
            (session_id, uuid, parent_uuid, timestamp, role, content, is_notification)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_db_id, uuid, parent_uuid, timestamp, role, content[:10000], is_notif))

        msg_id = conn.execute("SELECT id FROM session_messages WHERE session_id = ? AND uuid = ?",
                              (session_db_id, uuid)).fetchone()
        if msg_id:
            messages.append({"id": msg_id[0], "role": role, "content": content[:10000],
                             "timestamp": timestamp, "uuid": uuid})

        msg_count += 1

    conn.commit()
    print(f"   消息: {msg_count} 条 (用户 {user_count} / 助手 {assistant_count})")

    # 创建分支
    leaf_uuid = entries[-1].get("uuid", session_uuid) if entries else session_uuid
    branch = conn.execute(
        "SELECT id FROM branches WHERE session_id = ? AND leaf_uuid = ?",
        (session_db_id, leaf_uuid)
    ).fetchone()

    if not branch:
        first_ts = entries[0].get("timestamp", "") if entries else ""
        last_ts = entries[-1].get("timestamp", "") if entries else ""
        conn.execute("""
            INSERT INTO branches
            (session_id, leaf_uuid, is_active, started_at, ended_at, exchange_count)
            VALUES (?, ?, 1, ?, ?, ?)
        """, (session_db_id, leaf_uuid, first_ts, last_ts, user_count))
        branch_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # 关联消息到分支
        for msg in messages:
            conn.execute(
                "INSERT OR IGNORE INTO branch_messages (branch_id, message_id) VALUES (?, ?)",
                (branch_id, msg["id"])
            )

        # 生成 context summary
        try:
            summary_json, summary_md = compute_context_summary(
                conn.cursor(), branch_id
            )
            conn.execute(
                "UPDATE branches SET context_summary = ?, context_summary_json = ? WHERE id = ?",
                (summary_md, summary_json, branch_id)
            )
            print(f"   摘要: {summary_md[:100]}...")
        except Exception as e:
            print(f"   ⚠️  摘要生成跳过: {e}")

    conn.commit()
    conn.close()

    print(f"✅ 同步完成: {session_uuid[:8]}... → {msg_count} 条消息")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python sync_session.py <transcript.jsonl> [--project-key <key>]")
        sys.exit(1)

    transcript_file = sys.argv[1]
    proj_key = None
    if "--project-key" in sys.argv:
        idx = sys.argv.index("--project-key")
        if idx + 1 < len(sys.argv):
            proj_key = sys.argv[idx + 1]

    import_transcript(transcript_file, proj_key)
