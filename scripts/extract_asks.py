#!/usr/bin/env python3
"""Print the prompts a user typed in past agent sessions for one project.

Three sources, read with --source (default: all):

  claude  Claude Code stores each session as JSONL under ~/.claude/projects/<slug>/,
          where <slug> is the project's absolute path with every non-alphanumeric
          character replaced by "-" (C:\\Users\\me\\proj becomes C--Users-me-proj).
          Those transcripts are pruned after 30 days by default, so older sessions
          come from ~/.claude/history.jsonl, the prompt log behind the up-arrow, which
          keeps the typed text, project and session id. A session is read from its
          transcript when one survives, else from that log, so no prompt is counted
          twice.
  codex   Codex stores each session as JSONL under $CODEX_HOME/sessions/YYYY/MM/DD/
          (CODEX_HOME defaults to ~/.codex). The first line, session_meta, records
          the cwd the session ran in; that is how a session is matched to a project.
  cursor  Cursor keeps chats in an undocumented SQLite store, state.vscdb under its
          globalStorage folder, in the table cursorDiskKV. Each composerData:<id> row is
          one conversation, matched to a project by workspaceIdentifier or, failing that,
          trackedGitRepos. Its turns are bubbleId:<id>:<bubble> rows; type 1 is the user.
          Timestamps are epoch milliseconds, and older bubbles carry none, so the
          conversation's own createdAt stands in.

Prints one typed prompt per line, oldest first, as "YYYY-MM-DD<TAB>source<TAB>prompt".

Skipped: tool results, subagent turns (Claude sidechains, Codex subagent threads),
non-interactive runs (codex exec, and Codex sessions driven by Claude Code, whose
prompts the agent wrote, not the user), meta turns, injected context and system
wrappers, and anything longer than --max-len (pasted documents, not asks).

Usage:
  extract_asks.py [project_dir] [--source all|claude|codex|cursor] [--since YYYY-MM-DD] [--max-len 400]
"""
import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# Codex session sources a person types into. "exec" is a scripted run, and a dict
# source ({"subagent": ...}) is a thread another agent spawned.
CODEX_INTERACTIVE = {"cli", "vscode"}
# Another agent driving Codex (e.g. a Claude Code plugin): its prompts are not the user's.
CODEX_AGENT_ORIGINATORS = {"Claude Code"}


def slug(path: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(path))


def norm_path(path: str) -> str:
    """Fold the ways a tool may record the same folder into one string. On Windows that
    means drive-letter case, / vs \\, and the \\\\?\\ prefix a canonicalized path carries."""
    if path.startswith("\\\\?\\"):
        path = path[4:]
    return os.path.normcase(os.path.abspath(path))


def prompt_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") in ("text", "input_text")
        )
    return ""


def is_wrapper(text: str) -> bool:
    return text.startswith(("<", "[Request", "# AGENTS.md instructions"))


# history.jsonl records slash commands and ! shell input as typed; transcripts wrap them in
# tags that is_wrapper() already drops. A path such as /Users/me/cv.pdf is still an ask.
SLASH_OR_SHELL = re.compile(r"^(/[A-Za-z0-9:_-]+(\s|$)|!)")
PASTE_ONLY = re.compile(r"^\[Pasted text #\d+[^\]]*\]$")


def read_jsonl(path):
    with open(path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def claude_asks(project_dir):
    home = Path.home() / ".claude"
    sessions = home / "projects" / slug(project_dir)
    history = home / "history.jsonl"
    if not sessions.is_dir() and not history.is_file():
        return None, sessions
    asks, seen = [], set()
    for f in sessions.glob("*.jsonl") if sessions.is_dir() else []:
        seen.add(f.stem)
        for turn in read_jsonl(f):
            if turn.get("type") != "user" or turn.get("isMeta") or turn.get("isSidechain"):
                continue
            seen.add(turn.get("sessionId"))
            text = prompt_text(turn.get("message", {}).get("content")).strip()
            asks.append((turn.get("timestamp", "")[:10], text))
    project = norm_path(project_dir)
    for entry in read_jsonl(history) if history.is_file() else []:
        where = entry.get("project")
        if not where or norm_path(where) != project or entry.get("sessionId") in seen:
            continue
        text = (entry.get("display") or "").strip()
        if SLASH_OR_SHELL.match(text) or PASTE_ONLY.match(text):
            continue
        ts = entry.get("timestamp")
        day = datetime.fromtimestamp(ts / 1000, timezone.utc).strftime("%Y-%m-%d") if ts else ""
        asks.append((day, text))
    if not asks and not sessions.is_dir():
        return None, sessions
    return asks, f"{sessions} + {history}"


def codex_asks(project_dir):
    root = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions"
    if not root.is_dir():
        return None, root
    project = norm_path(project_dir)
    asks, matched = [], 0
    for f in root.rglob("*.jsonl"):
        turns = read_jsonl(f)
        meta = next(turns, {})
        info = meta.get("payload") or {}
        source = info.get("source")
        if (
            meta.get("type") != "session_meta"
            or not info.get("cwd")
            or norm_path(info["cwd"]) != project
            or not isinstance(source, str)
            or source not in CODEX_INTERACTIVE
            or info.get("originator") in CODEX_AGENT_ORIGINATORS
        ):
            continue
        matched += 1
        for turn in turns:
            item = turn.get("payload") or {}
            if turn.get("type") != "response_item" or item.get("role") != "user":
                continue
            text = prompt_text(item.get("content")).strip()
            asks.append((turn.get("timestamp", "")[:10], text))
    if not matched:
        return None, f"{root} (no interactive session ran in {project})"
    return asks, root


def cursor_db_path():
    if sys.platform == "darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "Cursor"
            / "User"
            / "globalStorage"
            / "state.vscdb"
        )
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Cursor" / "User" / "globalStorage" / "state.vscdb"
        return (
            Path.home()
            / "AppData"
            / "Roaming"
            / "Cursor"
            / "User"
            / "globalStorage"
            / "state.vscdb"
        )
    config = os.environ.get("XDG_CONFIG_HOME")
    base = Path(config) if config else Path.home() / ".config"
    return base / "Cursor" / "User" / "globalStorage" / "state.vscdb"


def cursor_day(ts):
    """A Cursor timestamp as YYYY-MM-DD: epoch milliseconds, or ISO text in older data."""
    if isinstance(ts, (int, float)) and not isinstance(ts, bool):
        return datetime.fromtimestamp(ts / 1000, timezone.utc).strftime("%Y-%m-%d")
    return ts[:10] if isinstance(ts, str) else ""


def cursor_project(data):
    """The folders a Cursor conversation ran in: its workspace, else its tracked repos."""
    uri = (data.get("workspaceIdentifier") or {}).get("uri") or {}
    if uri.get("fsPath"):
        return [uri["fsPath"]]
    repos = data.get("trackedGitRepos") or []
    return [r["repoPath"] for r in repos if isinstance(r, dict) and r.get("repoPath")]


def cursor_asks(project_dir):
    db = cursor_db_path()
    if not db.is_file():
        return None, db
    project = norm_path(project_dir)
    try:
        # Read-only, so a running Cursor holding the database is no obstacle.
        conn = sqlite3.connect(f"{db.as_uri()}?mode=ro", uri=True)
    except sqlite3.Error:
        return None, db
    try:
        started = {}
        for key, value in conn.execute(
            "SELECT key, value FROM cursorDiskKV WHERE key LIKE 'composerData:%'"
        ):
            try:
                data = json.loads(value)
            except (TypeError, json.JSONDecodeError):
                continue
            if any(norm_path(p) == project for p in cursor_project(data)):
                started[key.split(":", 1)[1]] = cursor_day(data.get("createdAt"))
        if not started:
            return None, f"{db} (no conversation ran in {project_dir})"
        asks = []
        for composer_id, day in started.items():
            for (value,) in conn.execute(
                "SELECT value FROM cursorDiskKV WHERE key LIKE ?", (f"bubbleId:{composer_id}:%",)
            ):
                try:
                    bubble = json.loads(value)
                except (TypeError, json.JSONDecodeError):
                    continue
                if bubble.get("type") != 1:
                    continue
                text = (bubble.get("text") or "").strip()
                asks.append((cursor_day(bubble.get("createdAt")) or day, text))
    except sqlite3.Error:
        return None, db
    finally:
        conn.close()
    return asks, db


SOURCES = {"claude": claude_asks, "codex": codex_asks, "cursor": cursor_asks}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir", nargs="?", default=os.getcwd())
    ap.add_argument("--source", choices=["all", *SOURCES], default="all")
    ap.add_argument("--since", default="")
    ap.add_argument("--max-len", type=int, default=400)
    args = ap.parse_args()
    if sys.platform == "win32":
        # A pipe on Windows defaults to the ANSI code page, which can't print most prompts.
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    names = list(SOURCES) if args.source == "all" else [args.source]
    rows, missing = [], []
    for name in names:
        asks, where = SOURCES[name](args.project_dir)
        if asks is None:
            missing.append(f"{name}: no session history at {where}")
            continue
        kept = 0
        for day, text in asks:
            if not text or is_wrapper(text) or len(text) > args.max_len or day < args.since:
                continue
            rows.append((day, name, " ".join(text.split())))
            kept += 1
        print(f"{kept} prompts from {name} ({where})", file=sys.stderr)

    if len(missing) == len(names):
        sys.exit("\n".join(missing))
    for note in missing:
        print(note, file=sys.stderr)

    rows.sort()
    for day, name, text in rows:
        print(f"{day}\t{name}\t{text}")


if __name__ == "__main__":
    main()
