# Changelog

## Unreleased

### Changed

- The demo GIF and PNG are served from the v1.2.0 tag instead of being shipped in the
  plugin, and `render_demo.py` no longer writes into the repository by default.
- Tests run the extractor with a minimal environment instead of a copy of the developer's.

## v1.3.1

### Changed

- A first run with no history for the folder now says what to do (run it from the folder
  you worked in, or come back after a few sessions) instead of only listing missing paths.
- Fewer than 20 prompts prints a note on stderr that there is too little history to show
  repeats; the skill then proposes at most one or two shortcuts and never invents asks.
- The Claude Code plugin has a version and an icon, so it can be listed in the plugin directory.

## v1.3.0

### Added

- Secrets pasted into prompts (API keys, tokens, passwords, credentials in URLs, webhooks)
  are replaced with `[REDACTED]` before printing, since the list goes to a model.
  `--no-redact` keeps them.
- `--min-words N` skips short replies such as "ok" and "yes". The skill uses `3`, which on
  a heavily used project cut 4,607 prompts to 3,367.

### Changed

- The skill calls the extractor by its own folder, so it no longer depends on the agent
  guessing that `scripts/` is relative to the skill, not the user's project.
- The skill trims large histories with `--since` or reads them in chunks instead of
  loading thousands of prompts at once.

## v1.2.0

### Added

- Cursor chat history extraction, native Windows installation, and Claude Code plugin installation.
- A 24-second synthetic walkthrough, with GIF and downloadable MP4 versions.
- A maintainer traffic snapshot script that stores analytics outside the checkout.
- Optional `--format jsonl` output with `date`, `source`, and `prompt` fields.
- CLI option reference, filtering limits, contributor guide, and GitHub issue/PR templates.
- Regression coverage for malformed history, filtering, deduplication, Unicode JSONL,
  invalid arguments, and missing history.

### Fixed

- Non-object JSON records, unexpected payload types, and out-of-range timestamps no
  longer crash supported history readers.
- Invalid dates, non-positive prompt limits, and missing project directories produce
  actionable CLI errors.
- An unreadable history source no longer prevents other available sources from running.
- Tests isolate Cursor profile paths from the developer's environment.
- The README now reflects existing Windows support and explains agent privacy boundaries.
