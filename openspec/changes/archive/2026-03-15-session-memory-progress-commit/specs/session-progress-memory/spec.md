## ADDED Requirements

### Requirement: Git commit command returns structured session progress context
The system MUST return a structured commit context payload whenever `superspec git commit <change> --message <message>` succeeds.

#### Scenario: Successful commit returns expanded payload
- **WHEN** a user runs `superspec git commit demo-change --message "feat: add file"` and the git commit succeeds
- **THEN** the JSON output includes `change`, `commit_hash`, `message`, `committed_at`, and `files_changed`
- **AND** the JSON output includes `progress_file`
- **AND** the JSON output includes a `progress_entry` object describing the record written for the current session

### Requirement: Git commit command maintains root progress file
The system MUST create or update a root `progress.md` file after a successful `superspec git commit`.

#### Scenario: Create progress file on first commit
- **WHEN** the repository root does not contain `progress.md` and a `superspec git commit` command succeeds
- **THEN** the system creates `progress.md`
- **AND** the file contains a current-session marker pair
- **AND** the file includes a commit entry for the new commit inside the marked current-session section

#### Scenario: Append a second commit entry without losing prior content
- **WHEN** `progress.md` already contains the current-session markers and one previous commit entry
- **AND** a later `superspec git commit` command succeeds
- **THEN** the system preserves content outside the current-session markers
- **AND** appends a new commit entry inside the current-session section
- **AND** keeps the previous commit entry intact

### Requirement: Current-session entries use normalized machine-readable fields
The system MUST write current-session commit entries in a stable Markdown structure that can be read by later automation.

#### Scenario: Commit entry contains normalized fields
- **WHEN** a `superspec git commit` command updates `progress.md`
- **THEN** the written entry includes the commit hash, timestamp, change name, message title, and changed file paths
- **AND** each field is labeled consistently across commits
