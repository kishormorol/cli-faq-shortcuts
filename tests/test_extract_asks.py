"""Run extract_asks.py against fake Claude Code and Codex history in a temp home.

CI runs this on Linux, macOS and Windows, so each OS's paths, drive letters and
encodings are exercised: python -m unittest discover tests
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "extract_asks.py"
sys.path.insert(0, str(SCRIPT.parent))
from extract_asks import slug  # noqa: E402

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

    @unittest.skipUnless(WINDOWS, "Windows path layout")
    def test_windows_slug(self):
        self.assertEqual(slug("C:\\Users\\me\\proj"), "C--Users-me-proj")


if __name__ == "__main__":
    unittest.main()
