## MODIFIED Requirements

### Requirement: Unified change advance command modes
The CLI SHALL provide a unified `superspec change advance` command that supports list mode, existing-change advance mode, and create-and-advance mode.

#### Scenario: List mode without arguments
- **WHEN** a user runs `superspec change advance` with no positional change name and no `--new`
- **THEN** the command returns the same change listing semantics as current `superspec change list`
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
