# workflow-schema-management Specification

## Purpose
Define file-based workflow definitions for runtime snapshot generation, including identity, validation, and extensibility requirements.

## Requirements

### Requirement: File-based workflow definitions
The system MUST support declarative workflow files that define workflow metadata and step sequence content.

#### Scenario: Load a valid workflow file
- **WHEN** a user requests change creation with `change advance --new <schema>/<change-name>` and the schema exists in the configured workflow directory
- **THEN** the system loads that workflow definition
- **AND** uses its metadata and steps as generation input

#### Scenario: Discover workflow in default filesystem location
- **WHEN** a user adds a valid workflow file under `superspec/schemas/workflows/` using the `<schema>.workflow.json` naming pattern
- **THEN** the workflow is discoverable by `change advance --new <schema>/<change-name>`
- **AND** no SuperSpec source code changes are required

#### Scenario: Project-local workflow overrides packaged workflow of same name
- **WHEN** a workflow file exists at both `superspec/schemas/workflows/<schema>.workflow.json` and the packaged built-in workflow directory
- **THEN** the system resolves the project-local workflow first
- **AND** uses the packaged copy only when no project-local file exists

### Requirement: Workflow identity and metadata validation
The system MUST validate required workflow metadata fields and workflow template customization fields before using a workflow for generation, and MUST enforce an explicit finite set of supported fields at both top-level and constrained nested objects.

#### Scenario: Reject workflow missing required metadata
- **WHEN** a workflow definition is missing required identity metadata such as `workflowId`
- **THEN** change initialization fails with a clear validation error
- **AND** no `execution/state.json` is generated

#### Scenario: Reject unsupported template customization field
- **WHEN** a workflow definition includes a template customization field that is not in the supported schema contract
- **THEN** change initialization fails with a clear validation error that includes the unsupported path
- **AND** no `execution/state.json` is generated

#### Scenario: Reject unknown nested field in constrained workflow object
- **WHEN** a workflow definition includes an unknown field under constrained objects such as `steps[*]`
- **THEN** validation fails before runtime baseline generation
- **AND** the error identifies the precise nested path

### Requirement: User-defined workflow extensibility
The system MUST allow users to add new workflow files without modifying SuperSpec source code.

#### Scenario: Use a newly added custom workflow
- **WHEN** a user adds a new valid workflow file to the supported workflow directory
- **THEN** that workflow becomes selectable for subsequent `change advance --new` calls
- **AND** the system can generate a valid runtime baseline from it

### Requirement: Built-in workflow forking
The CLI MUST let users clone a packaged built-in workflow into the current project's local workflow directory so they can customize it without editing SuperSpec source files.

#### Scenario: Fork built-in workflow into project-local workflow directory
- **WHEN** a user runs `superspec workflow fork spec-dev my-spec-dev`
- **THEN** the system copies the packaged `spec-dev` workflow into `superspec/schemas/workflows/my-spec-dev.workflow.json`
- **AND** the resulting file becomes selectable by `change advance --new my-spec-dev/<change-name>`

#### Scenario: Reject fork when target workflow already exists
- **WHEN** a user runs `superspec workflow fork <builtin> <custom>`
- **AND** `superspec/schemas/workflows/<custom>.workflow.json` already exists
- **THEN** the command fails with a structured error
- **AND** does not overwrite the existing project-local workflow

#### Scenario: Reject fork for unknown built-in workflow
- **WHEN** a user runs `superspec workflow fork missing-flow my-flow`
- **THEN** the command fails with a structured error indicating the built-in workflow is unknown
