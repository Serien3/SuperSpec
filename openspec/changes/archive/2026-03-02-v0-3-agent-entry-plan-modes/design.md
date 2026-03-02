## Context

SuperSpec v0.2 has the protocol primitives (`next`, `complete`, `fail`, `status`) but leaves loop execution and skill runtime wiring to external agents without a standardized execution playbook. In parallel, current plan initialization behavior is effectively single-template and tightly coupled with `change new`, which conflicts with an explicit lifecycle of `new change -> select plan mode -> validate -> execute`.

This v0.3 iteration introduces a clear entry architecture:
- SuperSpec protocol engine remains the source of truth for state, leases, retries, and terminal status.
- Agent guidance (skill and/or AGENT.md) becomes the execution entrypoint contract that repeatedly drives protocol commands and executor dispatch.
- Plan initialization becomes mode-aware and explicit, starting with `sdd`.

## Goals / Non-Goals

**Goals:**
- Provide explicit agent guidance for end-to-end plan execution.
- Define stable handling for skill action execution outcomes reported back to protocol.
- Support mode-based plan initialization with an extensible mode registry (initially `sdd`).
- Clarify lifecycle separation between change creation and plan creation.

**Non-Goals:**
- Parallel DAG execution or multi-agent scheduling.
- Cross-change orchestration in a single run.
- Defining non-SDD plan semantics in this increment.
- Replacing external skill runtimes with an embedded orchestrator.

## Decisions

### 1) Keep protocol engine pure; define guidance at boundary
- Decision: retain current protocol engine responsibilities and define a standardized agent guidance artifact (skill and/or AGENT.md) that specifies polling, dispatch, and report calls.
- Why: keeps state machine logic isolated while delivering an immediately usable entrypoint across agent runtimes.
- Alternatives considered:
  - Put execution logic directly into `next`/protocol path: rejected due to tighter coupling and reduced debuggability.
  - Build an internal runner command first: deferred to future version to prioritize speed and flexibility.

### 2) Enforce executor boundary in guidance contract
- Decision: guidance explicitly states that `executor=script` and `executor=skill` are dispatched by the agent runtime; both map to normalized complete/fail report payloads.
- Why: aligns with existing payload contract and supports heterogeneous runtimes without over-constraining implementation language.
- Alternatives considered:
  - Treat skill actions as no-op placeholders: rejected because it prevents reliable end-to-end automation.
  - Force all actions into scripts: rejected because it weakens semantic intent and skill portability.

### 3) Introduce mode-keyed plan template resolution
- Decision: `plan init --mode <mode>` resolves a template from a registry, with `sdd` as the initial supported mode.
- Why: avoids hardcoded template behavior and creates a stable extension point for future workflows.
- Alternatives considered:
  - Keep single static `plan.template.json`: rejected because it blocks product-level workflow evolution.
  - Allow arbitrary inline templates at init time only: rejected in v0.3 to preserve consistency and validation control.

### 4) Make plan lifecycle explicit
- Decision: change creation and plan initialization are treated as separate lifecycle steps; protocol commands require an initialized plan.
- Why: matches expected user workflow and improves predictability when multiple plan modes are available.
- Alternatives considered:
  - Implicitly auto-create plan on `change new`: rejected because it hides mode selection and causes default coupling.

## Risks / Trade-offs

- [Risk] Agent implementations may apply inconsistent retry logic. -> Mitigation: guidance states retry authority remains in protocol state; agent reports one attempt outcome per lease.
- [Risk] Skill runtime payload diversity may produce inconsistent failure metadata. -> Mitigation: define minimum required error fields and normalize before `plan fail`.
- [Risk] Users may be confused by explicit two-step setup (`change new` then `plan init`). -> Mitigation: improve CLI help, examples, and actionable error messages when plan is missing.
- [Risk] Future plan modes may diverge in quality. -> Mitigation: enforce schema validation and maintain mode template tests.

## Migration Plan

1. Add and publish agent guidance artifact (skill and/or AGENT.md) for loop execution while keeping protocol commands unchanged.
2. Add plan mode resolution with `sdd` mode mapped to current SDD plan semantics.
3. Update change/plan command lifecycle checks and CLI guidance text.
4. Add integration tests covering:
   - guidance-driven full loop with mixed script/skill actions,
   - explicit init mode flow,
   - missing-plan and unsupported-mode failures.
5. Document v0.3 workflow and deprecate implicit assumptions from v0.2 docs.

Rollback strategy:
- If guidance-first path is unstable, continue supporting direct protocol command usage.
- If mode registry introduces regressions, keep `sdd` as a compatibility fallback and disable new modes.

## Open Questions

- Should `change new` stop writing `plan.json` by default, or keep compatibility via an explicit `--with-default-plan` flag?
- What is the minimum standardized schema for skill failure payloads (`code`, `message`, `category`, `details`)?
- Should guidance mandate a default backoff/poll interval for `blocked` state, or leave it agent-specific in v0.3?
