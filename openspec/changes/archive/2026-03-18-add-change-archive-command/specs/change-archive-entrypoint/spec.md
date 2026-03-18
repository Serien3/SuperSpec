# change-archive-entrypoint Specification

## Purpose

Define the `superspec change archive` command for retiring active changes into the archive area.

## Requirements

### Requirement: Explicit change archive command
The CLI SHALL provide `superspec change archive <change-name>` to archive an active change directory.

#### Scenario: Archive a terminal change
- **WHEN** a user runs `superspec change archive <change-name>` for an existing change whose runtime status is not `running`
- **THEN** the command removes that change's `execution/` directory
- **AND** moves the remaining change directory into `superspec/changes/archive/<started-date>-<change-name>-<workflow-type>`

### Requirement: Running changes require force
The CLI SHALL reject archive requests for actively running changes unless the user explicitly opts in.

#### Scenario: Reject archive for running change by default
- **WHEN** a user runs `superspec change archive <change-name>` for an existing change whose runtime status is `running`
- **THEN** the command fails with a structured invalid-state error
- **AND** the active change directory remains unchanged

#### Scenario: Force archive for running change
- **WHEN** a user runs `superspec change archive <change-name> --force` for an existing change whose runtime status is `running`
- **THEN** the command archives the change using the standard archive naming rules

### Requirement: Missing changes fail clearly
The CLI SHALL return a stable structured error when the requested active change does not exist.

#### Scenario: Reject archive for unknown change
- **WHEN** a user runs `superspec change archive <change-name>` and `superspec/changes/<change-name>` does not exist
- **THEN** the command fails with error code `change_not_found`
- **AND** no archive directory is created
