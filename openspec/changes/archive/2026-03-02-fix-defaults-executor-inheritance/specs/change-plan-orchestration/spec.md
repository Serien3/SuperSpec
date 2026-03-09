## MODIFIED Requirements

### Requirement: Unified step execution contract
The system MUST support both `skill` and `script` executors using a shared step contract with normalized outputs under serial single-agent execution.

#### Scenario: Skill executor step
- **WHEN** an step declares `executor: skill`
- **THEN** the execution protocol returns a skill step payload containing `skillName` and `prompt`
- **AND** stores normalized outputs only after explicit completion reporting

#### Scenario: Script executor step
- **WHEN** an step declares `executor: script`
- **THEN** the execution protocol returns a script step payload containing `scriptName` and `prompt`
- **AND** stores normalized outputs only after explicit completion reporting

#### Scenario: Inherit executor from plan defaults
- **WHEN** an step omits explicit `executor`, `script`, and `skill` fields
- **THEN** the execution protocol resolves executor type from effective plan defaults
- **AND** returns a payload shape consistent with the resolved executor type
