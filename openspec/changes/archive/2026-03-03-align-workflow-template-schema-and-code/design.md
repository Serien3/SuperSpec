## Context

SuperSpec currently allows workflow template customization through `workflow.json`, but the accepted fields and behavior are not fully aligned between `workflow.schema.json` and runtime merge/validation logic. Users can author workflows that pass one layer (schema or code) but fail or behave differently in the other. The change should reduce ambiguity and keep customization intentionally small.

Mismatch audit (before this change):
- Schema allowed unknown top-level fields (`additionalProperties: true`), but runtime only consumed a limited subset.
- Runtime accepted legacy `plan` overlay semantics while schema did not constrain its shape, allowing ambiguous nested customizations.
- Authors could provide fields like `context` that schema accepted but runtime ignored, producing silent no-op behavior.

## Goals / Non-Goals

**Goals:**
- Define one authoritative set of supported template customization fields.
- Ensure schema validation and runtime validation enforce the same contract.
- Keep rendering behavior deterministic with explicit precedence and protected fields.
- Fail fast on unsupported customization with clear errors.

**Non-Goals:**
- Introducing a broad plugin-like templating system.
- Supporting arbitrary deep customization across all plan fields.
- Changing change-bound context rules (`changeName`, `changeDir`) to be overridable.

## Decisions

### Decision 1: Introduce a strict, minimal customization surface
Only a small whitelist of template customization fields is supported in `workflow.json` (the exact set is defined in schema and mirrored in runtime constants). Unknown fields are rejected during validation.

Alternative considered:
- Allow permissive additional properties and ignore unknown fields.
Why not:
- Silent ignore leads to user confusion and hidden misconfiguration.

### Decision 2: Single source of truth for allowed fields and structural shape
`workflow.schema.json` remains the author-facing contract, while runtime validation imports or mirrors the same allowed field list and type expectations in one centralized validation module. This avoids independent drift across code paths.

Alternative considered:
- Keep schema and runtime checks separate and rely on tests only.
Why not:
- Drift has already occurred; tests alone are insufficient without shared constraints.

### Decision 3: Deterministic merge strategy with protected context
Plan generation applies a fixed merge order for supported customization fields: base template < workflow defaults/customization. Protected change context fields always win from active change context and cannot be overridden.

Alternative considered:
- Per-field ad-hoc precedence rules.
Why not:
- Hard to reason about and increases maintenance complexity.

### Decision 4: User-facing errors prioritize actionable remediation
Validation errors include the unsupported field path and expected supported fields, so users can quickly update `workflow.json`.

Alternative considered:
- Generic validation failures.
Why not:
- Slows debugging and increases support burden.

## Risks / Trade-offs

- [Risk] Existing custom workflows may rely on previously tolerated unsupported fields.  
  Mitigation: Provide explicit error messages and a migration note describing the new supported set.

- [Risk] Tight alignment may require touching both schema and engine modules, increasing chance of partial updates.  
  Mitigation: Add tests that assert schema acceptance and runtime behavior for the same sample workflows.

- [Trade-off] Reduced flexibility for advanced custom templates.  
  Mitigation: Keep initial scope narrow; extend later only with explicit spec-backed requirements.

## Migration Plan

1. Define/confirm the allowed customization field set and encode it in schema.
2. Refactor runtime workflow validation to enforce the same set and reject unknown fields.
3. Align plan rendering merge logic and protected field handling with documented precedence.
4. Add/adjust tests for valid customizations, unknown fields, and precedence behavior.
5. Document migration guidance for existing workflow authors.

Rollback:
- Revert schema and runtime validation changes together to avoid split-brain behavior.

## Open Questions

- Should migration guidance be embedded in CLI error output directly, or only in docs/spec notes?
- Do we need a compatibility flag for one release cycle, or enforce strict mode immediately?
