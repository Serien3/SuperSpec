## MODIFIED Requirements

### Requirement: Executor-specific payload contract
The system MUST return normalized execution payloads that distinguish script, skill, and human execution modes, and MUST reject plans whose explicit `executor` value is not one of `skill`, `script`, or `human`.

#### Scenario: Script action payload
- **WHEN** the next action uses `executor=script`
- **THEN** the payload includes `script_command` and `prompt`

#### Scenario: Skill action payload
- **WHEN** the next action uses `executor=skill`
- **THEN** the payload includes `skillName` and `prompt`
- **AND** does not include context file maps in the action payload

#### Scenario: Human action payload
- **WHEN** the next action uses `executor=human`
- **THEN** the payload includes `human` review metadata and `prompt`
- **AND** does not include `script_command` or `skillName`

#### Scenario: Skill action completion contract
- **WHEN** a skill action finishes successfully in an external agent runtime
- **THEN** the client reports completion using the returned `actionId`
- **AND** the output payload includes runtime outcome fields sufficient for audit and replay decisions

#### Scenario: Skill action failure contract
- **WHEN** a skill action fails in an external agent runtime
- **THEN** the client reports failure using the returned `actionId`
- **AND** the error payload includes an error code/category and human-readable failure context

#### Scenario: Reject invalid explicit executor values at validation time
- **WHEN** a plan action declares an explicit `executor` value outside `skill|script|human`
- **THEN** plan validation fails before protocol execution starts
- **AND** no next-action payload is generated for that invalid action
