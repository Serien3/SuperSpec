## 1. Runtime path integrity hardening

- [x] 1.1 Add orchestration guard that compares CLI-target change directory with plan context change directory and fails on mismatch.
- [x] 1.2 Add protocol lifecycle regression test covering mismatch rejection before runtime state mutation.

## 2. Executor validation hardening

- [x] 2.1 Update plan validator to reject explicit executor values outside `skill|script|human` and reject non-string explicit executor values.
- [x] 2.2 Add validator/integration regression tests for invalid explicit executor values.

## 3. Verification

- [x] 3.1 Run targeted tests for plan lifecycle and integration behavior updates.
- [x] 3.2 Run full unit test suite and confirm green.
