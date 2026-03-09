## 1. Schema and Contract Updates

- [x] 1.1 Extend workflow schema executor enums (`defaults.executor`, `steps[].executor`, `steps[].defaults.executor`) to include `human`.
- [x] 1.2 Extend protocol contracts (`schemas/protocol.contracts.json` and debug contracts payload) to include human executor and human step payload shape.

## 2. Validation and Protocol Implementation

- [x] 2.1 Update plan/workflow validator rules to accept `executor=human` and require valid human payload fields.
- [x] 2.2 Update runtime step field resolution to include human-specific runtime-resolved fields.
- [x] 2.3 Update next-step payload builder to emit `executor=human` payload with review instruction metadata while preserving existing script/skill behavior.

## 3. Agent Loop Guidance

- [x] 3.1 Update bundled agent-loop skills to document and dispatch `human` executor by waiting for human feedback and reporting `complete` or `fail`.

## 4. Tests

- [x] 4.1 Add/extend integration tests for human executor next payload, blocked polling while human step is running, and completion/failure transitions.
- [x] 4.2 Add/extend validation/lifecycle tests for human executor schema acceptance and invalid human payload rejection.
- [x] 4.3 Run targeted tests, then full test suite, and fix regressions.
