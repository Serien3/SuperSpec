## Context

SuperSpec protocol execution currently supports `script` and `skill` executors. Workflow and validator schemas reject any third executor type, and protocol payload generation assumes non-script actions are `skill` actions. Teams need a workflow-native pause point for human review between automated steps while preserving existing pull-loop semantics.

The existing runtime already supports this execution shape: `next` marks one action `RUNNING`, subsequent `next` calls return `blocked`, and execution resumes after a `complete` or `fail` report. This lets us add a human-gated action without introducing a new protocol command.

## Goals / Non-Goals

**Goals:**
- Add first-class `human` executor support in workflow schema, plan validation, and protocol action payloads.
- Represent human review as a normal running action that is finalized by existing `complete`/`fail` commands.
- Keep existing `skill` and `script` behaviors unchanged and backward compatible.
- Document agent-loop dispatch rules for `human` executor.

**Non-Goals:**
- Add new protocol commands like `approve`/`reject`.
- Add asynchronous external approval services or notifications.
- Redesign action state machine or add new terminal/intermediate states.

## Decisions

1. Add `human` to executor enums in workflow schema and protocol contracts.
- Rationale: keeps executor model explicit and self-describing.
- Alternative considered: encode human review as `skill` with specific skill name; rejected because it hides semantics and weakens validation.

2. Reuse current lifecycle (`next -> RUNNING -> complete|fail`) for human actions.
- Rationale: zero state-machine expansion, minimal risk.
- Alternative considered: add dedicated approval state and commands; rejected as unnecessary protocol complexity.

3. Add structured `human` action payload in `next` response.
- Fields: `executor=human`, `prompt`, and `human` object from action definition (for example `instruction`, `approveLabel`, `rejectLabel`).
- Rationale: UI/agent can render clear human instructions without schema-free conventions.

4. Keep completion/failure report schema generic.
- Rationale: `complete` and `fail` already accept object payloads; no command-level branching needed.

5. Update execution playbook docs to dispatch `human` as “wait for human feedback then report complete/fail”.
- Rationale: keeps operator behavior aligned with protocol support.

## Risks / Trade-offs

- [Risk] Human action payload may be under-specified for some workflows. -> Mitigation: validate `human` object type and require at least `instruction` string for executor `human`.
- [Risk] Existing automation loops may ignore unknown executor. -> Mitigation: update bundled loop skills and contracts to include explicit `human` branch.
- [Trade-off] Reusing complete/fail means no approval-specific ergonomics. -> Accepted for v1 to avoid redundant command surface.

## Migration Plan

1. Extend schema and validator to accept `human` executor payloads.
2. Extend protocol payload generation and contract metadata.
3. Update loop skill guidance for executor dispatch.
4. Add integration and lifecycle tests for `human` executor success/failure flows.
5. Validate with targeted and full unit tests.

Rollback strategy: revert enum and protocol payload changes; existing `skill`/`script` flows remain unchanged.

## Open Questions

- Should `human` action payload later require a canonical decision field (`approved: true|false`) in completion output for analytics consistency?
- Should timeout/escalation behavior for unattended human actions be introduced as a future retry/onFail policy extension?
