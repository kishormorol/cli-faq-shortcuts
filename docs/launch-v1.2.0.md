# v1.2.0 launch kit

## Assets

- `media/faq-shortcuts-demo.gif`: looping 24-second README walkthrough.
- `media/faq-shortcuts-demo.png`: static preview.
- [MP4 download](https://github.com/kishormorol/cli-faq-shortcuts/releases/download/v1.2.0/faq-shortcuts-demo.mp4): 1280 x 720, 24 seconds, silent with on-screen text.

All prompts, counts, and results in the demo are invented. It illustrates the agent
workflow; it is not a live recording or a performance benchmark.

To rebuild, install `Pillow` and `imageio-ffmpeg` in a separate environment, then run
`python scripts/render_demo.py --output-dir <output-folder>`. These are optional media
build dependencies, not extractor dependencies.

## LinkedIn

Keep typing the same long requests to your coding agent?

I built cli-faq-shortcuts to turn recurring asks into reusable slash commands.

It reads project history from Claude Code, Codex, and Cursor. Your agent groups the asks
by intent, proposes shortcuts, and creates the ones you choose using tools your project
already has.

Example: "Did the newsletter actually go out?" becomes /sent.

v1.2.0 brings Cursor history support, native Windows setup, a Claude Code plugin install,
JSONL export, and more resilient history parsing.

The Python extractor runs locally with no extra dependencies. Your coding agent handles
the grouping, so its model-provider settings still apply.

The 24-second demo uses synthetic examples. What request would you turn into a shortcut?

https://github.com/kishormorol/cli-faq-shortcuts

If it saves you typing, a GitHub star helps others discover it.

#OpenSource #DeveloperTools #AIAgents

## X

Keep repeating prompts to your coding agent?

cli-faq-shortcuts turns recurring asks into slash commands using Claude Code, Codex & Cursor history.

v1.2.0 is out. Synthetic demo below.
What would you shorten?

https://github.com/kishormorol/cli-faq-shortcuts

## Show HN draft

Title: Show HN: Turn repeated coding-agent prompts into project shortcuts

URL: https://github.com/kishormorol/cli-faq-shortcuts

Suggested introductory comment:

I built this because I kept typing variations of the same project questions to coding
agents. The extractor reads local Claude Code, Codex, and Cursor history for a project;
the agent groups requests by intent and proposes small SKILL.md shortcuts. You choose
which ones to create. They point to existing project tools rather than inventing new ones.

The extractor is standard-library Python and makes no network calls. Grouping happens
in your configured agent, so that part follows its model-provider settings. The repo has
installation commands and a short demo with synthetic data.

Limitations: history is matched to the exact folder; long prompts are filtered by default;
Cursor's undocumented storage can change. I'd welcome feedback on missing history
formats and whether the suggested shortcuts capture the tasks you actually repeat.

Before posting, check for an earlier submission of this project and follow
[Show HN guidelines](https://news.ycombinator.com/showhn.html). An ordinary version update
is generally not a new Show HN. Do not ask others to upvote.

## Measurement

Run `python scripts/collect_traffic.py` with an authenticated GitHub CLI that has push
access. It saves raw snapshots and `summary.csv` under
`~/.local/share/cli-faq-shortcuts/traffic/`, outside the public checkout.

Capture weekly, and record each post URL and publication time in a private launch log.
Compare changes in total stars and daily visitor/clone data around each post. GitHub
traffic provides a rolling window; never add overlapping unique counts. Clones can
include automated activity and are not a direct count of active users. GitHub does not
attribute an individual star to a referring channel.

[GitHub traffic documentation](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-traffic-to-a-repository)
