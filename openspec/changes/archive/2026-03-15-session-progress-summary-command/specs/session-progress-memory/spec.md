## MODIFIED Requirements

### Requirement: Git commit command maintains machine-readable current-session progress
The system MUST create or update a root `progress.md` file after a successful `superspec git commit` and MUST write each commit entry in a stable machine-readable structure that later automation can summarize and clear.

#### Scenario: Create progress file and markers on first commit
- **WHEN** the repository root does not contain `progress.md` and a `superspec git commit` command succeeds
- **THEN** the system creates `progress.md`
- **AND** the file contains `<!-- superspec:current-session:start -->` and `<!-- superspec:current-session:end -->`
- **AND** the current-session section contains an entry for the new commit

#### Scenario: Progress entry records summary details block next and files
- **WHEN** a `superspec git commit` command updates `progress.md`
- **THEN** the written entry includes the commit hash, timestamp, change name, summary, next step, and changed file paths
- **AND** non-empty multiline details content is preserved so later summary generation can emit one child bullet per line
- **AND** blank or whitespace-only details content does not need to produce visible detail bullets in later summaries

#### Scenario: Existing content outside current-session markers is preserved
- **WHEN** `progress.md` already contains content outside the current-session markers and a later `superspec git commit` succeeds
- **THEN** the system preserves content outside the current-session markers
- **AND** appends a new current-session entry without removing prior entries
