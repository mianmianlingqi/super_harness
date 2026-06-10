"""
session_memory — Super Harness 会话记忆模块

从 claude-memory (MIT) 移植，适配 Super Harness 架构。
提供：会话存储、transcript 解析、摘要生成、上下文注入。
"""

from .db import get_db_connection, load_settings, DEFAULT_SETTINGS
from .content import (
    extract_text_content,
    parse_origin,
    is_task_notification,
    is_teammate_message,
    is_tool_result,
    extract_files_modified,
    extract_commits,
)
from .summarizer import (
    build_exchange_pairs,
    build_context_summary_json,
    render_context_summary,
    compute_context_summary,
    truncate_mid,
)
from .formatting import (
    format_time,
    format_time_full,
    get_project_key,
    normalize_cwd,
    format_markdown_session,
)
