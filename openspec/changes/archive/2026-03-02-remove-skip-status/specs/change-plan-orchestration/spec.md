## MODIFIED Requirements

### Requirement: Action dependency ordering
The system MUST execute actions in dependency-safe order and reject invalid dependency graphs.

#### Scenario: Execute only ready actions
- **WHEN** an action has unresolved dependencies
- **THEN** the action is not executed
- **AND** it remains pending until dependencies succeed

#### Scenario: Reject cyclic dependencies
- **WHEN** the action graph contains a cycle
- **THEN** validation fails before execution starts

#### Scenario: Resolve downstream actions after dependency failure
- **WHEN** an upstream dependency reaches terminal `FAILED`
- **THEN** downstream dependents are transitioned to terminal `FAILED` with dependency-failure context
- **AND** the run does not leave those dependents indefinitely pending

## ADDED Requirements

### Requirement: Failure policy enum constraints
The system MUST limit action failure policy values to the supported runtime semantics.

#### Scenario: Accept supported failure policies
- **WHEN** plan defaults or action overrides specify `onFail` as `stop` or `continue`
- **THEN** plan validation succeeds for that field

#### Scenario: Reject unsupported skip-dependent policy
- **WHEN** plan defaults or action overrides specify `onFail` as `skip_dependents`
- **THEN** plan validation fails with a clear enum validation error
