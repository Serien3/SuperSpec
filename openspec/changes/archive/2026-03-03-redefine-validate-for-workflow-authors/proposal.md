## Why

`superspec plan validate` currently validates generated `plan.json`, which is useful for runtime debugging but not for workflow authors. Users defining custom `*.workflow.json` need a human-facing validator that explicitly checks allowed fields, field shapes, and plan-generation readiness before they run `plan init`.

## What Changes

- **BREAKING**: Redefine `superspec validate` to validate workflow templates for human authors, replacing the old "validate change plan.json" semantics.
- Add a strict workflow validation contract that explicitly defines all supported top-level and nested workflow fields, with unknown-field rejection.
- Require validation to cover both structural schema correctness and generation-readiness (including semantic checks such as dependency references and actionable executor constraints).
- Add machine-readable and human-readable error output with precise field paths and actionable guidance.
- Update CLI docs/help text so `validate` is documented as workflow-author tooling.

## Capabilities

### New Capabilities
- `workflow-validation-command`: Human-facing `superspec validate` command that validates user-defined workflow templates and reports format/contract errors clearly.

### Modified Capabilities
- `plan-scheme-management`: Tighten and document explicit workflow template field contract for user-defined workflow files.
- `workflow-template-customization-alignment`: Align strict schema validation and runtime acceptance under one finite supported field surface.

## Impact

- Affected code: CLI command routing/help, workflow schema and loader validation path, related tests.
- Affected contracts: command semantics for `validate`, workflow schema strictness, error payload conventions.
- Docs: `docs/cli.md` and workflow authoring guidance in README/related docs.
