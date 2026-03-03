## 1. Contract Alignment

- [x] 1.1 Audit current `workflow.schema.json` customization fields and runtime-accepted fields in `superspec` engine, and document the mismatch list in code comments or change notes.
- [x] 1.2 Define a minimal supported customization field set and update `workflow.schema.json` to represent only this set with explicit validation constraints.
- [x] 1.3 Centralize runtime validation constants/rules so code paths use the same supported field set as schema validation.

## 2. Runtime Validation and Merge Behavior

- [x] 2.1 Update workflow loading/validation to reject unknown customization fields with clear, path-specific errors.
- [x] 2.2 Align plan generation merge logic to deterministic precedence for supported customization fields (base template < workflow customization < init-time overrides).
- [x] 2.3 Ensure protected change context fields (such as `changeName`, `changeDir`) cannot be overridden by workflow customization.

## 3. Tests and Documentation

- [x] 3.1 Add or update unit/integration tests covering valid customization, unsupported-field rejection, and deterministic precedence behavior.
- [x] 3.2 Add or update test coverage for protected-field override attempts to verify enforced rejection/ignore behavior.
- [x] 3.3 Refresh workflow authoring docs/examples so sample `workflow.json` files only use supported customization fields.
