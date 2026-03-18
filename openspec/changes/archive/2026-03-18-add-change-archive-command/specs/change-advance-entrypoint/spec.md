# change-advance-entrypoint Specification

## Delta

### Requirement: Explicit change listing command
The CLI SHALL provide `superspec change list` to return all unarchived changes.

#### Scenario: List unarchived changes
- **WHEN** a user runs `superspec change list`
- **THEN** the command lists change directories under `superspec/changes`
- **AND** the output excludes non-change directories such as `archive`

### Requirement: Explicit change archive command
The CLI SHALL provide `superspec change archive <change-name>` to retire an active change into the archive area.

#### Scenario: Archive command is part of change lifecycle surface
- **WHEN** a user runs `superspec change archive <change-name>`
- **THEN** the command applies archive lifecycle semantics for that active change
