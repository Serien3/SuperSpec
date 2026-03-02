# plan-scheme-management Specification

## Purpose
TBD - created by archiving change decouple-plan-template-and-schemes. Update Purpose after archive.
## Requirements
### Requirement: File-based scheme definitions
The system MUST support declarative plan scheme files that define scheme metadata, defaults, and action sequence content.

#### Scenario: Load a valid scheme file
- **WHEN** a user requests plan initialization with a scheme name that exists in the configured scheme directory
- **THEN** the system loads that scheme definition
- **AND** uses its metadata, defaults, and actions as generation input

### Requirement: Scheme identity and metadata validation
The system MUST validate required scheme metadata fields before using a scheme for generation.

#### Scenario: Reject scheme missing required metadata
- **WHEN** a scheme definition is missing required identity metadata such as scheme id or version
- **THEN** plan initialization fails with a clear validation error
- **AND** no plan file is generated

### Requirement: User-defined scheme extensibility
The system MUST allow users to add new scheme files without modifying SuperSpec source code.

#### Scenario: Use a newly added custom scheme
- **WHEN** a user adds a new valid scheme file to the supported scheme directory
- **THEN** that scheme becomes selectable for subsequent plan initialization
- **AND** the system can generate a valid plan from it

