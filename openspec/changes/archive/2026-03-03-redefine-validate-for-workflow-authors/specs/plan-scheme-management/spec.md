## MODIFIED Requirements

### Requirement: Workflow identity and metadata validation
The system MUST validate required workflow metadata fields and workflow template customization fields before using a workflow for generation, and MUST enforce an explicit finite set of supported fields at both top-level and constrained nested objects.

#### Scenario: Reject workflow missing required metadata
- **WHEN** a workflow definition is missing required identity metadata such as `workflowId` or `version`
- **THEN** plan initialization fails with a clear validation error
- **AND** no plan file is generated

#### Scenario: Reject unsupported template customization field
- **WHEN** a workflow definition includes a template customization field that is not in the supported schema contract
- **THEN** validation fails with a clear validation error that includes the unsupported path
- **AND** no plan file is generated

#### Scenario: Reject unknown nested field in constrained workflow object
- **WHEN** a workflow definition includes an unknown field under constrained objects such as `defaults` or `steps[*]`
- **THEN** validation fails before plan generation
- **AND** the error identifies the precise nested path
