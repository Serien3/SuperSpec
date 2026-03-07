# single-workflow-per-change Specification

## Purpose
TBD - created by archiving change unify-change-workflow-entrypoint. Update Purpose after archive.
## Requirements
### Requirement: One workflow binding per change
Each change SHALL bind to exactly one workflow type at creation time, and that binding SHALL be reused for all future advance operations for that change.

#### Scenario: Bind workflow during new advance flow
- **WHEN** `superspec change advance --new <workflow-type>/<change-name>` succeeds
- **THEN** the created change persists the selected workflow identity in change-scoped execution metadata
- **AND** subsequent `change advance <change-name>` uses that bound workflow context

#### Scenario: Reject workflow rebinding for existing change
- **WHEN** a user attempts to recreate an existing change with a different workflow type selector
- **THEN** the command fails with a structured workflow-binding conflict error
- **AND** the existing change workflow binding remains unchanged

### Requirement: Custom workflow compatibility
Workflow binding SHALL support built-in and user-provided workflow definitions using the same resolver contract.

#### Scenario: Resolve built-in workflow type
- **WHEN** `--new` references a built-in workflow type
- **THEN** the plan initialization resolves the built-in workflow file and creates a valid plan

#### Scenario: Resolve user-defined workflow type
- **WHEN** `--new` references a workflow type provided under repository workflow schema paths
- **THEN** the plan initialization resolves the user-defined workflow file and creates a valid plan
- **AND** validation failures are returned with existing structured schema error payloads

