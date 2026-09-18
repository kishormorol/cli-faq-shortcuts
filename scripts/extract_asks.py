#!/usr/bin/env python3
"""Print the prompts a user typed in past agent sessions for one project.

Two sources, read with --source (default: all):

  claude  Claude Code stores each session as JSONL under ~/.claude/projects/<slug>/,
          where <slug> is the project's absolute path with every non-alphanumeric
          character replaced by "-".
  codex   Codex stores each session as JSONL under $CODEX_HOME/sessions/YYYY/MM/DD/
          (CODEX_HOME defaults to ~/.codex). The first line, session_meta, records
          the cwd the session ran in; that is how a session is matched to a project.

Prints one typed prompt per line, oldest first, as "YYYY-MM-DD<TAB>source<TAB>prompt".

Skipped: tool results, subagent turns (Claude sidechains, Codex subagent threads),
non-interactive runs (codex exec, and Codex sessions driven by Claude Code, whose
prompts the agent wrote, not the user), meta turns, injected context and system
wrappers, and anything longer than --max-len (pasted documents, not asks).

Usage:
  extract_asks.py [project_dir] [--source all|claude|codex] [--since YYYY-MM-DD] [--max-len 400]
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

# Codex session sources a person types into. "exec" is a scripted run, and a dict
# source ({"subagent": ...}) is a thread another agent spawned.
CODEX_INTERACTIVE = {"cli", "vscode"}
# Another agent driving Codex (e.g. a Claude Code plugin): its prompts are not the user's.
CODEX_AGENT_ORIGINATORS = {"Claude Code"}


def slug(path: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(path))


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


def read_jsonl(path):
    with open(path, errors="ignore") as fh:
        for line in fh:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def claude_asks(project_dir):
    sessions = Path.home() / ".claude" / "projects" / slug(project_dir)
    if not sessions.is_dir():
        return None, sessions
    asks = []
    for f in sessions.glob("*.jsonl"):
        for turn in read_jsonl(f):
            if turn.get("type") != "user" or turn.get("isMeta") or turn.get("isSidechain"):
                continue
            text = prompt_text(turn.get("message", {}).get("content")).strip()
            asks.append((turn.get("timestamp", "")[:10], text))
    return asks, sessions


def codex_asks(project_dir):
    root = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions"
    if not root.is_dir():
        return None, root
    project = os.path.abspath(project_dir)
    asks, matched = [], 0
    for f in root.rglob("*.jsonl"):
        turns = read_jsonl(f)
        meta = next(turns, {})
        info = meta.get("payload") or {}
        source = info.get("source")
        if (
            meta.get("type") != "session_meta"
            or not info.get("cwd")
            or os.path.abspath(info["cwd"]) != project
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


SOURCES = {"claude": claude_asks, "codex": codex_asks}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir", nargs="?", default=os.getcwd())
    ap.add_argument("--source", choices=["all", *SOURCES], default="all")
    ap.add_argument("--since", default="")
    ap.add_argument("--max-len", type=int, default=400)
    args = ap.parse_args()

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
