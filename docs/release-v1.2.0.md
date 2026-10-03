Turn the requests you keep repeating into short commands for Claude Code, Codex, and Cursor.

This release brings together the community's Cursor and Windows support with clearer
setup, more resilient history extraction, and a 24-second walkthrough.

### What's new since v1.1.0

- **Cursor history:** extract chats associated with your project folder, alongside Claude Code and Codex (#4).
- **Windows without WSL:** install using a directory junction, with installation and extraction checked in CI (#1).
- **Claude Code plugin installation:** install from the repository's marketplace (#6).
- **JSONL export:** use `--format jsonl` for structured `date`, `source`, and `prompt` records.
- **More resilient extraction:** skip malformed record shapes, handle invalid timestamps, and continue with other sources when one cannot be read.
- **Clearer CLI errors:** validate dates, positive prompt-length limits, and project directories.
- **Contributor onboarding:** contribution guide, issue templates, troubleshooting, and privacy guidance.

### See the workflow

![Synthetic walkthrough](https://raw.githubusercontent.com/kishormorol/cli-faq-shortcuts/v1.2.0/docs/media/faq-shortcuts-demo.gif)

Download `faq-shortcuts-demo.mp4` below to watch or share the 24-second walkthrough.
All prompts, counts, and results in it are synthetic; this is an illustration, not a live recording.

### Update

```bash
git -C ~/.agents/skills/faq-shortcuts pull --ff-only
```

Then start a new agent session. See the [README](https://github.com/kishormorol/cli-faq-shortcuts#install)
for Windows and plugin installation.

TSV remains the default output. The extractor still uses only Python's standard library
and makes no network calls. Your agent performs intent grouping under its configured
model-provider settings.

Thanks to the contributors behind #1, #4, and #6, and everyone reporting setup issues.
Built and maintained with help from Claude Code and OpenAI Codex.

[Full changes](https://github.com/kishormorol/cli-faq-shortcuts/compare/v1.1.0...v1.2.0)
