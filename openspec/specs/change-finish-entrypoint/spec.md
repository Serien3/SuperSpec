# change-finish-entrypoint Specification

## Purpose

Define the `superspec change finish` command for terminal change cleanup driven by workflow policy.

## Requirements

### Requirement: Explicit change finish command
The CLI SHALL provide `superspec change finish <change-name>` to complete an active change using workflow-defined retention policy unless the user explicitly overrides it.

#### Scenario: Finish archives a spec-driven change by default
- **WHEN** a user runs `superspec change finish <change-name>` for an existing terminal change whose workflow declares `finishPolicy: "archive"`
- **THEN** the command removes that change's `execution/` directory
- **AND** moves the remaining change directory into `superspec/changes/archive/<started-date>-<change-name>-<workflow-id>`

#### Scenario: Finish deletes a short-lived change by default
- **WHEN** a user runs `superspec change finish <change-name>` for an existing terminal change whose workflow declares `finishPolicy: "delete"`
- **THEN** the command removes `superspec/changes/<change-name>` entirely
- **AND** no archive directory is created for that change

### Requirement: Finish allows explicit retention override
The CLI SHALL allow users to override workflow default retention with exactly one of `--archive`, `--delete`, or `--keep`.

#### Scenario: Finish override keeps the change directory
- **WHEN** a user runs `superspec change finish <change-name> --keep` for an existing terminal change
- **THEN** the command leaves `superspec/changes/<change-name>` unchanged
- **AND** the command reports that the change was finished with keep retention

#### Scenario: Finish override archives a delete-default workflow
- **WHEN** a user runs `superspec change finish <change-name> --archive` for an existing terminal change whose workflow declares `finishPolicy: "delete"`
- **THEN** the command archives the change using the standard archive naming rules

### Requirement: Running destructive finish actions require force
The CLI SHALL reject destructive finish actions for actively running changes unless the user explicitly opts in.

#### Scenario: Reject archive or delete finish for running change by default
- **WHEN** a user runs `superspec change finish <change-name>` or `superspec change finish <change-name> --archive` or `superspec change finish <change-name> --delete` for an existing change whose runtime status is `running`
- **THEN** the command fails with a structured invalid-state error
- **AND** the active change directory remains unchanged

#### Scenario: Force delete finish for running change
- **WHEN** a user runs `superspec change finish <change-name> --delete --force` for an existing change whose runtime status is `running`
- **THEN** the command removes the active change directory

### Requirement: Missing changes fail clearly
The CLI SHALL return a stable structured error when the requested active change does not exist.

#### Scenario: Reject finish for unknown change
- **WHEN** a user runs `superspec change finish <change-name>` and `superspec/changes/<change-name>` does not exist
- **THEN** the command fails with error code `change_not_found`
- **AND** no archive directory is created
