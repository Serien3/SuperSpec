## Purpose

Define the change-scoped plan orchestration behavior for SuperSpec v1.0.0, including plan validation, protocol-driven action execution, and execution state tracking.
## Requirements
### Requirement: Change-scoped runtime snapshot
The system MUST support a change-scoped runtime snapshot in `openspec/changes/<change-name>/execution/state.json` as the authoritative execution state for that change.

#### Scenario: Load execution runtime from state snapshot
- **WHEN** a user runs execution for a change
- **THEN** the system loads runtime execution state from `execution/state.json`
- **AND** rejects execution if the snapshot file is missing

#### Scenario: Unified advance bootstraps state snapshot for new change
- **WHEN** a user creates a change through `superspec change advance --new <workflow-type>/<change-name>`
- **THEN** the system creates a valid `execution/state.json` in that change directory as part of the same command flow
- **AND** the change is immediately executable by protocol pull commands without a separate initialization command

### Requirement: Workflow selection during change creation
The system MUST provide a workflow schema selector for snapshot generation through unified change creation flows.

#### Scenario: Initialize state snapshot with required schema key in unified flow
- **WHEN** a user runs `superspec change advance --new <schema>/<name>` with a supported schema
- **THEN** the system writes a valid generated runtime snapshot into `execution/state.json`
- **AND** the resulting snapshot is immediately eligible for execution

#### Scenario: Reject unsupported initialization selector
- **WHEN** a user provides an unsupported workflow schema selector in unified creation flow
- **THEN** initialization fails with a selector validation error
- **AND** no state snapshot file is created or overwritten

### Requirement: Schema-aware workflow resolution
The system MUST resolve initialization content through workflow composition and persist the resulting runtime baseline into the state snapshot.

#### Scenario: Resolve generated snapshot runtime from schema key
- **WHEN** initialization runs with a supported selector
- **THEN** the engine resolves the corresponding workflow input
- **AND** writes the resolved runtime baseline into `execution/state.json`

### Requirement: Simplified single-agent starter template
The system MUST provide a default plan template optimized for single-agent, single-process, serial execution.

#### Scenario: Initialize simplified default plan
- **WHEN** a user initializes a plan with the default schema
- **THEN** the generated template expresses a serial action flow suitable for one agent
- **AND** excludes lease-oriented or concurrency-oriented starter fields

### Requirement: Plan schema version validation
The system MUST validate the declared execution runtime schema version before any action execution begins.

#### Scenario: Reject unknown schema version
- **WHEN** snapshot runtime contains an unsupported `schemaVersion`
- **THEN** the system fails validation
- **AND** does not execute any actions

### Requirement: Action dependency ordering
The system MUST execute actions in dependency-safe order and reject invalid dependency graphs.

#### Scenario: Execute only ready actions
- **WHEN** an action has unresolved dependencies
- **THEN** the action is not executed
- **AND** it remains non-runnable until dependencies succeed and then transitions to `READY`

#### Scenario: Reject cyclic dependencies
- **WHEN** the action graph contains a cycle
- **THEN** validation fails before execution starts

#### Scenario: Resolve downstream actions after dependency failure
- **WHEN** an upstream dependency reaches terminal `FAILED`
- **THEN** downstream dependents are transitioned to terminal `FAILED` with dependency-failure context
- **AND** the run does not leave those dependents indefinitely pending

### Requirement: Unified action execution contract
The system MUST support `skill`, `script`, and `human` executors using a shared action contract with normalized outputs under serial single-agent execution.

#### Scenario: Skill executor action
- **WHEN** an action declares `executor: skill`
- **THEN** the execution protocol returns a skill action payload containing `skillName` and `prompt`
- **AND** stores normalized outputs only after explicit completion reporting

#### Scenario: Script executor action
- **WHEN** an action declares `executor: script`
- **THEN** the execution protocol returns a script action payload containing `script_command` and `prompt`
- **AND** stores normalized outputs only after explicit completion reporting

#### Scenario: Human executor action
- **WHEN** an action declares `executor: human`
- **THEN** the execution protocol returns a human action payload containing `human` review metadata and `prompt`
- **AND** stores normalized outputs only after explicit completion reporting

#### Scenario: No implicit executor inference
- **WHEN** an action omits explicit `executor`
- **THEN** plan validation fails before protocol execution starts
- **AND** no next-action payload is generated for that invalid action

#### Scenario: Reject non-inferable or ambiguous executor definition
- **WHEN** an action defines ambiguous executor payload fields
- **THEN** plan validation fails before protocol execution starts
- **AND** no next-action payload is generated for that invalid action

#### Scenario: Limit runtime expression resolution surface
- **WHEN** an action includes template expressions
- **THEN** runtime expression resolution for next-action payload generation is applied only to `executor`, `script`, `skill`, `prompt`, `human.instruction`, and `inputs` (recursive)
- **AND** expression scopes are constrained to `context.*`, `variables.*`, `actions.*`, `state.*`, and `env.*`
- **AND** other action fields do not participate in runtime payload expression expansion
- **AND** the runtime implementation does not provide a generic recursive resolver for arbitrary action objects

#### Scenario: Surface runtime expression resolution errors as protocol errors
- **WHEN** runtime expression resolution fails during next-action payload generation
- **THEN** execution does not fall back to an unstructured generic exception
- **AND** the engine raises a structured protocol error with code `invalid_expression`

### Requirement: Open action type support
The system MUST allow arbitrary non-empty action `type` values instead of enforcing a fixed allowlist.

#### Scenario: Accept custom action type
- **WHEN** a plan contains an action with a custom non-empty `type`
- **THEN** plan validation succeeds for action type semantics
- **AND** protocol execution can proceed using executor contract rules

### Requirement: Resumable execution state
The system MUST persist execution state to allow interrupted runs to resume safely in single-agent mode.

#### Scenario: Resume after failed action
- **WHEN** a prior run failed after completing a subset of actions
- **THEN** a resumed agent can continue by fetching the next runnable action via protocol commands
- **AND** previously successful actions are not re-executed unless explicitly requested

### Requirement: Per-action execution logs
The system MUST write per-action execution history for troubleshooting and auditability.

#### Scenario: Inspect action history after failure
- **WHEN** an action fails during execution
- **THEN** a corresponding execution event record exists in protocol execution storage
- **AND** includes error details sufficient for troubleshooting

### Requirement: Fail-fast failure handling
The system MUST apply terminal fail-fast behavior when any action failure is reported.

#### Scenario: Any reported failure halts workflow
- **WHEN** a running action is reported failed through the protocol
- **THEN** the workflow transitions to terminal `failed`
- **AND** no continuation policy is applied for additional autonomous actions

### Requirement: Retry fields have no runtime semantics
The system MUST not apply retry policy semantics from action fields during protocol execution.

#### Scenario: Ignore retry-like action metadata at runtime
- **WHEN** action definitions include retry-like metadata fields
- **THEN** plan validation and execution are governed by current schema and executor rules
- **AND** protocol runtime does not schedule retries based on those metadata fields
