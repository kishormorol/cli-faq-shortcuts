# Changelog

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
