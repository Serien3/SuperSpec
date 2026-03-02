## 1. Define execution protocol contracts

- [x] 1.1 Add command contract definitions for `next`, `complete`, `fail`, and `status` (request/response fields, states, and errors).
- [x] 1.2 Define action payload schemas for `script` and `skill` executors, including debug-only rendered prompt behavior.
- [x] 1.3 Define lease token structure and lifecycle rules (issued, validated, expired, reclaimed).

## 2. Refactor engine to protocol-driven progression

- [x] 2.1 Implement `next` logic to select one runnable action with dependency checks and return lease-bound payload.
- [x] 2.2 Implement `complete` logic to persist action output, transition state, and unlock downstream actions.
- [x] 2.3 Implement `fail` logic to record error payload, apply retry/backoff/onFail policy, and return next state.

## 3. Persist and observe execution state

- [x] 3.1 Add execution storage layout (`execution/state.json`, `execution/leases.json`, `execution/events.log`).
- [x] 3.2 Record state transitions and protocol events in append-only event log for auditing.
- [x] 3.3 Add `status --json` output to surface protocol-mode progress, lease ownership, and last failure details.

## 4. Integrate with existing CLI workflow

- [x] 4.1 Add CLI commands for `next`, `complete`, and `fail` with strict JSON payload validation.
- [x] 4.2 Remove legacy `plan run` path and keep protocol mode (`next`/`complete`/`fail`/`status`) as the only execution path.
- [x] 4.3 Ensure invalid lease or stale completion reports are rejected with deterministic error messages.

## 5. Validate behavior and document usage

- [x] 5.1 Add integration tests for successful pull-loop flow (`next -> complete` until done).
- [x] 5.2 Add concurrency tests for lease conflicts and expiry/reclaim behavior.
- [x] 5.3 Document Agent loop usage pattern and operational guidance for protocol mode.
