## MODIFIED Requirements

### Requirement: Step dependency ordering
The system MUST execute steps in dependency-safe order and reject invalid dependency graphs.

#### Scenario: Execute only ready steps
- **WHEN** an step has unresolved dependencies
- **THEN** the step is not executed
- **AND** it remains pending until dependencies succeed

#### Scenario: Reject cyclic dependencies
- **WHEN** the step graph contains a cycle
- **THEN** validation fails before execution starts

#### Scenario: Resolve downstream steps after dependency failure
- **WHEN** an upstream dependency reaches terminal `FAILED`
- **THEN** downstream dependents are transitioned to terminal `FAILED` with dependency-failure context
- **AND** the run does not leave those dependents indefinitely pending

## ADDED Requirements

### Requirement: Failure policy enum constraints
The system MUST limit step failure policy values to the supported runtime semantics.

#### Scenario: Accept supported failure policies
- **WHEN** plan defaults or step overrides specify `onFail` as `stop` or `continue`
- **THEN** plan validation succeeds for that field

#### Scenario: Reject unsupported skip-dependent policy
- **WHEN** plan defaults or step overrides specify `onFail` as `skip_dependents`
- **THEN** plan validation fails with a clear enum validation error
