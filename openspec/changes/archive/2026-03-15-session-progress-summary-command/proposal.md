## Why

`superspec git commit` already appends structured commit records into the root `progress.md`, but the repository still lacks a first-class way to close out the current session and turn those raw commit entries into a readable session summary. Without that command, users must manually scan the current-session ledger, manually deduplicate changes and files, and manually reset the session area before the next work block.

## What Changes

- Add a new `superspec progress` command that reads all commit entries from the `current-session` block in `progress.md` and generates one Markdown session summary.
- Write the generated session summary back into `progress.md`, including a dated `Session x` heading, finish timestamp, deduplicated change list, deduplicated file list, and the final next-step note.
- Clear the `current-session` section after a successful summary write so the next session starts from an empty ledger.
- Evolve session progress parsing rules so commit details may be absent or blank without forcing empty detail bullets into the summary, and allow `superspec git commit` to omit `--details`.

## Capabilities

### New Capabilities
- `session-progress-summary`: Summarize the current-session commit ledger into a stable Markdown session summary through a dedicated CLI command.

### Modified Capabilities
- `session-progress-memory`: Extend `progress.md` handling so current-session entries can be consumed, summarized, and cleared after summarization, while tolerating empty commit details.

## Impact

- Affected code: `src/superspec/cli.py`, `src/superspec/engine/scm/progress_file.py`, and new summarization logic under `src/superspec/engine/scm/`
- Affected specs: `openspec/specs/session-progress-memory/spec.md` plus a new `openspec/specs/session-progress-summary/spec.md`
- Tests: new unit coverage for progress parsing/summarization and CLI behavior
