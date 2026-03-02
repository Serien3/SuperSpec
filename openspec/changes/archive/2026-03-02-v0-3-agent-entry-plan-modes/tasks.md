## 1. Plan Mode Initialization

- [x] 1.1 Add mode option parsing to `superspec plan init` (initial support: `sdd`).
- [x] 1.2 Implement mode-keyed template resolution and interpolation for change-scoped plan generation.
- [x] 1.3 Add validation and clear error handling for unsupported plan modes.
- [x] 1.4 Align `change new` and plan lifecycle behavior with explicit plan initialization semantics.

## 2. Agent-Driven Execution Guidance

- [x] 2.1 Create a reusable skill and/or `AGENT.md` guidance document that defines the full loop: `plan next -> execute -> plan complete|fail -> repeat`.
- [x] 2.2 Document executor dispatch rules for `script` and `skill` actions, including required report payload fields.
- [x] 2.3 Define guidance for `blocked` handling, polling/backoff, and terminal success/failure signaling.
- [x] 2.4 Add usage examples so an external agent can run the full superspec workflow without additional assumptions.

## 3. Protocol and Contract Updates

- [x] 3.1 Update protocol contracts/docs to formalize external skill execution report requirements.
- [x] 3.2 Ensure lease-safe reporting behavior is preserved under continuous loop polling.
- [x] 3.3 Add CLI/help docs for the v0.3 flow: `new change -> plan init --mode sdd -> plan validate -> agent-guided loop`.

## 4. Verification

- [x] 4.1 Add verification steps (or tests where applicable) for guidance-driven full loop completion across mixed `script` and `skill` actions.
- [x] 4.2 Add tests for unsupported mode rejection and missing-plan lifecycle errors.
- [x] 4.3 Validate terminal success/failure signaling behavior as described by guidance.
