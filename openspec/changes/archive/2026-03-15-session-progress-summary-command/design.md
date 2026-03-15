## Context

The repository already uses `progress.md` as a marker-delimited ledger of raw commit entries for the active session. `superspec git commit` appends one normalized Markdown entry per successful commit, but no command currently consumes that ledger, produces a human-readable session closeout, or resets the current-session region afterwards.

This change crosses both CLI wiring and the progress file helper layer. It also changes how `progress.md` is interpreted: the file will now contain both an append-only history of completed session summaries and a transient `current-session` block for in-flight commits.

## Goals / Non-Goals

**Goals:**
- Add a dedicated `superspec progress` command that summarizes the current-session ledger into one Markdown session block.
- Reuse the existing normalized commit entry format instead of introducing a second source of truth.
- Keep the generated session summary deterministic and rule-based, with no external dependency or LLM requirement.
- Preserve `progress.md` as the single Markdown artifact for both open-session commits and completed session summaries.
- Support blank commit details by omitting empty detail bullets in the generated summary.

**Non-Goals:**
- Do not archive or rotate session summaries into separate files.
- Do not infer semantic groupings beyond the requested sections (`Done`, `Changes`, `Files`, `Next`, `Finish`).
- Do not alter execution state or event logging as part of the summarization command.

## Decisions

### Decision: Introduce a progress summarization service in the SCM layer

The new command should delegate to SCM-focused helper functions rather than embed parsing in `cli.py`. The helper layer will own:
- reading `progress.md`
- extracting the current-session block
- parsing normalized commit entries
- generating the final session summary Markdown
- rewriting `progress.md` with the new summary appended and the current-session block cleared

This keeps the CLI thin and lets tests exercise the summarization logic directly.

### Decision: Keep current-session as the only source for in-flight commit parsing

The command will summarize exactly the entries found between:
- `<!-- superspec:current-session:start -->`
- `<!-- superspec:current-session:end -->`

No explicit session identifier will be added in this change. The current-session marker pair already defines the active session boundary, so adding a second identifier now would create migration work without enabling the requested behavior.

### Decision: Keep current-session first and stack completed summaries newest-first below it

Completed session summaries will be inserted immediately after the `Current Session` block, leaving the markers in place for future commits. Older summaries remain below newer ones, so the managed region is always ordered as current-session first, then newest summary to oldest summary. The generated summary format is:

- `## YYYY-MM-DD Session x`
- `- Finish: <timestamp>`
- `### Done`
- `### Changes`
- `### Files`
- `### Next`

This preserves prior summaries, keeps session numbering derivable from the document itself, and gives the document a stable top-down reading order where the active session is always first.

### Decision: Derive session numbering from existing same-day session headings

`Session x` should be computed by scanning existing `## YYYY-MM-DD Session <n>` headings already present in `progress.md` for the current date and using the next number. This keeps numbering stable across multiple invocations on the same day without requiring extra metadata.

### Decision: Treat details as optional content during parsing and summary rendering

`superspec git commit` should accept `--details` as optional input, normalize blank values to an empty string, and omit the Git commit body paragraph when no details are provided. The progress entry renderer and the summarization parser should both treat missing or blank detail blocks as valid. During rendering:
- summary lines are always emitted
- detail lines are emitted only when stripped non-empty lines exist
- each detail line is rendered as an indented child bullet under its parent summary
- commit ledger entries omit the `Details` block entirely when details are blank

## Risks / Trade-offs

- [Risk] Hand-edited `progress.md` content may partially resemble session headings and distort same-day session counting -> Mitigation: only count headings that match the exact `## YYYY-MM-DD Session <n>` pattern.
- [Risk] Parsing normalized commit entries from Markdown is brittle if entry formatting drifts -> Mitigation: centralize both rendering and parsing in the same helper module and test multiline and blank-detail cases.
- [Risk] Clearing current-session after summary generation can lose data if the rewrite fails midway -> Mitigation: compute the full updated document in memory first, then write once.
- [Risk] Reordering existing summaries around the current-session block may move older session headings lower in the file -> Mitigation: keep non-managed front matter intact and enforce one deterministic managed ordering: current-session, newest summary, older summaries.
