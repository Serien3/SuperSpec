## ADDED Requirements

### Requirement: Progress command summarizes the current session into progress.md
The system MUST provide a `superspec progress` command that reads all commit entries from the `current-session` block in the repository root `progress.md`, generates one Markdown session summary, writes that summary back into `progress.md`, and clears the current-session entries after a successful write.

#### Scenario: Summarize multiple current-session commits into one session block
- **WHEN** `progress.md` contains multiple normalized commit entries between `<!-- superspec:current-session:start -->` and `<!-- superspec:current-session:end -->`
- **AND** a user runs `superspec progress`
- **THEN** the system appends a session summary block to `progress.md`
- **AND** the `Current Session` section remains above all completed session summaries
- **AND** the new session summary is placed above older session summaries from the same file
- **AND** the session summary heading is `## YYYY-MM-DD Session x`
- **AND** the `### Done` section contains one bullet per commit summary in original commit order
- **AND** any non-empty detail lines appear as indented child bullets beneath their parent summary bullet
- **AND** the `### Changes` section lists unique change names from the summarized commits
- **AND** the `### Files` section lists unique file paths from the summarized commits
- **AND** the `### Next` section uses the `Next` value from the last summarized commit
- **AND** the `current-session` block is empty after the command succeeds

#### Scenario: Finish field records command completion time
- **WHEN** a user runs `superspec progress` and the current-session block contains at least one commit entry
- **THEN** the generated session summary contains a `- Finish: <timestamp>` line
- **AND** the timestamp reflects the summary command completion time rather than any commit timestamp

#### Scenario: Session numbering increments within the same date
- **WHEN** `progress.md` already contains `## 2026-03-15 Session 1` and `## 2026-03-15 Session 2`
- **AND** a user runs `superspec progress` on `2026-03-15`
- **THEN** the new summary heading is `## 2026-03-15 Session 3`

#### Scenario: Empty current-session ledger is rejected
- **WHEN** the `current-session` block contains no commit entries
- **AND** a user runs `superspec progress`
- **THEN** the command fails with a structured protocol error
- **AND** `progress.md` is left unchanged
