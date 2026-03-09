## MODIFIED Requirements

### Requirement: Agent loop execution guidance
The system MUST provide standardized guidance (via skill and/or AGENT.md) that instructs an external agent to execute the protocol loop for a change until the plan reaches a terminal state.

#### Scenario: Run loop to terminal state from guidance
- **WHEN** an agent follows the published guidance for a valid change
- **THEN** the agent repeatedly fetches work using `next`
- **AND** executes and reports outcomes in strict serial order until protocol state is `done`

### Requirement: Executor-dispatched step execution
The agent guidance MUST define dispatch behavior by executor type and report outcomes through protocol commands.

#### Scenario: Execute script step from guidance
- **WHEN** `next` returns an step with `executor=script`
- **THEN** the guided agent executes the provided script command
- **AND** reports `complete` or `fail` using the returned step identifier

#### Scenario: Execute skill step from guidance
- **WHEN** `next` returns an step with `executor=skill`
- **THEN** the guided agent invokes a skill runtime using the provided skill payload
- **AND** reports `complete` or `fail` using the returned step identifier

### Requirement: Loop observability and terminal signaling
The agent guidance MUST specify structured progress reporting and terminal outcome signaling for success and failure.

#### Scenario: Terminal success signaling
- **WHEN** the loop reaches `done` with change status `success`
- **THEN** the guided agent reports terminal success
- **AND** includes final progress summary

#### Scenario: Terminal failure signaling
- **WHEN** the loop reaches `done` with change status `failed`
- **THEN** the guided agent reports terminal failure
- **AND** surfaces the last failure step and error payload
