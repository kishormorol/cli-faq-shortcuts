# v1.3.0 launch kit

Post in this order, a day or two apart, so each one can be measured on its own (see
Measurement in [the v1.2.0 kit](launch-v1.2.0.md#measurement)). Use the demo GIF and
MP4 from v1.2.0; they still match the workflow.

The secret-redaction numbers below come from the maintainer's own history. Post them only
after every credential they refer to has been rotated.

## 1. awesome-claude-code

Submit through the web form at <https://github.com/hesreallyhim/awesome-claude-code>
(not with `gh`); one open submission per person.

- Category: Skills
- Name: faq-shortcuts
- Link: https://github.com/kishormorol/cli-faq-shortcuts
- Description: Mines your own Claude Code, Codex and Cursor history for the asks you keep
  repeating and turns the top ones into project slash commands that point at your
  existing scripts. Pasted secrets are redacted before the agent reads the history.

## 2. Show HN

Never posted before (checked on HN Algolia, 2026-10-28), so this is a valid first
Show HN. Post on a weekday morning US time. Do not ask anyone to upvote.

Title: Show HN: Turn the prompts you keep retyping into slash commands

URL: https://github.com/kishormorol/cli-faq-shortcuts

First comment:

I kept typing variations of the same few questions to coding agents: "did the newsletter
actually go out?", "how many signed up this week, minus test accounts?". Each time the
agent started cold and sometimes made the same mistake again.

This is an Agent Skill for Claude Code, Codex and Cursor. A small standard-library Python
script reads the project's local session history; the agent groups the prompts by intent,
shows you how often you asked each one, and writes the ones you pick as short SKILL.md
commands. Each shortcut points at the script or query your project already uses and
records the mistakes already made on that path. Anything that writes or sends does a dry
run first.

On one of my projects the most repeated exact sentence appeared 14 times, but grouped by
intent the top ask had been typed 230 times.

When I ran the extractor across my own 42 projects, 49 prompts contained pasted API keys,
bot tokens or database URLs with passwords. v1.3.0 redacts those before the agent sees
anything. It's pattern-based, so a safety net rather than a guarantee.

Limits: history is matched to the exact project folder, Cursor's storage format is
undocumented, and only history still on your machine is read. Feedback on history formats
I'm missing is very welcome.

## 3. Reddit

Post to one subreddit per day, not all at once, and check each one's self-promotion
rules first. Good fits: r/ClaudeAI (pick its project-showcase flair), r/ClaudeCode,
r/cursor, r/codex.

Title: I found I'd asked my coding agent the same thing 230 times, so I made it a slash command

Body:

I noticed I was typing the same handful of requests to Claude Code every day, worded a
little differently each time. So I built a skill that reads your local session history
for a project (Claude Code, Codex and Cursor), groups what you asked by intent, and shows
you a table of proposed shortcuts, the ask each replaces, and how often you typed it. On
one of my projects the top ask had been typed 230 times; no single wording appeared more
than 14.

You pick which ones to keep, and each becomes a small SKILL.md in the project that points
at the script you already use, plus the traps you already hit ("delivered to a shared
inbox doesn't mean anyone read it").

New in v1.3.0: secrets you pasted into old prompts (API keys, DB URLs, bot tokens) are
redacted before the agent reads them. 49 of my own old prompts had one.

Install is one `git clone` (or `/plugin install` in Claude Code), and it's free and open
source (Apache-2.0): https://github.com/kishormorol/cli-faq-shortcuts

Curious what other people's most-repeated ask turns out to be.

## 4. X

I ran my coding-agent history through a script.

One question, typed 230 times in different words. Now it's a slash command.

faq-shortcuts finds your repeated asks in Claude Code, Codex & Cursor and turns them into
slash commands. v1.3.0 also redacts the API keys you pasted into old prompts.

https://github.com/kishormorol/cli-faq-shortcuts

## 5. LinkedIn

I asked my coding agent the same question 230 times without noticing.

Worded differently every time, so no single sentence repeated more than 14 times. Grouped
by intent, it was the most common thing I typed in that project.

faq-shortcuts is an open-source Agent Skill that reads your local Claude Code, Codex and
Cursor history, finds those repeated asks, and turns the ones you choose into short slash
commands, like /sent for "did the newsletter actually go out?". Each command uses the
tools your project already has and remembers the mistakes made last time.

v1.3.0 adds something I didn't expect to need: across my own projects, 49 old prompts
contained pasted API keys or database passwords. They are now redacted before the agent
reads anything.

What would your most repeated ask be?

https://github.com/kishormorol/cli-faq-shortcuts

#OpenSource #DeveloperTools #AIAgents #ClaudeCode
