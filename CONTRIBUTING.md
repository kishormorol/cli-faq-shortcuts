# Contributing

Thanks for helping make repeated requests easier to reuse. Small, focused pull requests
are welcome, especially history compatibility fixes and clearer setup instructions.

## Development

You need Git and Python 3.9 or newer. The extractor and tests use only the standard library.

```bash
git clone https://github.com/kishormorol/cli-faq-shortcuts.git
cd cli-faq-shortcuts
python -m unittest discover tests -v
python scripts/extract_asks.py --help
```

Use `python3` if that is your Python command. CI runs the suite on Linux, macOS, and
Windows, and checks the Windows junction installation separately.

## Changes and tests

- Keep extraction local and read-only. Do not add network calls or runtime dependencies.
- Preserve the default TSV interface; put diagnostics on stderr.
- For parser fixes, add the smallest synthetic history record that reproduces the bug
  to `tests/test_extract_asks.py`. Cover unrelated projects and non-user turns when relevant.
- Use temporary directories and an isolated profile. Tests must never read your real history.
- Document changed behavior in the README and the Unreleased section of `CHANGELOG.md`.
- Describe the problem, resulting behavior, and tests run in your pull request.

## Reporting bugs

Include your OS, Python version (`python --version`), agent version, the command with
private paths replaced, and a sanitized error message. For missing prompts, mention the
source and whether the session ran in a different folder or worktree.

Never upload a real session transcript, `history.jsonl`, `state.vscdb`, or an extracted
prompt list. Replace prompts with invented examples and remove credentials, names,
email addresses, repository paths, and internal URLs. A tiny synthetic record is enough
to explain most parser issues.

## Project layout

| Path | Purpose |
|---|---|
| `SKILL.md` | Instructions the coding agent follows to propose and create shortcuts. |
| `scripts/extract_asks.py` | Local history readers and command-line interface. |
| `tests/test_extract_asks.py` | Synthetic history fixtures and CLI regression tests. |
| `.claude-plugin/` | Claude Code plugin and marketplace metadata. |
| `.github/workflows/test.yml` | Cross-platform checks. |
