## ADDED Requirements

### Requirement: Change-scoped plan definition
The system MUST support a change-scoped `plan.json` located at `openspec/changes/<change-name>/plan.json` as the authoritative execution definition for that change.

#### Scenario: Load plan from change directory
- **WHEN** a user runs plan validation or execution for a change
- **THEN** the system loads `plan.json` from that change directory
- **AND** rejects execution if the file is missing

### Requirement: Plan schema version validation
The system MUST validate the declared plan schema version before any step execution begins.

#### Scenario: Reject unknown schema version
- **WHEN** `plan.json` contains an unsupported `schemaVersion`
- **THEN** the system fails validation
- **AND** does not execute any steps

### Requirement: Step dependency ordering
The system MUST execute steps in dependency-safe order and reject invalid dependency graphs.

#### Scenario: Execute only ready steps
- **WHEN** an step has unresolved dependencies
- **THEN** the step is not executed
- **AND** it remains pending until dependencies succeed

#### Scenario: Reject cyclic dependencies
- **WHEN** the step graph contains a cycle
- **THEN** validation fails before execution starts

### Requirement: Unified step execution contract
The system MUST support both `skill` and `script` executors using a shared step contract with normalized outputs.

#### Scenario: Skill executor step
- **WHEN** an step declares `executor: skill`
- **THEN** the orchestrator invokes the configured skill
- **AND** stores normalized outputs for downstream step references

#### Scenario: Script executor step
- **WHEN** an step declares `executor: script`
- **THEN** the orchestrator runs the configured script
- **AND** stores normalized outputs for downstream step references

### Requirement: Open step type support
The system MUST allow arbitrary non-empty step `type` values in plan execution.

#### Scenario: Accept custom step type
- **WHEN** a plan contains an step with a custom non-empty `type`
- **THEN** plan validation succeeds for step type semantics

### Requirement: Resumable execution state
The system MUST persist execution state to allow interrupted runs to resume safely.

#### Scenario: Resume after failed step
- **WHEN** a prior run failed after completing a subset of steps
- **THEN** a resume run continues from the next executable step
- **AND** previously successful steps are not re-executed unless explicitly requested

### Requirement: Per-step execution logs
The system MUST write per-step logs for each run under a run-specific directory.

#### Scenario: Inspect step log after failure
- **WHEN** an step fails during execution
- **THEN** a corresponding step log exists in the run log directory
- **AND** includes command or skill execution details sufficient for troubleshooting
