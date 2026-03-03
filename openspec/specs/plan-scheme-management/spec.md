# plan-scheme-management Specification

## Purpose
Define file-based workflow definitions for plan generation, including identity, validation, and extensibility requirements.

## Requirements

### Requirement: File-based workflow definitions
The system MUST support declarative workflow files that define workflow metadata, defaults, and action sequence content.

#### Scenario: Load a valid workflow file
- **WHEN** a user requests plan initialization with a schema name that exists in the configured workflow directory
- **THEN** the system loads that workflow definition
- **AND** uses its metadata, defaults, and actions as generation input

#### Scenario: Discover workflow in default filesystem location
- **WHEN** a user adds a valid workflow file under `superspec/schemas/workflows/` using the `<schema>.workflow.json` naming pattern
- **THEN** the workflow is discoverable by `plan init --schema <schema>`
- **AND** no SuperSpec source code changes are required

### Requirement: Workflow identity and metadata validation
The system MUST validate required workflow metadata fields and workflow template customization fields before using a workflow for generation, and MUST enforce an explicit finite set of supported fields at both top-level and constrained nested objects.

#### Scenario: Reject workflow missing required metadata
- **WHEN** a workflow definition is missing required identity metadata such as `workflowId` or `version`
- **THEN** plan initialization fails with a clear validation error
- **AND** no plan file is generated

#### Scenario: Reject unsupported template customization field
- **WHEN** a workflow definition includes a template customization field that is not in the supported schema contract
- **THEN** plan initialization fails with a clear validation error that includes the unsupported path
- **AND** no plan file is generated

#### Scenario: Reject unknown nested field in constrained workflow object
- **WHEN** a workflow definition includes an unknown field under constrained objects such as `defaults` or `actions[*]`
- **THEN** validation fails before plan generation
- **AND** the error identifies the precise nested path

### Requirement: User-defined workflow extensibility
The system MUST allow users to add new workflow files without modifying SuperSpec source code.

#### Scenario: Use a newly added custom workflow
- **WHEN** a user adds a new valid workflow file to the supported workflow directory
- **THEN** that workflow becomes selectable for subsequent plan initialization
- **AND** the system can generate a valid plan from it
