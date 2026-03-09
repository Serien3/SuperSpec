## ADDED Requirements

### Requirement: Next-step retrieval command
The system MUST provide a command to retrieve exactly one executable step for a change in structured JSON form.

#### Scenario: Retrieve next ready step
- **WHEN** a client requests the next step for a change with pending runnable work
- **THEN** the system returns state `ready`
- **AND** includes step metadata, execution payload, and a lease token

#### Scenario: No remaining steps
- **WHEN** all steps are completed or skipped according to execution policy
- **THEN** the system returns state `done`
- **AND** does not return an executable step payload

### Requirement: Step completion reporting
The system MUST provide a command for clients to report successful step completion with structured result payload.

#### Scenario: Complete with valid lease token
- **WHEN** a client reports completion for a leased step with matching token
- **THEN** the step state transitions to `SUCCESS`
- **AND** result payload is stored as step output

### Requirement: Step failure reporting
The system MUST provide a command for clients to report step failure with structured error payload.

#### Scenario: Fail step with retry policy
- **WHEN** a client reports failure for an step that has remaining retry attempts
- **THEN** the system records the failure attempt
- **AND** keeps the step eligible for retry according to configured backoff

### Requirement: Lease-based step claim safety
The system MUST use lease tokens to prevent concurrent clients from completing the same step without ownership.

#### Scenario: Reject completion with invalid lease
- **WHEN** a client reports completion using a stale or mismatched lease token
- **THEN** the system rejects the report
- **AND** preserves current step state

### Requirement: Executor-specific payload contract
The system MUST return normalized execution payloads that distinguish script and skill execution modes.

#### Scenario: Script step payload
- **WHEN** the next step uses `executor=script`
- **THEN** the payload includes executable script command details

#### Scenario: Skill step payload
- **WHEN** the next step uses `executor=skill`
- **THEN** the payload includes skill reference (`name`, `version`, `input`, `contextFiles`)
- **AND** does not include full rendered prompt by default
