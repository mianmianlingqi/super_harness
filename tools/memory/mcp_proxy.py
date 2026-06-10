#!/usr/bin/env python3
"""
MCP 动态代理 — 临时/永久安装外部 MCP Server 和 Skill

原理: 启动外部 MCP Server 为子进程 → JSON-RPC 通信 → 代理工具调用
存储: 临时安装 → ~/.claude/.mcp.json (_temp 标记)
      永久安装 → .super-harness/resources/mcp/<name>.json
      永久 Skill → .super-harness/resources/skills/<name>/SKILL.md
"""

import json
import subprocess
import sys
import os
import re
import signal
import atexit
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# 已启动的子进程
_SPAWNED: dict[str, subprocess.Popen] = {}

# 临时安装记录（用于 Stop 时清理 .mcp.json）
TEMP_INSTALLS: list[str] = []

# MCP 握手超时（秒）
HANDSHAKE_TIMEOUT = 10
TOOL_CALL_TIMEOUT = 30

# 允许的包管理器白名单
ALLOWED_COMMANDS = {"npx", "uvx", "python", "python3", "pipx", "node"}

# Skill 名称安全正则：只允许字母数字和 . _ -
_SKILL_NAME_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$')


def _cleanup():
    """清理所有子进程"""
    for name, proc in _SPAWNED.items():
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    _SPAWNED.clear()

atexit.register(_cleanup)


def _read_line_with_timeout(proc, timeout: int) -> Optional[str]:
    """带超时的 readline — 子进程不响应时不会永久阻塞"""
    result = []
    exception = []

    def _read():
        try:
            line = proc.stdout.readline()
            result.append(line)
        except Exception as e:
            exception.append(e)

    t = threading.Thread(target=_read, daemon=True)
    t.start()
    t.join(timeout)

    if t.is_alive():
        # 超时了 — 线程还在阻塞 readline
        return None
    if exception:
        return None
    return result[0] if result else None


def _read_stderr(proc) -> str:
    """非阻塞读取 stderr 中的错误信息"""
    try:
        import select
        ready, _, _ = select.select([proc.stderr], [], [], 0.1)
        if ready:
            return proc.stderr.read(4096) or ""
    except Exception:
        pass
    return ""


def _is_valid_initialize_response(resp: dict) -> bool:
    """验证 initialize 响应是否是合法的 MCP JSON-RPC 响应"""
    if not isinstance(resp, dict):
        return False
    if resp.get("jsonrpc") != "2.0":
        return False
    result = resp.get("result", {})
    if not isinstance(result, dict):
        return False
    # MCP initialize 响应必须有 capabilities 字段
    if "capabilities" not in result:
        return False
    if "protocolVersion" not in result:
        return False
    return True


def proxy_mcp_call(server_command: str, tool_name: str,
                   tool_args: dict = None) -> dict:
    """
    动态启动 MCP Server 并调用指定工具

    带超时保护：握手 10s 超时，工具调用 30s 超时。
    非 MCP 进程会快速报错而非永久阻塞。

    Args:
        server_command: npx/pip/uvx 命令，如 "npx -y @playwright/mcp"
        tool_name: 工具名，如 "browser_navigate"
        tool_args: 工具参数

    Returns:
        {"result": ..., "error": None} 或 {"result": None, "error": "..."}
    """
    if tool_args is None:
        tool_args = {}

    # 安全验证：拒绝未授权的可执行文件和 shell 元字符
    ok, err = _validate_command(server_command)
    if not ok:
        return {"result": None, "error": err}

    cache_key = f"{server_command}::{tool_name}"

    # 复用已启动的进程
    if cache_key in _SPAWNED:
        proc = _SPAWNED[cache_key]
    else:
        # 启动 MCP Server 子进程
        parts = server_command.split()
        try:
            proc = subprocess.Popen(
                parts,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            _SPAWNED[cache_key] = proc

            # MCP 握手: initialize
            init_req = json.dumps({
                "jsonrpc": "2.0", "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "super-harness-proxy", "version": "1.0"}
                }
            })
            proc.stdin.write(init_req + "\n")
            proc.stdin.flush()

            # 读 initialize 响应（带超时）
            init_line = _read_line_with_timeout(proc, HANDSHAKE_TIMEOUT)
            if init_line is None:
                stderr_text = _read_stderr(proc)
                _SPAWNED.pop(cache_key, None)
                try:
                    proc.kill()
                except Exception:
                    pass
                return {
                    "result": None,
                    "error": f"MCP 握手超时 ({HANDSHAKE_TIMEOUT}s): 子进程可能不是 MCP Server。"
                             f" 尝试用 search_capability 找真正的 MCP Server。"
                             + (f" stderr: {stderr_text[:200]}" if stderr_text else "")
                }

            if not init_line or not init_line.strip():
                stderr_text = _read_stderr(proc)
                exit_code = proc.poll()
                _SPAWNED.pop(cache_key, None)
                return {
                    "result": None,
                    "error": f"MCP Server 启动失败：进程无响应 (exit_code={exit_code})。"
                             f" 确认 '{parts[0]}' 启动的是 MCP Server 而非普通程序。"
                             + (f" stderr: {stderr_text[:200]}" if stderr_text else "")
                }

            # 验证 initialize 响应
            try:
                init_resp = json.loads(init_line.strip())
            except json.JSONDecodeError:
                stderr_text = _read_stderr(proc)
                _SPAWNED.pop(cache_key, None)
                try:
                    proc.kill()
                except Exception:
                    pass
                return {
                    "result": None,
                    "error": f"MCP 握手失败：返回的不是 JSON。这很可能不是 MCP Server。"
                             f" 前 100 字符: {init_line.strip()[:100]}"
                }

            if not _is_valid_initialize_response(init_resp):
                stderr_text = _read_stderr(proc)
                _SPAWNED.pop(cache_key, None)
                try:
                    proc.kill()
                except Exception:
                    pass
                return {
                    "result": None,
                    "error": f"MCP 握手失败：响应不符合 MCP 协议。"
                             f" 响应: {json.dumps(init_resp, ensure_ascii=False)[:200]}"
                             + (f" stderr: {stderr_text[:200]}" if stderr_text else "")
                }

            # 收到 valid initialize 后发送 initialized 通知
            proc.stdin.write(json.dumps({
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }) + "\n")
            proc.stdin.flush()

        except FileNotFoundError:
            return {"result": None, "error": f"命令未找到: {parts[0]}"}
        except Exception as e:
            return {"result": None, "error": f"启动失败: {str(e)}"}

    # 调用工具
    try:
        call_req = json.dumps({
            "jsonrpc": "2.0", "id": 2,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": tool_args}
        })
        proc.stdin.write(call_req + "\n")
        proc.stdin.flush()

        resp_line = _read_line_with_timeout(proc, TOOL_CALL_TIMEOUT)
        if resp_line is None:
            return {"result": None, "error": f"工具调用超时 ({TOOL_CALL_TIMEOUT}s)"}

        if not resp_line or not resp_line.strip():
            return {"result": None, "error": "工具调用无响应（MCP Server 可能已崩溃）"}

        resp = json.loads(resp_line.strip())
        if "error" in resp:
            return {"result": None, "error": resp["error"].get("message", str(resp["error"]))}
        return {"result": resp.get("result", {}), "error": None}

    except Exception as e:
        return {"result": None, "error": str(e)}


def _validate_command(command: str) -> tuple[bool, str]:
    """验证 MCP 安装命令是否安全

    只允许白名单中的包管理器，拒绝含 shell 元字符的命令。
    """
    if not command or not command.strip():
        return False, "命令不能为空"

    parts = command.strip().split()
    executable = parts[0]

    # 包管理器必须在白名单中
    if executable not in ALLOWED_COMMANDS:
        return False, f"不允许的命令 '{executable}'，仅支持: {', '.join(sorted(ALLOWED_COMMANDS))}"

    # 检查每个参数是否有 shell 元字符注入
    dangerous = re.compile(r'[;&|`$(){}\[\]<>!#]')
    for i, part in enumerate(parts[1:], 1):
        if dangerous.search(part):
            return False, f"参数 {i} 包含禁止字符: '{part}'"

    return True, ""


def _validate_skill_name(name: str) -> tuple[bool, str]:
    """验证 Skill 名称安全：拒绝路径穿越和特殊字符"""
    if not name:
        return False, "名称不能为空"
    if not _SKILL_NAME_RE.match(name):
        return False, f"名称 '{name}' 不合法，只允许字母数字和 . _ -，最长 64 字符"
    if ".." in name:
        return False, "名称不能包含 '..'"
    return True, ""


def temp_install_mcp(name: str, command: str, args: list = None) -> dict:
    """
    临时安装 MCP 到 .mcp.json（带 _temp 标记）

    会话结束后 Stop hook 自动清理。
    需要重启 Claude Code 才能加载新 MCP（或使用 proxy_mcp_call 本轮直接调用）。

    Returns:
        {"installed": True/False, "message": "...", "needs_restart": True}
    """
    mcp_json = Path.home() / ".claude" / ".mcp.json"

    try:
        config = json.loads(mcp_json.read_text(encoding='utf-8'))
    except Exception:
        config = {}

    temp_name = f"_temp_{name}"

    if temp_name in config:
        return {"installed": False, "message": f"{name} 已临时安装", "needs_restart": True}

    # 安全验证：command 必须在白名单中
    ok, err = _validate_command(command)
    if not ok:
        return {"installed": False, "error": err}

    config[temp_name] = {
        "type": "stdio",
        "command": command.split()[0],
        "args": command.split()[1:] + (args or []),
        "_temp": True,
        "_installed_at": str(Path.cwd()),
    }

    mcp_json.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding='utf-8')
    TEMP_INSTALLS.append(temp_name)

    return {
        "installed": True,
        "message": f"✅ {name} 已临时安装。重启 Claude Code 后生效。会话结束后自动卸载。",
        "needs_restart": True,
        "uninstall": f"Stop hook 会自动清理 {temp_name}",
    }


def cleanup_temp_mcps() -> dict:
    """清理所有临时安装的 MCP"""
    mcp_json = Path.home() / ".claude" / ".mcp.json"
    try:
        config = json.loads(mcp_json.read_text(encoding='utf-8'))
    except Exception:
        return {"cleaned": 0}

    removed = []
    for key in list(config.keys()):
        if key.startswith("_temp_") or config[key].get("_temp"):
            del config[key]
            removed.append(key)

    if removed:
        mcp_json.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding='utf-8')

    return {"cleaned": len(removed), "removed": removed}


# ── 项目级永久安装 ──────────────────────────────────────

def _get_resources_dir(project_root: str = None) -> Path:
    """获取项目资源库目录"""
    if project_root:
        root = Path(project_root)
    else:
        root = Path.cwd()
    return root / ".super-harness" / "resources"


def perm_install_mcp(name: str, command: str, args: list = None,
                     description: str = "", project_root: str = None) -> dict:
    """
    永久安装 MCP 到项目资源库

    将 MCP Server 配置写入 .super-harness/resources/mcp/<name>.json，
    跨会话保留，可 Git 版本控制。

    Args:
        name: MCP Server 名称
        command: 启动命令 (如 "npx" 或 "python")
        args: 命令参数列表 (如 ["-y", "@playwright/mcp"])
        description: 用途描述
        project_root: 项目根目录（默认当前目录）

    Returns:
        {"installed": bool, "path": str, "message": str}
    """
    resources = _get_resources_dir(project_root)
    mcp_dir = resources / "mcp"
    mcp_dir.mkdir(parents=True, exist_ok=True)

    # 安全验证：name 不能含路径穿越，command 必须在白名单
    ok, err = _validate_skill_name(name)
    if not ok:
        return {"installed": False, "error": err}

    ok, err = _validate_command(f"{command} {' '.join(args or [])}".strip())
    if not ok:
        return {"installed": False, "error": err}

    mcp_file = mcp_dir / f"{name}.json"

    if args is None:
        args = []

    config = {
        "name": name,
        "command": command,
        "args": args,
        "description": description,
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "installed_by": "super-harness",
        "last_used": None,
        "use_count": 0,
    }

    mcp_file.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding='utf-8')

    # 同时更新 INDEX.md
    _update_resource_index(resources, "mcp", name, description)

    return {
        "installed": True,
        "path": str(mcp_file),
        "message": f"✅ MCP '{name}' 已永久安装到项目资源库。SessionStart 自动检测。",
        "activate": f"将以下配置添加到项目 .claude/.mcp.json 即可激活:\n{json.dumps({name: {'command': command, 'args': args}}, indent=2)}",
    }


def perm_install_skill(name: str, description: str, content: str,
                       project_root: str = None) -> dict:
    """
    永久安装 Skill 到项目资源库

    将 Skill 写入 .super-harness/resources/skills/<name>/SKILL.md，
    跨会话保留，可 Git 版本控制。

    Args:
        name: Skill 名称
        description: 用途描述
        content: SKILL.md 完整内容（含 frontmatter）
        project_root: 项目根目录（默认当前目录）

    Returns:
        {"installed": bool, "path": str, "message": str}
    """
    resources = _get_resources_dir(project_root)

    # 安全验证：name 必须合法，防止路径穿越
    ok, err = _validate_skill_name(name)
    if not ok:
        return {"installed": False, "error": err}

    skill_dir = resources / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)

    skill_file = skill_dir / "SKILL.md"

    # 二次确认：解析出的路径必须仍在 resources/skills/ 下
    real_skill = skill_file.resolve()
    real_skills_root = (resources / "skills").resolve()
    try:
        real_skill.relative_to(real_skills_root)
    except ValueError:
        return {"installed": False, "error": f"路径穿越拒绝: '{name}' 试图逃逸 skills 目录"}

    # 如果 content 不含 frontmatter，自动生成
    if not content.strip().startswith("---"):
        content = f"""---
name: {name}
description: {description}
---

{content}"""

    skill_file.write_text(content, encoding='utf-8')

    # 更新 INDEX.md
    _update_resource_index(resources, "skill", name, description)

    return {
        "installed": True,
        "path": str(skill_file),
        "message": f"✅ Skill '{name}' 已永久安装到项目资源库。SessionStart 自动检测。",
    }


def list_project_mcps(project_root: str = None) -> list:
    """列出项目资源库中已安装的 MCP"""
    resources = _get_resources_dir(project_root)
    mcp_dir = resources / "mcp"
    if not mcp_dir.exists():
        return []

    mcps = []
    for f in sorted(mcp_dir.glob("*.json")):
        try:
            cfg = json.loads(f.read_text(encoding='utf-8'))
            mcps.append({
                "name": cfg.get("name", f.stem),
                "command": cfg.get("command", ""),
                "args": cfg.get("args", []),
                "description": cfg.get("description", ""),
                "installed_at": cfg.get("installed_at", ""),
                "last_used": cfg.get("last_used"),
                "use_count": cfg.get("use_count", 0),
                "file": str(f),
            })
        except Exception:
            mcps.append({"name": f.stem, "file": str(f), "error": "解析失败"})
    return mcps


def list_project_skills(project_root: str = None) -> list:
    """列出项目资源库中已安装的 Skill"""
    resources = _get_resources_dir(project_root)
    skills_dir = resources / "skills"
    if not skills_dir.exists():
        return []

    skills = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        try:
            content = skill_file.read_text(encoding='utf-8')
            # 解析 frontmatter
            name = skill_dir.name
            desc = ""
            if content.startswith("---"):
                end = content.find("---", 3)
                if end > 0:
                    fm = content[3:end]
                    for line in fm.split("\n"):
                        line = line.strip()
                        if line.startswith("name:"):
                            name = line.split(":", 1)[1].strip()
                        elif line.startswith("description:"):
                            desc = line.split(":", 1)[1].strip()
            skills.append({
                "name": name,
                "description": desc,
                "directory": str(skill_dir),
                "file": str(skill_file),
            })
        except Exception:
            skills.append({"name": skill_dir.name, "directory": str(skill_dir), "error": "解析失败"})
    return skills


def _update_resource_index(resources: Path, rtype: str, name: str, description: str):
    """更新 INDEX.md 添加新资源条目"""
    index_file = resources / "INDEX.md"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    new_entry = f"| {today} | {rtype} | {name} | 本地 | {description[:80]} |\n"

    if index_file.exists():
        content = index_file.read_text(encoding='utf-8')
        # 在第一个空行前插入
        if "|------|" in content:
            # 找到表头后的第一行数据
            lines = content.split("\n")
            inserted = False
            result = []
            in_table = False
            for i, line in enumerate(lines):
                result.append(line)
                if line.startswith("| ") and "------" in line:
                    in_table = True
                    continue
                if in_table and not inserted:
                    if not line.startswith("| "):
                        result.insert(len(result) - 1, new_entry.rstrip())
                        inserted = True
                        in_table = False
            if not inserted:
                result.append(new_entry.rstrip())
            index_file.write_text("\n".join(result), encoding='utf-8')
        else:
            # 无表格，追加
            with open(index_file, 'a', encoding='utf-8') as f:
                f.write(new_entry)
    else:
        # 创建新 INDEX.md
        index_file.write_text(f"""# 项目资源索引

> 由 Super Harness 自动维护。最后更新: {today}

| 日期 | 类型 | 名称 | 来源 | 摘要 |
|------|------|------|------|------|
{new_entry}
""", encoding='utf-8')


def record_mcp_usage(name: str, project_root: str = None):
    """记录 MCP 使用（更新 last_used 和 use_count）"""
    resources = _get_resources_dir(project_root)
    mcp_file = resources / "mcp" / f"{name}.json"
    if not mcp_file.exists():
        return
    try:
        cfg = json.loads(mcp_file.read_text(encoding='utf-8'))
        cfg["last_used"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cfg["use_count"] = cfg.get("use_count", 0) + 1
        mcp_file.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass


# ── 命令行入口 ──────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python mcp_proxy.py proxy <command> <tool> [args_json]")
        print("  python mcp_proxy.py install <name> <command>")
        print("  python mcp_proxy.py perm-install <name> <command> [args_json] [--desc ...] [--project ...]")
        print("  python mcp_proxy.py perm-skill <name> <desc> [--content ...] [--project ...]")
        print("  python mcp_proxy.py list [--project ...]")
        print("  python mcp_proxy.py cleanup")
        sys.exit(1)

    action = sys.argv[1]

    if action == "proxy":
        cmd = sys.argv[2]
        tool = sys.argv[3]
        args = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
        result = proxy_mcp_call(cmd, tool, args)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif action == "install":
        name = sys.argv[2]
        cmd = sys.argv[3]
        result = temp_install_mcp(name, cmd)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif action == "perm-install":
        name = sys.argv[2]
        cmd = sys.argv[3]
        args_json = sys.argv[4] if len(sys.argv) > 4 and not sys.argv[4].startswith("--") else "[]"
        args = json.loads(args_json) if args_json else []

        # 解析可选参数
        desc = ""
        project = None
        rest = sys.argv[4:]
        i = 0
        while i < len(rest):
            if rest[i] == "--desc" and i + 1 < len(rest):
                desc = rest[i + 1]
                i += 2
            elif rest[i] == "--project" and i + 1 < len(rest):
                project = rest[i + 1]
                i += 2
            else:
                i += 1

        result = perm_install_mcp(name, cmd, args, desc, project)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif action == "perm-skill":
        name = sys.argv[2]
        desc = sys.argv[3] if len(sys.argv) > 3 else ""

        content = ""
        project = None
        rest = sys.argv[4:] if len(sys.argv) > 4 else []
        i = 0
        while i < len(rest):
            if rest[i] == "--content" and i + 1 < len(rest):
                content = rest[i + 1]
                i += 2
            elif rest[i] == "--project" and i + 1 < len(rest):
                project = rest[i + 1]
                i += 2
            else:
                i += 1

        result = perm_install_skill(name, desc, content, project)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif action == "list":
        project = None
        rest = sys.argv[2:] if len(sys.argv) > 2 else []
        i = 0
        while i < len(rest):
            if rest[i] == "--project" and i + 1 < len(rest):
                project = rest[i + 1]
                i += 2
            else:
                i += 1

        mcps = list_project_mcps(project)
        skills = list_project_skills(project)
        print(json.dumps({"mcps": mcps, "skills": skills}, indent=2, ensure_ascii=False))

    elif action == "cleanup":
        result = cleanup_temp_mcps()
        print(json.dumps(result, indent=2, ensure_ascii=False))
