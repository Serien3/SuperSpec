## Context

SuperSpec protocol payload construction currently resolves executor type with a fallback chain that omits plan-level defaults during payload shaping. The state already stores merged defaults (`DEFAULTS + plan.defaults`), but payload code uses `DEFAULTS + step.defaults` instead, creating divergence between configured plan behavior and dispatched executor payloads.

## Goals / Non-Goals

**Goals:**
- Ensure executor selection for payload generation respects plan-level defaults when an step does not provide explicit executor fields.
- Add integration coverage for the no-explicit-executor case.
- Preserve existing behavior for explicit `executor`, `script`, or `skill` declarations.

**Non-Goals:**
- No change to retry, dependency, or failure-policy semantics.
- No new executor types or CLI flags.

## Decisions

- Update payload builder wiring to consume effective runtime defaults from protocol state (already merged during state initialization), not ad-hoc defaults from step-local fields.
- Keep `_resolve_executor` precedence unchanged: explicit `executor` > inferred from `script`/`skill` > provided defaults.
- Add a regression test that builds a plan with `defaults.executor=script` and an step with only `id` + `type`, then asserts returned payload executor is `script` and includes `scriptName`.

## Risks / Trade-offs

- [Risk] Existing tests may implicitly rely on current fallback behavior in edge cases.  
  Mitigation: Add targeted test coverage and run full test suite.
- [Risk] If plan defaults are malformed, behavior might still fail at runtime.  
  Mitigation: Existing plan validation constraints remain the guardrail.
