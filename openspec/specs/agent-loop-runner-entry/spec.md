## Purpose

Define standardized agent guidance for running SuperSpec plans end-to-end using the pull protocol loop.
## Requirements
### Requirement: Agent loop execution guidance
The system MUST provide standardized guidance (via skill and/or AGENT.md) that instructs an external agent to execute the protocol loop for a change until the plan reaches a terminal state.

#### Scenario: Run loop to terminal state from unified entry guidance
- **WHEN** an agent follows the published guidance for a valid change
- **THEN** the agent enters the loop using `superspec change advance <change-name>` as the next-step entry command
- **AND** exits only when protocol state is `done`

### Requirement: Executor-dispatched step execution
The agent guidance MUST define dispatch behavior by executor type and report outcomes through protocol commands.

#### Scenario: Execute script step from guidance
- **WHEN** next-step pull returns an step containing `script_command`
- **THEN** the guided agent executes `step.script_command`
- **AND** reports `complete` or `fail` with the returned step identifier

#### Scenario: Execute skill step from guidance
- **WHEN** next-step pull returns an step containing `skillName`
- **THEN** the guided agent invokes the skill named by `step.skillName`
- **AND** reports `complete` or `fail` with the returned step identifier

### Requirement: Loop observability and terminal signaling
The agent guidance MUST specify structured progress reporting and terminal outcome signaling for success and failure.

#### Scenario: Terminal success signaling
- **WHEN** the loop reaches `done` and `superspec change status <change-name>` reports `success`
- **THEN** the guided agent reports terminal success
- **AND** includes final progress summary

#### Scenario: Terminal failure signaling
- **WHEN** the loop reaches `done` and `superspec change status <change-name>` reports `failed`
- **THEN** the guided agent reports terminal failure
- **AND** surfaces the last failed step id
