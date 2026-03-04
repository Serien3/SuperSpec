## Context

The protocol CLI currently resolves `plan.json` using the CLI change name but then trusts `plan.context.changeDir` for runtime state location. This allows a malformed plan to redirect state writes to another change directory under `openspec/changes`. In parallel, plan validation does not reject unknown executor values, so runtime can emit payloads that violate expected executor contracts.

## Goals / Non-Goals

**Goals:**
- Bind protocol execution directory to the same change requested by CLI.
- Reject invalid explicit executor values (`skill|script|human` only) during plan validation.
- Preserve backward-compatible behavior for valid plans.
- Add regression tests for both protections.

**Non-Goals:**
- Introduce locking/atomic write changes in this change set.
- Alter fail-fast semantics or runtime action scheduling logic.
- Redesign protocol payload schema beyond executor validation hardening.

## Decisions

1. Add a strict consistency check in orchestration startup:
- Compare canonical change dir resolved from CLI `change_name` with resolved `plan.context.changeDir`.
- If mismatch, raise `ProtocolError(code="invalid_path")` with details for expected vs actual paths.

Rationale:
- Fastest and least invasive way to prevent cross-change state writes.
- Reuses existing path canonicalization and safety checks in `plan_loader`.

Alternative considered:
- Ignore `context.changeDir` and always derive runtime dir from CLI change.
  - Rejected because existing code intentionally keeps plan context as runtime source of truth; a strict equality guard preserves intent while closing safety gap.

2. Enforce executor enum/type at plan validation layer:
- If `executor` field exists, require it to be a non-empty string and one of `skill`, `script`, `human`.
- Keep existing executor-specific payload checks (`skill` requires `skill`, etc.).

Rationale:
- Prevents contract-breaking runtime payloads before protocol starts.
- Keeps behavior deterministic and aligned with documented protocol contract.

Alternative considered:
- Add runtime fallback/coercion for unknown executor.
  - Rejected because silent coercion can hide malformed plans and produce confusing action payloads.

## Risks / Trade-offs

- [Risk] Some previously tolerated malformed plans will now fail early.
  → Mitigation: return explicit validation/path error codes and add tests to document new expectations.

- [Risk] Existing tooling that mutates `context.changeDir` for experimentation may break.
  → Mitigation: this is an intentional hardening boundary; update tooling to keep CLI change and context aligned.

## Migration Plan

1. Implement guard in orchestrator before action dispatch.
2. Implement strict executor validation in plan validator.
3. Add regression tests for mismatch and invalid executor cases.
4. Run full unit test suite and release with changelog note: malformed plans are now rejected earlier.

## Open Questions

- Should future versions fully derive runtime path from CLI change and treat `context.changeDir` as informational only?
- Should we add a dedicated validator error code taxonomy (e.g., `invalid_executor`) instead of generic validation messages?
