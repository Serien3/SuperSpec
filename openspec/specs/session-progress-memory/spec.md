## Purpose

Define how `superspec git commit` captures session progress into Git history, change execution state, and the repository root `progress.md`.

## Requirements

### Requirement: Git commit command accepts structured session inputs
The system MUST require a change name, a commit subject summary, and a next-step note when running `superspec git commit`, and it MUST accept an optional commit body narrative.

#### Scenario: Successful commit uses summary as subject and details as body
- **WHEN** a user runs `superspec git commit demo-change --summary "feat: add file" --details "Body line one" --next "do next thing"`
- **THEN** the system creates a Git commit whose subject is `feat: add file`
- **AND** the Git commit body contains `Body line one`
- **AND** the command prints the successful Git commit output instead of JSON

#### Scenario: Blank details are omitted from git commit body and progress entry
- **WHEN** a user runs `superspec git commit demo-change --summary "feat: add file" --next "do next thing"` without `--details`
- **THEN** the system creates a Git commit whose message contains only the summary subject
- **AND** the resulting `progress.md` commit entry does not include a `Details` block

#### Scenario: Missing required structured commit fields are rejected
- **WHEN** a user omits either `--summary` or `--next`
- **THEN** the command fails validation
- **AND** no Git commit is created

### Requirement: Git commit command updates change execution state from committed files
The system MUST stage repository changes before committing, and MUST merge committed file paths into the target change execution runtime.

#### Scenario: Auto-staged commit records committed files
- **WHEN** a user modifies tracked or untracked repository files and runs `superspec git commit`
- **THEN** the command stages those file changes before creating the Git commit
- **AND** the command may include the target change `execution/state.json` and `execution/events.log` when they already have staged or unstaged changes before the commit is created
- **AND** the committed file list is merged into `superspec/changes/<change>/execution/state.json.runtime.files_changed`

#### Scenario: Root progress file may be included in the commit
- **WHEN** `progress.md` already has unstaged edits before `superspec git commit` runs
- **THEN** the command stages `progress.md`
- **AND** `progress.md` may appear in the committed file list for that commit

### Requirement: Git commit command maintains machine-readable current-session progress
The system MUST create or update a root `progress.md` file after a successful `superspec git commit` and MUST write each commit entry in a stable machine-readable structure.

#### Scenario: Create progress file and markers on first commit
- **WHEN** the repository root does not contain `progress.md` and a `superspec git commit` command succeeds
- **THEN** the system creates `progress.md`
- **AND** the file contains `<!-- superspec:current-session:start -->` and `<!-- superspec:current-session:end -->`
- **AND** the current-session section contains an entry for the new commit

#### Scenario: Progress entry records summary details block next and files
- **WHEN** a `superspec git commit` command updates `progress.md`
- **THEN** the written entry includes the commit hash, timestamp, change name, summary, next step, and changed file paths
- **AND** the entry wraps non-empty details text between `<!-- superspec:details:start -->` and `<!-- superspec:details:end -->`
- **AND** multiline details content is preserved inside that block
- **AND** blank details content omits the `Details` block entirely

#### Scenario: Existing content outside current-session markers is preserved
- **WHEN** `progress.md` already contains content outside the current-session markers and a later `superspec git commit` succeeds
- **THEN** the system preserves content outside the current-session markers
- **AND** appends a new current-session entry without removing prior entries
