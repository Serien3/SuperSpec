## Why

Current workflow field definitions are hard to learn and hard to extend because executor configuration is split across mixed styles (explicit executor vs inferred payload fields). This causes author confusion and validation ambiguity, and slows down custom workflow adoption.

## What Changes

- Define a strict minimal workflow contract with explicit required fields at top-level and action-level.
- Require explicit `executor` on every action and enforce exactly-one matching executor payload (`skill`/`script`/`human`).
- Keep readability-oriented fields as optional annotations, clearly separated from execution-critical fields.
- Tighten workflow validation so contract violations fail early with stable error codes and field paths.
- Update default workflow templates and tests to use the normalized contract.
- **BREAKING**: remove executor inference-based authoring style; workflows must provide explicit executor and matching payload.

## Capabilities

### New Capabilities
- `workflow-core-contract-normalization`: Define a core-vs-annotation field model for workflow templates and enforce it consistently in schema and runtime validation.

### Modified Capabilities
- `workflow-template-customization-alignment`: Narrow customization/authoring surface to the normalized field contract and reject mixed executor styles.
- `workflow-validation-command`: Extend validation diagnostics to cover explicit core-contract violations (required fields, mutually exclusive executor payloads).

## Impact

- Affected files: `src/superspec/schemas/workflow.schema.json`, `src/superspec/engine/workflow_loader.py`, default workflow templates under `src/superspec/schemas/workflows/`, and related tests.
- Validation behavior changes for workflow authors (stricter and less ambiguous).
- Existing non-normalized workflow files in downstream repos will need migration before they can pass validation.
