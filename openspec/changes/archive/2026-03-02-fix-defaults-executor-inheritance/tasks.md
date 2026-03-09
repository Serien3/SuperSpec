## 1. Executor Inheritance Fix

- [x] 1.1 Update protocol payload executor resolution to use effective plan defaults for steps without explicit executor fields.
- [x] 1.2 Verify existing explicit step executor resolution behavior remains unchanged.

## 2. Regression Tests

- [x] 2.1 Add integration test covering step payload generation when `defaults.executor=script` and step has no explicit executor fields.
- [x] 2.2 Run full SuperSpec test suite and confirm all tests pass.
