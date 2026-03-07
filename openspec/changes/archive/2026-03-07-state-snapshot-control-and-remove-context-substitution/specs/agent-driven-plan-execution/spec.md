## MODIFIED Requirements

### Requirement: Next-action retrieval command
The system MUST provide a command to retrieve exactly one executable action for a change in structured JSON form.

#### Scenario: Retrieve next ready action
- **WHEN** a client requests the next action for a change with pending runnable work
- **THEN** the system returns state `ready`
- **AND** returns only top-level fields `state` and `action`

#### Scenario: No remaining actions
- **WHEN** all actions are in terminal states according to execution policy
- **THEN** the system returns state `done`
- **AND** does not return an executable action payload

### Requirement: Executor-specific payload contract
The system MUST return normalized execution payloads that distinguish script, skill, and human execution modes, and MUST reject plans whose explicit `executor` value is not one of `skill`, `script`, or `human`.

#### Scenario: Script action payload
- **WHEN** the next action uses `executor=script`
- **THEN** the payload includes `script_command` and `prompt`
- **AND** may include literal `inputs` when action inputs are defined

#### Scenario: Skill action payload
- **WHEN** the next action uses `executor=skill`
- **THEN** the payload includes `skillName` and `prompt`
- **AND** does not include context file maps in the action payload
- **AND** may include literal `inputs` when action inputs are defined

#### Scenario: Human action payload
- **WHEN** the next action uses `executor=human`
- **THEN** the payload includes `human` review metadata and `prompt`
- **AND** does not include `script_command` or `skillName`
- **AND** may include literal `inputs` when action inputs are defined

#### Scenario: Runtime fields are not expression-expanded
- **WHEN** action runtime fields contain `${...}` substrings
- **THEN** protocol payload generation treats those fields as literal string content
- **AND** no runtime expression expansion scope is applied
