## MODIFIED Requirements

### Requirement: Unified action execution contract
The system MUST support both `skill` and `script` executors using a shared action contract with normalized outputs under serial single-agent execution.

#### Scenario: Skill executor action
- **WHEN** an action declares `executor: skill`
- **THEN** the execution protocol returns a skill action payload containing `skillName` and `prompt`
- **AND** stores normalized outputs only after explicit completion reporting

#### Scenario: Script executor action
- **WHEN** an action declares `executor: script`
- **THEN** the execution protocol returns a script action payload containing `scriptName` and `prompt`
- **AND** stores normalized outputs only after explicit completion reporting

#### Scenario: Inherit executor from plan defaults
- **WHEN** an action omits explicit `executor`, `script`, and `skill` fields
- **THEN** the execution protocol resolves executor type from effective plan defaults
- **AND** returns a payload shape consistent with the resolved executor type
