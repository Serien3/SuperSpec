## Purpose

Define the change-scoped workflow execution behavior for SuperSpec v1.2.0, including workflow validation, protocol-driven step execution, and execution state tracking.
## Requirements
### Requirement: Change-scoped runtime snapshot
The system MUST support a change-scoped runtime snapshot in `superspec/changes/<change-name>/execution/state.json` as the authoritative execution state for that change.

#### Scenario: Load execution runtime from state snapshot
- **WHEN** a user runs execution for a change
- **THEN** the system loads runtime execution state from `execution/state.json`
- **AND** rejects execution if the snapshot file is missing

#### Scenario: Unified advance bootstraps state snapshot for new change
- **WHEN** a user creates a change through `superspec change advance --new <workflow-type>/<change-name>`
- **THEN** the system creates a valid `execution/state.json` in that change directory as part of the same command flow
- **AND** the change is immediately executable by protocol pull commands without a separate initialization command

### Requirement: Workflow selection during change creation
The system MUST provide a workflow selector for snapshot generation through unified change creation flows.

#### Scenario: Initialize state snapshot with required workflow key in unified flow
- **WHEN** a user runs `superspec change advance --new <workflow>/<name>` with a supported workflow
- **THEN** the system writes a valid generated runtime snapshot into `execution/state.json`
- **AND** the resulting snapshot is immediately eligible for execution

#### Scenario: Reject unsupported initialization selector
- **WHEN** a user provides an unsupported workflow selector in unified creation flow
- **THEN** initialization fails with a selector validation error
- **AND** no state snapshot file is created or overwritten

### Requirement: Selector-aware workflow resolution
The system MUST resolve initialization content through workflow composition and persist the resulting runtime baseline into the state snapshot.

#### Scenario: Resolve generated snapshot runtime from workflow key
- **WHEN** initialization runs with a supported selector
- **THEN** the engine resolves the corresponding workflow input
- **AND** writes the resolved runtime baseline into `execution/state.json`

### Requirement: Simplified single-agent built-in workflow
The system MUST provide a default built-in workflow optimized for single-agent, single-process, serial execution.

#### Scenario: Initialize simplified default workflow
- **WHEN** a user initializes a change with the default workflow
- **THEN** the generated runtime expresses a serial step flow suitable for one agent
- **AND** excludes lease-oriented or concurrency-oriented starter fields

### Requirement: Workflow schema identity persistence
The system MUST persist workflow schema identity metadata in the state snapshot.

#### Scenario: Snapshot records workflow schema identity
- **WHEN** a new change snapshot is initialized
- **THEN** `execution/state.json.meta` includes all workflow top-level fields except `steps`
- **AND** runtime execution state remains in `execution/state.json.runtime`

### Requirement: Step dependency ordering
The system MUST execute steps in dependency-safe order and reject invalid dependency graphs.

#### Scenario: Execute only ready steps
- **WHEN** an step has unresolved dependencies
- **THEN** the step is not executed
- **AND** it remains non-runnable until dependencies succeed and then transitions to `READY`

#### Scenario: Reject cyclic dependencies
- **WHEN** the step graph contains a cycle
- **THEN** validation fails before execution starts

#### Scenario: Resolve downstream steps after dependency failure
- **WHEN** an upstream dependency reaches terminal `FAILED`
- **THEN** downstream dependents are transitioned to terminal `FAILED` with dependency-failure context
- **AND** the run does not leave those dependents indefinitely pending

### Requirement: Unified step execution contract
The system MUST support `skill`, `script`, and `human` executors using a shared step contract under serial single-agent execution.

#### Scenario: Skill executor step
- **WHEN** an step declares `executor: skill`
- **THEN** the execution protocol returns a next-step payload containing `change`, `skillName`, and `prompt`
- **AND** completion only transitions state without storing an step output payload

#### Scenario: Script executor step
- **WHEN** an step declares `executor: script`
- **THEN** the execution protocol returns a next-step payload containing `change`, `script_command`, and `prompt`
- **AND** completion only transitions state without storing an step output payload

#### Scenario: Human executor step
- **WHEN** an step declares `executor: human`
- **THEN** the execution protocol returns a next-step payload containing `change`, optional `option` review metadata, and `prompt`
- **AND** completion only transitions state without storing an step output payload

#### Scenario: No implicit executor inference
- **WHEN** an step omits explicit `executor`
- **THEN** workflow validation fails before protocol execution starts
- **AND** no next-step payload is generated for that invalid step

#### Scenario: Reject non-inferable or ambiguous executor definition
- **WHEN** an step defines ambiguous executor payload fields
- **THEN** workflow validation fails before protocol execution starts
- **AND** no next-step payload is generated for that invalid step

#### Scenario: Runtime fields are treated as literal values
- **WHEN** an step runtime field contains `${...}` substrings
- **THEN** next-step payload generation keeps those values literal
- **AND** no expression expansion is performed by protocol runtime

### Requirement: Resumable execution state
The system MUST persist execution state to allow interrupted runs to resume safely in single-agent mode.

#### Scenario: Resume after failed step
- **WHEN** a prior run failed after completing a subset of steps
- **THEN** a resumed agent observes terminal workflow state through protocol commands
- **AND** no additional runnable step is allocated automatically after the failure
- **AND** previously successful steps are not re-executed unless explicitly requested

### Requirement: Per-step execution logs
The system MUST write per-step execution history for troubleshooting and auditability.

#### Scenario: Inspect step history after failure
- **WHEN** an step fails during execution
- **THEN** a corresponding execution event record exists in protocol execution storage
- **AND** includes error details sufficient for troubleshooting

### Requirement: Fail-fast failure handling
The system MUST apply terminal fail-fast behavior when any step failure is reported.

#### Scenario: Any reported failure halts workflow
- **WHEN** a running step is reported failed through the protocol
- **THEN** the workflow transitions to terminal `failed`
- **AND** all remaining non-terminal steps are terminalized under the same failed run
- **AND** no continuation policy is applied for additional autonomous steps

### Requirement: Retry fields have no runtime semantics
The system MUST not apply retry policy semantics from step fields during protocol execution.

#### Scenario: Ignore retry-like step metadata at runtime
- **WHEN** step definitions include retry-like metadata fields
- **THEN** workflow validation and execution are governed by current workflow contract and executor rules
- **AND** protocol runtime does not schedule retries based on those metadata fields
