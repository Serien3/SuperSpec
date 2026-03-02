## ADDED Requirements

### Requirement: Next-action retrieval command
The system MUST provide a command to retrieve exactly one executable action for a change in structured JSON form.

#### Scenario: Retrieve next ready action
- **WHEN** a client requests the next action for a change with pending runnable work
- **THEN** the system returns state `ready`
- **AND** includes action metadata, execution payload, and a lease token

#### Scenario: No remaining actions
- **WHEN** all actions are completed or skipped according to execution policy
- **THEN** the system returns state `done`
- **AND** does not return an executable action payload

### Requirement: Action completion reporting
The system MUST provide a command for clients to report successful action completion with structured result payload.

#### Scenario: Complete with valid lease token
- **WHEN** a client reports completion for a leased action with matching token
- **THEN** the action state transitions to `SUCCESS`
- **AND** result payload is stored as action output

### Requirement: Action failure reporting
The system MUST provide a command for clients to report action failure with structured error payload.

#### Scenario: Fail action with retry policy
- **WHEN** a client reports failure for an action that has remaining retry attempts
- **THEN** the system records the failure attempt
- **AND** keeps the action eligible for retry according to configured backoff

### Requirement: Lease-based action claim safety
The system MUST use lease tokens to prevent concurrent clients from completing the same action without ownership.

#### Scenario: Reject completion with invalid lease
- **WHEN** a client reports completion using a stale or mismatched lease token
- **THEN** the system rejects the report
- **AND** preserves current action state

### Requirement: Executor-specific payload contract
The system MUST return normalized execution payloads that distinguish script and skill execution modes.

#### Scenario: Script action payload
- **WHEN** the next action uses `executor=script`
- **THEN** the payload includes executable script command details

#### Scenario: Skill action payload
- **WHEN** the next action uses `executor=skill`
- **THEN** the payload includes skill reference (`name`, `version`, `input`, `contextFiles`)
- **AND** does not include full rendered prompt by default
