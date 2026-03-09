## Context

SuperSpec currently supports retry scheduling (`maxAttempts`, `intervalSec`) and optional continuation behavior after failure. This requires extra state (`attempts`, `nextEligibleAt`), retry-focused status payloads, and loop logic for blocked polling. The user goal is to simplify the model to a strict fail-fast contract where failure is always terminal and human intervention is explicit.

## Goals / Non-Goals

**Goals:**
- Make failure handling deterministic: one reported step failure ends the workflow.
- Remove retry policy surfaces from runtime config and status contracts.
- Keep step lifecycle and status payload simple for both humans and agents.
- Align skills/docs with a human-escalation model.

**Non-Goals:**
- Add automatic human notification integrations.
- Redesign executor payload formats beyond failure semantics.
- Introduce partial-success workflow branches after failure.

## Decisions

1. Immediate terminal failure on `plan fail`
- Decision: `fail_action` always sets step state to `FAILED`, sets run status to `failed`, and sets `finishedAt` immediately.
- Rationale: deterministic behavior and immediate escalation.
- Alternative: keep `onFail` policies; rejected as unnecessary policy branching.

2. Remove retry runtime state usage
- Decision: drop retry scheduling logic and retry-only status payload mode.
- Rationale: simplifies protocol and avoids blocked polling loops as recovery mechanism.
- Alternative: keep retry fields but ignore them; rejected because it leaves misleading API surface.

3. Preserve dependency-failure propagation for terminal consistency
- Decision: keep downstream dependency failure propagation once root failure occurs.
- Rationale: ensures each pending dependent gets explicit terminal failed context.
- Alternative: stop without propagation; rejected because status would leave ambiguous pending states.

4. Simplify configuration/contract surfaces
- Decision: remove retry fields from plan schema and defaults constants; remove retry mode from CLI/status contracts/docs.
- Rationale: make API reflect actual behavior with no dead knobs.

## Risks / Trade-offs

- [Risk] Existing plans that include `retry` fields will fail validation.
  Mitigation: update workflow templates and provide clear migration note in docs.

- [Risk] Transient execution issues will now require human restart instead of auto-retry.
  Mitigation: document operational expectation and surface explicit failure details.

- [Risk] Existing loop skills may still poll blocked+retry paths.
  Mitigation: update bundled skill instructions in both source and packaged copies.

## Migration Plan

1. Update capability specs to define fail-fast semantics and remove retry contract.
2. Remove retry fields from schema/constants and delete retry behavior in protocol.
3. Remove `--retry` status option and retry payload contract/docs.
4. Update tests and skill docs for new failure model.
5. Validate full test suite.

## Open Questions

- Should future versions add a dedicated `escalated` metadata field in status payload for UIs, or is `status=failed` plus `lastFailure` sufficient?
