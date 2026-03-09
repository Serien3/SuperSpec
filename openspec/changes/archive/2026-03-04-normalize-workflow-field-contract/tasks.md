## 1. Workflow Contract Normalization

- [x] 1.1 Tighten `workflow.schema.json` so each step requires explicit `executor`.
- [x] 1.2 Add schema constraints to enforce exact executor payload mapping and reject mixed payloads.
- [x] 1.3 Keep annotation/readability fields available as optional fields without execution semantics.

## 2. Validation Semantics Alignment

- [x] 2.1 Update workflow semantic validation to enforce explicit executor and exact payload matching rules.
- [x] 2.2 Remove implicit executor inference acceptance from workflow authoring validation path.
- [x] 2.3 Ensure diagnostics include stable code/path/message/hint for core contract violations.

## 3. Built-in Workflow and Runtime Compatibility

- [x] 3.1 Update packaged workflow templates to explicit executor style.
- [x] 3.2 Verify generated plans still satisfy plan validator/runtime protocol behavior.

## 4. Test Coverage

- [x] 4.1 Add/adjust plan lifecycle tests for strict core-contract checks.
- [x] 4.2 Add/adjust integration tests to assert no inference-based workflow acceptance.
- [x] 4.3 Run targeted tests and full suite, then resolve failures.
