## MODIFIED Requirements

### Requirement: Agent loop execution guidance
The system MUST provide standardized guidance (via skill and/or AGENT.md) that instructs an external agent to execute the protocol loop for a change until the plan reaches a terminal state.

#### Scenario: Run loop to terminal state from unified entry guidance
- **WHEN** an agent follows the published guidance for a valid change
- **THEN** the agent enters the loop using `superspec change advance <change-name>` as the next-action entry command
- **AND** exits only when protocol state is `done`

### Requirement: Executor-dispatched action execution
The agent guidance MUST define dispatch behavior by executor type and report outcomes through protocol commands.

#### Scenario: Execute script action from guidance
- **WHEN** next-action pull returns an action with `executor=script`
- **THEN** the guided agent executes `action.script_command`
- **AND** reports `complete` or `fail` with the returned action identifier

#### Scenario: Execute skill action from guidance
- **WHEN** next-action pull returns an action with `executor=skill`
- **THEN** the guided agent invokes the skill named by `action.skillName`
- **AND** reports `complete` or `fail` with the returned action identifier

### Requirement: Loop observability and terminal signaling
The agent guidance MUST specify structured progress reporting and terminal outcome signaling for success and failure.

#### Scenario: Terminal success signaling
- **WHEN** the loop reaches `done` and `status` reports `success`
- **THEN** the guided agent reports terminal success
- **AND** includes final progress summary

#### Scenario: Terminal failure signaling
- **WHEN** the loop reaches `done` and `status` reports `failed`
- **THEN** the guided agent reports terminal failure
- **AND** surfaces the last failure action and error payload
