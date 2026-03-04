## Why

`workflow.schema.json` and the current SuperSpec implementation diverge on which `workflow.json` template customization fields are allowed and how they behave. This creates confusion for users, inconsistent validation outcomes, and higher maintenance cost when adding or using custom workflows.

## What Changes

- Align schema contract and runtime behavior for workflow template customization so they accept the same fields and enforce the same constraints.
- Narrow customization scope to a small, explicit set of supported template fields and reject undefined or ambiguous customization fields.
- Make merge and precedence behavior explicit and deterministic for supported template customization fields.
- Improve validation and error messages so unsupported customization fields fail fast with actionable guidance.
- Update documentation/examples in workflow artifacts so authored templates match actual runtime behavior.

## Capabilities

### New Capabilities
- `workflow-template-customization-alignment`: Define a single, simplified contract for supported workflow template customization fields and required runtime behavior.

### Modified Capabilities
- `plan-scheme-management`: Tighten workflow file validation rules so accepted customization fields are exactly those defined by the schema contract.
- `plan-generation-from-scheme`: Clarify and enforce deterministic rendering behavior for supported customization fields, including conflict resolution and rejection rules.

## Impact

- Affected code: workflow schema definitions under `src/superspec/schemas/`, workflow loading/validation logic, and plan rendering/merge logic under `src/superspec/engine/`.
- Affected behavior: custom workflow authoring and `plan init --schema <name>` validation/rendering outcomes.
- Affected tests: schema validation tests, plan generation precedence tests, and integration tests for custom workflows.
