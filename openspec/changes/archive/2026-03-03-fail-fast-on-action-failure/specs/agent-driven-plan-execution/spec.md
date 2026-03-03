## MODIFIED Requirements

### Requirement: Action failure reporting
The system MUST provide a command for clients to report action failure with structured error payload and MUST treat reported failure as terminal for the workflow.

#### Scenario: Fail action immediately terminalizes workflow
- **WHEN** a client reports failure for a running action
- **THEN** the action transitions to `FAILED`
- **AND** the workflow state transitions to terminal `failed`
- **AND** no retry scheduling is created

#### Scenario: Propagate dependency failure to downstream actions
- **WHEN** an action reaches terminal `FAILED` and downstream actions depend on it directly or transitively
- **THEN** those downstream actions transition to terminal `FAILED`
- **AND** each propagated failure includes dependency-failure context identifying the upstream failed action

### Requirement: Agent-managed loop semantics
The protocol MUST support agent-managed execution loops that stop on terminal states and rely on humans for post-failure recovery.

#### Scenario: Failure ends loop
- **WHEN** an agent reports failure for any action
- **THEN** subsequent `next` calls return `done`
- **AND** the agent loop does not continue autonomous retry polling

### Requirement: Status contract visibility in debug mode
The system MUST return protocol contract metadata in status responses only when debug mode is explicitly requested.

#### Scenario: Status contract excludes retry mode
- **WHEN** a client calls status in any mode
- **THEN** the response includes execution state and progress fields
- **AND** does not expose retry-focused payload sections (`scheduledCount`, `nextWakeAt`, `nextWakeInSec`, `scheduled`)

## REMOVED Requirements

### Requirement: Retry-focused status mode
**Reason**: Workflow failure is now terminal at first reported action failure, so retry scheduling and wake-window reporting are no longer part of protocol behavior.

**Migration**: Use standard `superspec plan status --json` and inspect `status` + `lastFailure` for failure handling.
