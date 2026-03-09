# change-advance-entrypoint Specification

## Purpose
Define the unified `superspec change advance` entrypoint behavior for listing, creating, and advancing changes.
## Requirements
### Requirement: Unified change advance command modes
The CLI SHALL provide a unified `superspec change advance` command that supports list mode, existing-change advance mode, and create-and-advance mode.

#### Scenario: List mode without arguments
- **WHEN** a user runs `superspec change advance` with no positional change name and no `--new`
- **THEN** the command lists change directories under `superspec/changes`
- **AND** the output excludes non-change directories such as `archive`

#### Scenario: Advance existing change by name
- **WHEN** a user runs `superspec change advance <change-name>`
- **THEN** the command resolves the target change and performs next-action pull semantics for that change
- **AND** non-JSON mode prints the action prompt or protocol state text

#### Scenario: Create and advance with explicit workflow selector
- **WHEN** a user runs `superspec change advance --new <workflow-type>/<change-name>`
- **THEN** the command creates the change directory, initializes workflow snapshot state in `execution/state.json`, and initializes `execution/events.log`
- **AND** the command immediately returns the first protocol pull result from that snapshot-backed state
- **AND** the command fails atomically with a structured error if creation or initialization fails

### Requirement: Advance command argument exclusivity
The CLI SHALL reject ambiguous `change advance` argument combinations with structured validation errors.

#### Scenario: Reject mixed positional and new selector
- **WHEN** a user provides both `<change-name>` and `--new <workflow-type>/<change-name>` in one command
- **THEN** the command fails with an invalid argument error
- **AND** no change state is mutated

#### Scenario: Reject malformed new selector
- **WHEN** a user provides `--new` without a `<workflow-type>/<change-name>` shape
- **THEN** the command fails with an invalid selector error
- **AND** the error includes remediation guidance for expected format
