## Why

Current SuperSpec execution protocol is optimized for concurrent and recoverable multi-agent orchestration, but that complexity is currently slowing down iteration. For the near term, the product only needs single-agent, single-process, serial execution, so lease management and related protocol surface add overhead without practical benefit.

## What Changes

- Remove lease-oriented command contract requirements from the active execution workflow for the current phase.
- Simplify agent loop semantics to a strict serial flow: `next -> execute -> complete|fail -> next` until `done`.
- Simplify default plan template to match single-agent serial execution assumptions and remove unnecessary advanced knobs from the starter template.
- Mark multi-agent lease-safe execution semantics as deferred/future scope rather than current required behavior.
- Clean up obsolete code paths, tests, and guidance documents that only exist to support lease-based concurrency behavior.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `agent-driven-plan-execution`: remove lease-token requirement from current protocol requirements and redefine reporting contract for single-agent serial execution.
- `agent-loop-runner-entry`: update runner guidance to a lease-free loop and simplify blocked/retry guidance to match serial assumptions.
- `change-plan-orchestration`: align orchestration requirements and defaults with a simplified single-process execution model and template surface.

## Impact

- Affected code: protocol engine command handlers (`next/complete/fail/status`), CLI argument surface, plan template defaults, and related tests.
- Affected docs/specs: active specs under `openspec/specs/` for execution protocol and loop guidance.
- Backward compatibility: **BREAKING** for clients that currently send/expect lease fields in protocol requests/responses.
- Future extensibility: lease/concurrency model is intentionally deferred and may be reintroduced in a future change with a deeper design.
