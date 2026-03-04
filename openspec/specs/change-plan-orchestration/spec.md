## Purpose

Define the change-scoped plan orchestration behavior for SuperSpec v0.5.0, including plan validation, protocol-driven action execution, and execution state tracking.
## Requirements
### Requirement: Change-scoped plan definition
The system MUST support a change-scoped `plan.json` located at `openspec/changes/<change-name>/plan.json` as the authoritative execution definition for that change, and MUST reject execution when the resolved runtime `context.changeDir` does not match the CLI-requested change.

#### Scenario: Load plan from change directory
- **WHEN** a user runs plan validation or execution for a change
- **THEN** the system loads `plan.json` from that change directory
- **AND** rejects execution if the file is missing

#### Scenario: Explicit plan initialization lifecycle
- **WHEN** a user creates a change without running plan initialization
- **THEN** the system treats that change as having no executable plan definition yet
- **AND** requires explicit plan initialization before plan validation or protocol execution can proceed

#### Scenario: Reject runtime context directory mismatch
- **WHEN** protocol execution is requested for change `A` but `plan.context.changeDir` resolves to another change directory `B`
- **THEN** protocol startup fails with a structured path validation error
- **AND** no execution state for change `B` is mutated by the command

### Requirement: Plan initialization schema selection
The system MUST provide a plan initialization option to select a named plan schema/workflow.

#### Scenario: Initialize plan with required schema key
- **WHEN** a user runs plan initialization with `--schema <name>`
- **THEN** the system writes a valid generated `plan.json` to the change directory
- **AND** the resulting plan is immediately eligible for plan validation

#### Scenario: Reject unsupported initialization selector
- **WHEN** a user runs plan initialization with an unsupported schema name
- **THEN** initialization fails with a selector validation error
- **AND** no plan file is created or overwritten

### Requirement: Schema-aware workflow resolution
The system MUST resolve plan initialization content through base-template-plus-workflow composition rather than a single monolithic template file.

#### Scenario: Resolve generated plan content from schema key
- **WHEN** initialization runs with a supported selector
- **THEN** the engine resolves the corresponding workflow and base template inputs
- **AND** interpolates change-scoped fields before writing the plan

### Requirement: Simplified single-agent starter template
The system MUST provide a default plan template optimized for single-agent, single-process, serial execution.

#### Scenario: Initialize simplified default plan
- **WHEN** a user initializes a plan with the default schema
- **THEN** the generated template expresses a serial action flow suitable for one agent
- **AND** excludes lease-oriented or concurrency-oriented starter fields

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
- **AND** it remains non-runnable until dependencies succeed and then transitions to `READY`

#### Scenario: Reject cyclic dependencies
- **WHEN** the action graph contains a cycle
- **THEN** validation fails before execution starts

#### Scenario: Resolve downstream actions after dependency failure
- **WHEN** an upstream dependency reaches terminal `FAILED`
- **THEN** downstream dependents are transitioned to terminal `FAILED` with dependency-failure context
- **AND** the run does not leave those dependents indefinitely pending

### Requirement: Unified action execution contract
The system MUST support both `skill` and `script` executors using a shared action contract with normalized outputs under serial single-agent execution.

#### Scenario: Skill executor action
- **WHEN** an action declares `executor: skill`
- **THEN** the execution protocol returns a skill action payload containing `skillName` and `prompt`
- **AND** stores normalized outputs only after explicit completion reporting

#### Scenario: Script executor action
- **WHEN** an action declares `executor: script`
- **THEN** the execution protocol returns a script action payload containing `script_command` and `prompt`
- **AND** stores normalized outputs only after explicit completion reporting

#### Scenario: Use built-in default executor
- **WHEN** an action omits explicit `executor`, `script`, and `skill` fields
- **THEN** the execution protocol resolves executor type from built-in runtime defaults
- **AND** runtime code uses the `DEFAULT_EXECUTOR` constant as the single source of truth for that fallback
- **AND** returns a payload shape consistent with the resolved executor type

#### Scenario: Limit runtime expression resolution surface
- **WHEN** an action includes template expressions
- **THEN** runtime expression resolution for next-action payload generation is applied only to `executor`, `script`, `skill`, and `inputs.prompt`
- **AND** other action fields do not participate in runtime payload expression expansion
- **AND** the runtime implementation does not provide a generic recursive resolver for arbitrary action objects

#### Scenario: Surface runtime expression resolution errors as protocol errors
- **WHEN** runtime expression resolution fails during next-action payload generation
- **THEN** execution does not fall back to an unstructured generic exception
- **AND** the engine raises a structured protocol error with code `invalid_expression`

### Requirement: OpenSpec workflow action support
The system MUST support the action types `openspec.proposal`, `openspec.specs`, `openspec.design`, `openspec.tasks`, and `openspec.apply` in plan execution.

#### Scenario: Validate allowed action types
- **WHEN** a plan contains an unsupported action type
- **THEN** plan validation fails with a clear type error

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

### Requirement: Retry configuration removal
The system MUST not expose retry policy configuration in runtime plan semantics.

#### Scenario: Reject retry fields in plan actions
- **WHEN** action definitions include retry controls
- **THEN** plan validation fails
- **AND** users are guided to fail-fast plus human intervention behavior
