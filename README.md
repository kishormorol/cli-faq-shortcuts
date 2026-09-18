# cli-faq-shortcuts

An [Agent Skill](https://agentskills.io) that reads what you keep typing to your coding
agent and turns it into short commands — for **Claude Code, Codex and Cursor**.

![An agent reads a project's past prompts and proposes four shortcuts, each with the sentence it replaces and how often it was asked (illustrative example)](demo.svg)

When a codebase gets big, every ask gets long. "Check whether the new signups got their
welcome email, and skip the test accounts like last time" — typed again every day, with a
typo one day, and the agent starts cold every time. This skill finds those asks in your
own history and makes each one a shortcut:

| You kept typing | You type now |
|---|---|
| "how many people signed up this week, not counting test accounts?" | `/signups` |
| "did the newsletter actually go out? did it reach everyone?" | `/sent` |
| "any update on the billing migration? what's blocked?" | `/project billing` |
| "add this CSV of new customers, skip the ones we already have" | `/import new.csv` |

The shortcuts are yours, not generic: each one points at the script or query your
project already uses, and records the mistakes already made on that path — so a short
command also stops being a way to repeat an old error.

## How it works

1. **Collect** — `scripts/extract_asks.py` prints every prompt you typed in one project,
   from Claude Code and Codex history. Subagent turns and scripted runs are skipped,
   because you didn't type those.
2. **Cluster** — the agent groups prompts by intent, whatever the wording, and counts them.
3. **Check** — it looks for shortcuts you already have and the tools your project already has.
4. **Propose** — you get a table: shortcut, the ask it replaces, how often you asked. You pick.
5. **Write** — each shortcut is a small `SKILL.md` in your project. Anything that writes or
   sends does a dry run first and waits for your yes, so a typo ends at the preview.
6. **List** — a table in `CLAUDE.md` / `AGENTS.md` maps each shortcut to the sentence it replaces.

## Install

Clone once, then link it so every agent finds it:

```bash
git clone https://github.com/kishormorol/cli-faq-shortcuts ~/.agents/skills/faq-shortcuts
mkdir -p ~/.claude/skills && ln -s ~/.agents/skills/faq-shortcuts ~/.claude/skills/faq-shortcuts
```

| Agent | Reads skills from |
|---|---|
| Codex | `~/.agents/skills/` |
| Claude Code | `~/.claude/skills/` (the link) |
| Cursor | both |

Then, inside a project, ask *"what do I keep asking in this project?"* — or in Claude Code,
type `/faq-shortcuts`.

The shortcuts it writes live in the project's `.claude/skills/`, linked into
`.agents/skills/`, so they load in all three agents and travel with the repo.

## What it reads

| Agent | History | Read? |
|---|---|---|
| Claude Code | `~/.claude/projects/<project>/*.jsonl` | yes |
| Codex | `~/.codex/sessions/` (or `$CODEX_HOME`), matched by the session's working directory | yes |
| Cursor | an undocumented SQLite store | not yet — Cursor still loads the shortcuts |

Run the extractor on its own to see what it finds:

```bash
python3 ~/.agents/skills/faq-shortcuts/scripts/extract_asks.py . --since 2026-01-01 | head
```

Prints `date<TAB>source<TAB>prompt`. Use `--source claude` or `--source codex` to read one.

## Privacy

The extractor reads local files and makes no network calls. Your prompts can contain
names, emails and tokens, so the skill writes them to a scratch location, never into the
repo. The agent reads that list the way it reads any file you show it.

## License

Apache-2.0. Python 3.9+ and nothing else.
