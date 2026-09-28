"""Run extract_asks.py against synthetic Claude Code, Codex and Cursor history.

CI runs this on Linux, macOS and Windows, so each OS's paths, drive letters and
encodings are exercised: python -m unittest discover tests
"""
import json
import io
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "extract_asks.py"
sys.path.insert(0, str(SCRIPT.parent))
from extract_asks import slug  # noqa: E402
import extract_asks  # noqa: E402

WINDOWS = sys.platform == "win32"
# Read or printed as cp1252 (the Windows default), "à" turns into a no-break space that the
# whitespace cleanup splits on, and the 0x9D byte in "Н" is dropped.
ASK = "voilà, Нет ✓ 日本語"


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def spelled_differently(project):
    """The same folder as another tool on Windows may record it: other drive-letter
    case, forward slashes, and the \\\\?\\ prefix of a canonicalized path."""
    if not WINDOWS:
        return project
    return "\\\\?\\" + (project[0].swapcase() + project[1:]).replace("\\", "/")


class ExtractAsks(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name) / "home"
        self.project = os.path.abspath(Path(tmp.name) / "my proj")
        os.makedirs(self.project)
        self.env = dict(
            os.environ,
            HOME=str(self.home),
            USERPROFILE=str(self.home),  # Path.home() on Windows
            CODEX_HOME=str(self.home / ".codex"),
            APPDATA=str(self.home / "AppData" / "Roaming"),
            XDG_CONFIG_HOME=str(self.home / ".config"),
        )
        for var in ("PYTHONIOENCODING", "PYTHONUTF8"):  # the script must pick UTF-8 itself
            self.env.pop(var, None)

    def run_script(self, *args):
        out = subprocess.run(
            [sys.executable, str(SCRIPT), self.project, *args],
            env=self.env,
            capture_output=True,
        )
        self.assertEqual(out.returncode, 0, out.stderr.decode("utf-8", "replace"))
        rows = out.stdout.decode("utf-8").splitlines()
        return [row.split("\t") for row in rows]

    def test_claude_transcript(self):
        write_jsonl(
            self.home / ".claude" / "projects" / slug(self.project) / "s1.jsonl",
            [
                {"type": "user", "sessionId": "s1", "timestamp": "2026-09-01T10:00:00Z",
                 "message": {"content": ASK}},
                {"type": "user", "sessionId": "s1", "isSidechain": True,
                 "timestamp": "2026-09-01T10:01:00Z", "message": {"content": "subagent turn"}},
            ],
        )
        self.assertEqual(self.run_script("--source", "claude"), [["2026-09-01", "claude", ASK]])

    def test_claude_history_log(self):
        write_jsonl(
            self.home / ".claude" / "history.jsonl",
            [
                {"display": ASK, "project": spelled_differently(self.project),
                 "sessionId": "old", "timestamp": 1756720800000},
                {"display": "no project recorded", "sessionId": "x", "timestamp": 1756720800000},
            ],
        )
        self.assertEqual(self.run_script("--source", "claude"), [["2025-09-01", "claude", ASK]])

    def test_codex_session(self):
        write_jsonl(
            self.home / ".codex" / "sessions" / "2026" / "09" / "02" / "rollout.jsonl",
            [
                {"type": "session_meta",
                 "payload": {"cwd": spelled_differently(self.project), "source": "cli"}},
                {"type": "response_item", "timestamp": "2026-09-02T09:00:00Z",
                 "payload": {"role": "user", "content": [{"type": "input_text", "text": ASK}]}},
            ],
        )
        write_jsonl(
            self.home / ".codex" / "sessions" / "2026" / "09" / "02" / "exec.jsonl",
            [
                {"type": "session_meta", "payload": {"cwd": self.project, "source": "exec"}},
                {"type": "response_item", "timestamp": "2026-09-02T09:05:00Z",
                 "payload": {"role": "user", "content": [{"type": "input_text", "text": "scripted"}]}},
            ],
        )
        self.assertEqual(self.run_script("--source", "codex"), [["2026-09-02", "codex", ASK]])

    def cursor_db(self, conversations):
        """A fake Cursor state.vscdb: {composer data: [bubbles]}, keyed in insertion order."""
        if sys.platform == "darwin":
            base = self.home / "Library" / "Application Support"
        else:
            base = self.home / ("AppData/Roaming" if WINDOWS else ".config")
            self.env["APPDATA" if WINDOWS else "XDG_CONFIG_HOME"] = str(base)
        db = base / "Cursor" / "User" / "globalStorage" / "state.vscdb"
        db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE cursorDiskKV (key TEXT PRIMARY KEY, value BLOB)")
        for i, (composer, bubbles) in enumerate(conversations):
            conn.execute(
                "INSERT INTO cursorDiskKV VALUES (?, ?)", (f"composerData:c{i}", json.dumps(composer))
            )
            for j, bubble in enumerate(bubbles):
                conn.execute(
                    "INSERT INTO cursorDiskKV VALUES (?, ?)",
                    (f"bubbleId:c{i}:b{j}", json.dumps(bubble, ensure_ascii=False)),
                )
        conn.commit()
        conn.close()

    def test_cursor_history(self):
        workspace = {"workspaceIdentifier": {"uri": {"fsPath": spelled_differently(self.project)}}}
        self.cursor_db(
            [
                (
                    workspace,
                    [
                        {"type": 1, "createdAt": "2026-09-03T10:00:00.000Z", "text": ASK},
                        {"type": 2, "createdAt": "2026-09-03T10:01:00.000Z", "text": "reply"},
                    ],
                ),
                (
                    {"workspaceIdentifier": {"uri": {"fsPath": self.project + "-other"}}},
                    [{"type": 1, "text": "another project"}],
                ),
            ]
        )
        self.assertEqual(self.run_script("--source", "cursor"), [["2026-09-03", "cursor", ASK]])

    def test_cursor_epoch_and_repo_fallback(self):
        # Current Cursor stores epoch milliseconds; older bubbles have no createdAt at all,
        # and a conversation without a workspace names its folder in trackedGitRepos.
        self.cursor_db(
            [
                (
                    {"createdAt": 1788000000000, "trackedGitRepos": [{"repoPath": self.project}]},
                    [
                        {"type": 1, "createdAt": 1788500000000, "text": "timed"},
                        {"type": 1, "text": "untimed"},
                    ],
                )
            ]
        )
        self.assertEqual(
            self.run_script("--source", "cursor"),
            [["2026-08-29", "cursor", "untimed"], ["2026-09-04", "cursor", "timed"]],
        )

    def test_malformed_records_do_not_hide_valid_prompts(self):
        transcript = self.home / ".claude" / "projects" / slug(self.project) / "s1.jsonl"
        write_jsonl(transcript, [
            None, [], "not an object",
            {"type": "user", "message": None, "timestamp": None, "sessionId": []},
            {"type": "user", "message": {"content": [{"type": "text", "text": {}}]}},
            {"type": "user", "timestamp": "2026-09-01T10:00:00Z", "message": {"content": ASK}},
        ])
        with transcript.open("a", encoding="utf-8") as fh:
            fh.write('{"unfinished":')
        self.assertEqual(self.run_script("--source", "claude"), [["2026-09-01", "claude", ASK]])

    def test_malformed_codex_payloads(self):
        root = self.home / ".codex" / "sessions"
        write_jsonl(root / "bad.jsonl", [{"type": "session_meta", "payload": []}])
        write_jsonl(root / "good.jsonl", [
            {"type": "session_meta", "payload": {"cwd": self.project, "source": "vscode"}},
            {"type": "response_item", "payload": "invalid"},
            {"type": "response_item", "timestamp": "2026-09-02", "payload": {
                "role": "user", "content": [{"type": "input_text", "text": ASK}]}},
        ])
        self.assertEqual(self.run_script("--source", "codex"), [["2026-09-02", "codex", ASK]])

    def test_cursor_malformed_records_and_timestamps(self):
        self.cursor_db([
            (None, []),
            ({"workspaceIdentifier": "invalid", "trackedGitRepos": 42}, []),
            ({"createdAt": 10**100, "trackedGitRepos": [{"repoPath": self.project}]}, [
                None, [], {"type": 1, "text": []},
                {"type": 1, "createdAt": 10**100, "text": ASK},
            ]),
        ])
        self.assertEqual(self.run_script("--source", "cursor"), [["", "cursor", ASK]])
        self.assertEqual(self.run_script("--source", "cursor", "--since", "2026-01-01"), [])

    def test_filters_and_history_deduplication(self):
        write_jsonl(self.home / ".claude" / "projects" / slug(self.project) / "s1.jsonl", [
            {"type": "user", "timestamp": "2026-09-01", "message": {"content": "older"}},
            {"type": "user", "timestamp": "2026-09-02", "message": {"content": "keep\tthis\nask"}},
            {"type": "user", "timestamp": "2026-09-02", "message": {"content": "x" * 401}},
            {"type": "user", "timestamp": "2026-09-02", "message": {"content": "<system>context"}},
        ])
        write_jsonl(self.home / ".claude" / "history.jsonl", [
            {"project": self.project, "sessionId": "s1", "display": "duplicate"},
            {"project": self.project, "sessionId": "old", "display": "/help"},
        ])
        self.assertEqual(self.run_script("--source", "claude", "--since", "2026-09-02"),
                         [["2026-09-02", "claude", "keep this ask"]])

    def test_jsonl_output_keeps_unicode_and_metadata(self):
        write_jsonl(self.home / ".claude" / "history.jsonl", [
            {"project": self.project, "display": ASK, "timestamp": 1756720800000},
        ])
        rows = self.run_script("--source", "claude", "--format", "jsonl")
        self.assertEqual([json.loads(row[0]) for row in rows],
                         [{"date": "2025-09-01", "source": "claude", "prompt": ASK}])

    def test_invalid_arguments(self):
        for args in [("--since", "yesterday"), ("--since", "2026-02-30"),
                     ("--since", "20260901"), ("--max-len", "0"), ("--max-len", "-1"),
                     ("--max-len", "many"), ("--format", "xml")]:
            with self.subTest(args=args):
                out = subprocess.run([sys.executable, str(SCRIPT), self.project, *args],
                                     env=self.env, capture_output=True)
                self.assertEqual(out.returncode, 2)
                self.assertEqual(out.stdout, b"")
                self.assertNotIn(b"Traceback", out.stderr)

    def test_missing_project(self):
        out = subprocess.run([sys.executable, str(SCRIPT), str(self.home / "missing")],
                             env=self.env, capture_output=True)
        self.assertEqual(out.returncode, 2)
        self.assertIn(b"existing directory", out.stderr)

    def test_no_history(self):
        out = subprocess.run([sys.executable, str(SCRIPT), self.project],
                             env=self.env, capture_output=True)
        self.assertEqual(out.returncode, 1)
        self.assertEqual(out.stdout, b"")
        self.assertIn(b"no session history", out.stderr)
        self.assertNotIn(b"Traceback", out.stderr)

    def test_unreadable_source_does_not_block_another_source(self):
        def unreadable(_):
            raise PermissionError(13, "Permission denied")

        sources = {"claude": unreadable, "codex": lambda _: ([("2026-09-01", ASK)], "synthetic")}
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(extract_asks, "SOURCES", sources), \
                patch.object(sys, "argv", [str(SCRIPT), self.project]), \
                patch.object(sys, "platform", "linux"), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            extract_asks.main()
        self.assertEqual(stdout.getvalue(), f"2026-09-01\tcodex\t{ASK}\n")
        self.assertIn("claude: could not read session history", stderr.getvalue())

    @unittest.skipUnless(WINDOWS, "Windows path layout")
    def test_windows_slug(self):
        self.assertEqual(slug("C:\\Users\\me\\proj"), "C--Users-me-proj")


if __name__ == "__main__":
    unittest.main()
