## Purpose

Define guardrails that enforce change-target integrity for protocol execution state access.

## Requirements

### Requirement: CLI change target integrity enforcement
The system MUST ensure protocol execution state is read and written only under the same change requested by the CLI command.

#### Scenario: Reject context changeDir mismatch with CLI target
- **WHEN** a user invokes a protocol command for change `X` and `plan.context.changeDir` resolves to change `Y`
- **THEN** the command fails before protocol state mutation
- **AND** the system returns a structured path validation error
- **AND** no execution files are created or updated under change `Y`

#### Scenario: Allow execution when changeDir matches target change
- **WHEN** a user invokes a protocol command for change `X` and `plan.context.changeDir` resolves to change `X`
- **THEN** protocol execution proceeds using that change directory
- **AND** execution state files remain scoped to change `X`
