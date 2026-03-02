## ADDED Requirements

### Requirement: Change-scoped plan definition
The system MUST support a change-scoped `plan.json` located at `openspec/changes/<change-name>/plan.json` as the authoritative execution definition for that change.

#### Scenario: Load plan from change directory
- **WHEN** a user runs plan validation or execution for a change
- **THEN** the system loads `plan.json` from that change directory
- **AND** rejects execution if the file is missing

### Requirement: Plan schema version validation
The system MUST validate the declared plan schema version before any action execution begins.

#### Scenario: Reject unknown schema version
- **WHEN** `plan.json` contains an unsupported `schemaVersion`
- **THEN** the system fails validation
- **AND** does not execute any actions

### Requirement: Action dependency ordering
The system MUST execute actions in dependency-safe order and reject invalid dependency graphs.

#### Scenario: Execute only ready actions
- **WHEN** an action has unresolved dependencies
- **THEN** the action is not executed
- **AND** it remains pending until dependencies succeed

#### Scenario: Reject cyclic dependencies
- **WHEN** the action graph contains a cycle
- **THEN** validation fails before execution starts

### Requirement: Unified action execution contract
The system MUST support both `skill` and `script` executors using a shared action contract with normalized outputs.

#### Scenario: Skill executor action
- **WHEN** an action declares `executor: skill`
- **THEN** the orchestrator invokes the configured skill
- **AND** stores normalized outputs for downstream action references

#### Scenario: Script executor action
- **WHEN** an action declares `executor: script`
- **THEN** the orchestrator runs the configured script
- **AND** stores normalized outputs for downstream action references

### Requirement: OpenSpec workflow action support
The system MUST support the action types `openspec.proposal`, `openspec.specs`, `openspec.design`, `openspec.tasks`, and `openspec.apply` in plan execution.

#### Scenario: Validate allowed action types
- **WHEN** a plan contains an unsupported action type
- **THEN** plan validation fails with a clear type error

### Requirement: Resumable execution state
The system MUST persist execution state to allow interrupted runs to resume safely.

#### Scenario: Resume after failed action
- **WHEN** a prior run failed after completing a subset of actions
- **THEN** a resume run continues from the next executable action
- **AND** previously successful actions are not re-executed unless explicitly requested

### Requirement: Per-action execution logs
The system MUST write per-action logs for each run under a run-specific directory.

#### Scenario: Inspect action log after failure
- **WHEN** an action fails during execution
- **THEN** a corresponding action log exists in the run log directory
- **AND** includes command or skill execution details sufficient for troubleshooting
