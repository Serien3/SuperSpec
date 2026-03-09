## MODIFIED Requirements

### Requirement: Executor-specific payload contract
The system MUST return normalized execution payloads that distinguish script, skill, and human execution modes.

#### Scenario: Script step payload
- **WHEN** the next step uses `executor=script`
- **THEN** the payload includes `script_command` and `prompt`

#### Scenario: Skill step payload
- **WHEN** the next step uses `executor=skill`
- **THEN** the payload includes `skillName` and `prompt`
- **AND** does not include context file maps in the step payload

#### Scenario: Human step payload
- **WHEN** the next step uses `executor=human`
- **THEN** the payload includes `human` review metadata and `prompt`
- **AND** does not include `script_command` or `skillName`

#### Scenario: Skill step completion contract
- **WHEN** a skill step finishes successfully in an external agent runtime
- **THEN** the client reports completion using the returned `stepId`
- **AND** the output payload includes runtime outcome fields sufficient for audit and replay decisions

#### Scenario: Skill step failure contract
- **WHEN** a skill step fails in an external agent runtime
- **THEN** the client reports failure using the returned `stepId`
- **AND** the error payload includes an error code/category and human-readable failure context
