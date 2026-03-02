## ADDED Requirements

### Requirement: Simplified single-agent starter template
The system MUST provide a default plan template optimized for single-agent, single-process, serial execution.

#### Scenario: Initialize simplified default plan
- **WHEN** a user initializes a plan in the default mode
- **THEN** the generated template expresses a serial action flow suitable for one agent
- **AND** excludes lease-oriented or concurrency-oriented starter fields

### Requirement: Single-agent execution assumption
The system MUST define current plan execution baseline as exclusive single-agent, single-process orchestration.

#### Scenario: Protocol contract reflects single-agent baseline
- **WHEN** users read generated plan guidance and execution docs
- **THEN** the documented contract matches single-agent serial execution behavior
- **AND** does not require lease ownership semantics in the baseline workflow

## MODIFIED Requirements

### Requirement: Unified action execution contract
The system MUST support both `skill` and `script` executors using a shared action contract with normalized outputs under serial single-agent execution.

#### Scenario: Skill executor action
- **WHEN** an action declares `executor: skill`
- **THEN** the execution protocol returns a skill execution payload for an external agent
- **AND** stores normalized outputs only after explicit completion reporting

#### Scenario: Script executor action
- **WHEN** an action declares `executor: script`
- **THEN** the execution protocol returns script command payload for execution
- **AND** stores normalized outputs only after explicit completion reporting
