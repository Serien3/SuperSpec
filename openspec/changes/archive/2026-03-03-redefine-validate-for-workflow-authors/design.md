## Context

SuperSpec currently exposes `superspec plan validate <change>` to validate generated `plan.json`. This serves agent/runtime protocol checks, but it does not serve workflow authors who need to validate `*.workflow.json` before plan generation.

At the same time, workflow schema validation is partly strict at top-level and partly permissive in nested objects (`defaults`, `steps`), which allows authoring mistakes to pass schema checks and fail later during plan generation or execution.

This change re-centers `validate` as a human authoring command: validate workflow templates against an explicit, finite, generation-ready contract.

## Goals / Non-Goals

**Goals:**
- Redefine `superspec validate` as a workflow-template validation command for human authors.
- Enforce explicit field contract for workflow files (top-level + nested fields) with unknown-field rejection.
- Validate both structure and generation-readiness so a passing workflow is suitable input for `superspec plan init`.
- Return actionable diagnostics in both human-readable and machine-readable forms.

**Non-Goals:**
- Changing protocol runtime state machine (`next/complete/fail/status`) semantics.
- Adding new workflow execution primitives beyond current plan/step model.
- Backward-compat shims that preserve old `superspec plan validate` behavior.

## Decisions

### Decision 1: Replace command semantics with a dedicated workflow-author contract
- New command meaning: `superspec validate` validates workflow templates, not change plans.
- Primary input mode: `--schema <name>` resolves `superspec/schemas/workflows/<name>.workflow.json` (with packaged fallback consistent with existing loader behavior).
- Optional input mode: `--file <path>` validates an explicit workflow file path.
- Rationale: aligns command intent with human workflow-author usage and removes ambiguity.
- Alternative considered: keep `plan validate` and add `workflow validate`. Rejected because user intent is to repurpose `validate` directly and remove old semantics.

### Decision 2: Three-stage validation pipeline
Validation SHALL execute in fixed order:
1. **Schema structure validation** against strict `workflow.schema.json`.
2. **Semantic validation** for graph and step constraints (e.g., dependency references, cycle detection, executor/field compatibility).
3. **Generation-readiness validation** by attempting deterministic render path checks required for `plan init` (without writing plan files).

Rationale: author sees earliest precise failure while guaranteeing a "pass" outcome is actually usable for plan generation.

### Decision 3: Strict finite field surface for workflow templates
- Tighten `workflow.schema.json` to explicit nested properties with `additionalProperties: false` on constrained objects (notably `defaults`, `defaults.retry`, `steps[*]`, `steps[*].retry`).
- Keep extensibility only where intentionally allowed and documented.
- Rationale: avoid silent acceptance of misspelled or unsupported fields.

### Decision 4: Structured diagnostics contract
- Human mode (default): concise error summary with path and fix hint.
- JSON mode (`--json`):
  - `ok: boolean`
  - `errors: [{code, path, message, hint}]`
  - optional `warnings`
- Error paths use stable dot notation for machine tooling.

Rationale: supports both CLI users and automated pre-commit/CI checks.

### Decision 5: Breaking migration strategy
- Document as breaking CLI behavior change.
- Update help/docs/examples to show `superspec validate --schema ...` as author workflow.
- Tests rewritten to assert new behavior; obsolete tests for plan.json validation removed/replaced.

## Risks / Trade-offs

- **[Risk] Existing users relying on `plan validate` semantics break** -> Mitigation: explicit BREAKING note in docs/changelog and clear command help text.
- **[Risk] Overly strict schema blocks previously tolerated workflows** -> Mitigation: provide precise path-level errors and a complete field contract table in docs.
- **[Risk] Duplicate validation logic between schema and semantic checks** -> Mitigation: centralize semantic checks in workflow loader validation path and reuse from CLI.
- **[Risk] Ambiguity when both `--schema` and `--file` are provided** -> Mitigation: define deterministic argument rule (mutually exclusive) and fail fast.

## Migration Plan

1. Introduce new `superspec validate` parser and handler for workflow validation input (`--schema`/`--file`).
2. Refactor workflow validation internals into reusable function returning structured diagnostics.
3. Tighten `workflow.schema.json` nested fields to explicit contract.
4. Add/update tests for command parsing, success cases, strict rejection cases, and JSON diagnostics.
5. Update CLI and workflow authoring documentation; call out breaking command semantic change.

## Open Questions

- Should validation warnings include "deprecated but accepted" fields, or should all unsupported fields be hard failures from day one?
- Should packaged workflow fallback be enabled for `--schema` in validate mode, or should author mode only validate local project files?
- Should `superspec validate` default schema be `SDD` when no argument is passed, or require explicit `--schema/--file` to avoid accidental validation target confusion?
