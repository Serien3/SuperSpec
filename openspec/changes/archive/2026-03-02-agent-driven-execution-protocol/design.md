## Context

The previous direct-run model did not cleanly model skill-driven actions that require an Agent runtime boundary, conversational context, and explicit handoff semantics.

To support reliable Agent orchestration, execution should become pull-based: the engine decides what is next, while an Agent fetches one action at a time, executes it, and reports the outcome back.

## Goals / Non-Goals

**Goals:**
- Define a command-level execution protocol: `next`, `complete`, `fail`, and `status`.
- Introduce lease-based action claiming to prevent duplicate execution under concurrency.
- Define structured action payloads for both `script` and `skill` executors.
- Keep execution resumable and auditable with explicit state/event persistence.
- Define protocol mode as the only execution path in `v1.0.0` (`next`, `complete`, `fail`, `status`).

**Non-Goals:**
- Implement distributed scheduling across multiple repositories.
- Introduce full parallel DAG dispatch in this increment.
- Build a full policy engine for prompt generation.
- Replace OpenSpec artifact workflow semantics.

## Decisions

### Decision 1: Pull-based execution protocol
Introduce `superspec next <change> --json` to return exactly one runnable action at a time.

Rationale:
- Keeps scheduling authority in engine.
- Keeps execution authority in agent.
- Improves observability and recoverability across step boundaries.

Alternatives considered:
- Engine-push to external worker. Rejected due to delivery complexity and weaker interactive control.

### Decision 2: Explicit result reporting commands
Add `complete` and `fail` commands to advance state only from explicit reported outcomes.

Rationale:
- Prevents implicit success assumptions.
- Enables deterministic retry/onFail semantics with clear event history.

Alternatives considered:
- Auto-advance on process exit code from `next` execution wrapper. Rejected as too implicit and fragile for skill actions.

### Decision 3: Lease token for action claim safety
`next` issues a lease token; `complete/fail` must present same token.

Rationale:
- Prevents duplicate completion from concurrent agents.
- Enables safe re-claim after lease timeout.

Alternatives considered:
- No lease model. Rejected due to race conditions and non-idempotent behavior.

### Decision 4: Skill actions return references, not full prompt by default
For `executor=skill`, engine returns skill reference (`name`, `version`, `input`, `contextFiles`) and optional debug prompt only in debug mode.

Rationale:
- Reduces token/log noise.
- Keeps prompt templates versioned outside runtime payload.
- Improves security posture for internal system prompts.

Alternatives considered:
- Always return full rendered prompt. Rejected for verbosity, leakage risk, and maintenance friction.

## Risks / Trade-offs

- [Risk] Lease expiry creates ambiguous ownership during slow runs. → Mitigation: TTL + heartbeat/renew command in future increment.
- [Risk] `complete/fail` payload schema drift across agents. → Mitigation: define strict JSON schema and reject unknown contract versions.
- [Risk] Agents submit malformed completion/failure payloads. → Mitigation: strict JSON object validation and deterministic protocol errors.
- [Risk] Skill execution remains externally dependent. → Mitigation: preserve script actions as fallback and make skill errors explicit and recoverable.
