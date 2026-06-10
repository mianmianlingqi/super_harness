"""
Session memory database — 会话存储层

从 claude-memory (MIT) 移植，适配 Super Harness 的 harness.db。
管理 projects / sessions / branches / messages / branch_messages / import_log 六张表。
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Optional

# ── 路径配置 ──────────────────────────────────────────────

# 复用 Super Harness 的 harness.db
HARNESS_DB = Path.home() / ".super-harness" / "vector-store" / "harness.db"

# ── 默认设置 ──────────────────────────────────────────────

DEFAULT_SETTINGS = {
    "auto_inject_context": True,
    "max_context_sessions": 2,
    "exclude_projects": [],
    "sync_on_stop": True,
    "consolidation_reminder_enabled": True,
    "consolidation_min_hours": 24,
    "consolidation_min_sessions": 5,
}

_CONFIG_KEYS = {
    "auto_inject_context",
    "consolidation_reminder_enabled",
    "consolidation_min_hours",
    "consolidation_min_sessions",
    "max_context_sessions",
}

# ── Schema ─────────────────────────────────────────────────

SCHEMA_CORE = """
CREATE TABLE IF NOT EXISTS session_projects (
  id INTEGER PRIMARY KEY,
  path TEXT UNIQUE NOT NULL,
  key TEXT UNIQUE NOT NULL,
  name TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_session_projects_key ON session_projects(key);

CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY,
  uuid TEXT UNIQUE NOT NULL,
  project_id INTEGER REFERENCES session_projects(id),
  parent_session_id INTEGER REFERENCES sessions(id),
  git_branch TEXT,
  cwd TEXT,
  imported_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_id);

CREATE TABLE IF NOT EXISTS branches (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(id),
  leaf_uuid TEXT NOT NULL,
  fork_point_uuid TEXT,
  is_active INTEGER DEFAULT 1,
  started_at DATETIME,
  ended_at DATETIME,
  exchange_count INTEGER DEFAULT 0,
  files_modified TEXT,
  commits TEXT,
  tool_counts TEXT,
  aggregated_content TEXT,
  context_summary TEXT,
  context_summary_json TEXT,
  summary_version INTEGER DEFAULT 0,
  UNIQUE(session_id, leaf_uuid)
);
CREATE INDEX IF NOT EXISTS idx_branches_session ON branches(session_id);
CREATE INDEX IF NOT EXISTS idx_branches_active ON branches(is_active);

CREATE TABLE IF NOT EXISTS session_messages (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(id),
  uuid TEXT,
  parent_uuid TEXT,
  timestamp DATETIME,
  role TEXT CHECK(role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  tool_summary TEXT,
  has_tool_use INTEGER DEFAULT 0,
  has_thinking INTEGER DEFAULT 0,
  is_notification INTEGER DEFAULT 0,
  origin TEXT,
  UNIQUE(session_id, uuid)
);
CREATE INDEX IF NOT EXISTS idx_session_messages_session ON session_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_session_messages_timestamp ON session_messages(timestamp);

CREATE TABLE IF NOT EXISTS branch_messages (
  branch_id INTEGER NOT NULL REFERENCES branches(id),
  message_id INTEGER NOT NULL REFERENCES session_messages(id),
  PRIMARY KEY (branch_id, message_id)
);

CREATE TABLE IF NOT EXISTS import_log (
  id INTEGER PRIMARY KEY,
  file_path TEXT UNIQUE NOT NULL,
  file_hash TEXT,
  imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  messages_imported INTEGER DEFAULT 0
);
"""

SCHEMA_FTS5 = """
CREATE VIRTUAL TABLE IF NOT EXISTS session_messages_fts USING fts5(
  content,
  content=session_messages,
  content_rowid=id,
  tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS session_messages_ai AFTER INSERT ON session_messages BEGIN
  INSERT INTO session_messages_fts(rowid, content) VALUES (new.id, new.content);
END;
CREATE TRIGGER IF NOT EXISTS session_messages_ad AFTER DELETE ON session_messages BEGIN
  INSERT INTO session_messages_fts(session_messages_fts, rowid, content) VALUES('delete', old.id, old.content);
END;
CREATE TRIGGER IF NOT EXISTS session_messages_au AFTER UPDATE ON session_messages BEGIN
  INSERT INTO session_messages_fts(session_messages_fts, rowid, content) VALUES('delete', old.id, old.content);
  INSERT INTO session_messages_fts(rowid, content) VALUES (new.id, new.content);
END;

CREATE VIRTUAL TABLE IF NOT EXISTS branches_fts USING fts5(
  aggregated_content,
  content=branches,
  content_rowid=id,
  tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS branches_ai AFTER INSERT ON branches BEGIN
  INSERT INTO branches_fts(rowid, aggregated_content) VALUES (new.id, new.aggregated_content);
END;
CREATE TRIGGER IF NOT EXISTS branches_ad AFTER DELETE ON branches BEGIN
  INSERT INTO branches_fts(branches_fts, rowid, aggregated_content) VALUES('delete', old.id, old.aggregated_content);
END;
CREATE TRIGGER IF NOT EXISTS branches_au AFTER UPDATE ON branches BEGIN
  INSERT INTO branches_fts(branches_fts, rowid, aggregated_content) VALUES('delete', old.id, old.aggregated_content);
  INSERT INTO branches_fts(rowid, aggregated_content) VALUES (new.id, new.aggregated_content);
END;
"""

SCHEMA = SCHEMA_CORE + SCHEMA_FTS5


# ── FTS 检测 ──────────────────────────────────────────────

def detect_fts_support(conn: sqlite3.Connection) -> Optional[str]:
    try:
        opts = {row[0] for row in conn.execute("PRAGMA compile_options").fetchall()}
    except Exception:
        return None
    if "ENABLE_FTS5" in opts:
        return "fts5"
    if "ENABLE_FTS4" in opts or "ENABLE_FTS3" in opts:
        return "fts4"
    return None


# ── 设置加载 ──────────────────────────────────────────────

def load_settings() -> dict:
    return DEFAULT_SETTINGS.copy()


# ── DB 连接 ───────────────────────────────────────────────

def get_db_connection(settings: Optional[dict] = None) -> sqlite3.Connection:
    db_path = HARNESS_DB
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))

    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA foreign_keys = ON")

    fts = detect_fts_support(conn)
    conn.executescript(SCHEMA_CORE)
    if fts == "fts5":
        conn.executescript(SCHEMA_FTS5)
    conn.commit()

    return conn
