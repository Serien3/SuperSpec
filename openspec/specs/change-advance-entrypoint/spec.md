# change-advance-entrypoint Specification

## Purpose
Define the `superspec change` command entrypoints for listing, creating, and advancing changes.
## Requirements
### Requirement: Explicit change listing command
The CLI SHALL provide `superspec change list` to return all unarchived changes.

#### Scenario: List unarchived changes
- **WHEN** a user runs `superspec change list`
- **THEN** the command lists change directories under `superspec/changes`
- **AND** the output excludes non-change directories such as `archive`

### Requirement: Change advance command modes
The CLI SHALL provide `superspec change advance` for existing-change advance mode and create-and-advance mode.

#### Scenario: Advance existing change by name
- **WHEN** a user runs `superspec change advance <change-name>`
- **THEN** the command resolves the target change and performs next-step pull semantics for that change
- **AND** non-JSON mode prints the step prompt or protocol state text

#### Scenario: Create and advance with explicit workflow selector
- **WHEN** a user runs `superspec change advance --new <workflow-type>/<change-name>`
- **THEN** the command creates the change directory, initializes workflow snapshot state in `execution/state.json`, and initializes `execution/events.log`
- **AND** the command immediately returns the first protocol pull result from that snapshot-backed state
- **AND** the command fails atomically with a structured error if creation or initialization fails

#### Scenario: Create and advance with explicit goal
- **WHEN** a user runs `superspec change advance --new <workflow-type>/<change-name> --goal "<sentence>"`
- **THEN** the command writes that sentence to `execution/state.json.runtime.goal`
- **AND** the returned protocol payload includes the same `goal` value

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

### Requirement: Selector-free change advance lists active changes
The CLI SHALL treat `superspec change advance` without selectors as a listing mode for active changes.

#### Scenario: Advance without args lists active changes
- **WHEN** a user runs `superspec change advance` with no positional change name and no `--new`
- **THEN** the command returns the same change listing semantics as `superspec change list`
- **AND** the output excludes non-change directories such as `archive`
