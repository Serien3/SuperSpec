## 1. CLI Command Semantics Redefinition

- [x] 1.1 Replace current `plan validate` command surface with top-level `validate` command focused on workflow templates
- [x] 1.2 Add validate inputs (`--schema`, `--file`, `--json`) and enforce mutually exclusive source selection rules
- [x] 1.3 Update CLI output/exit-code behavior so validation success is zero and failures are non-zero with stable error contract

## 2. Workflow Validation Core

- [x] 2.1 Extract/reuse workflow validation logic into a dedicated validator entrypoint callable by CLI
- [x] 2.2 Implement three-stage validation flow (schema structure, semantic checks, generation-readiness checks)
- [x] 2.3 Add standardized error mapping (`code`, `path`, `message`, `hint`) for both human and JSON output modes

## 3. Workflow Schema Contract Tightening

- [x] 3.1 Tighten `workflow.schema.json` to explicitly define supported nested fields for `defaults` and `steps`
- [x] 3.2 Set constrained objects to reject unknown nested fields where contract is finite (`additionalProperties: false`)
- [x] 3.3 Ensure schema field surface matches runtime-accepted customization surface without drift

## 4. Test Coverage Updates

- [x] 4.1 Replace obsolete tests that validate change `plan.json` via validate command semantics
- [x] 4.2 Add positive tests for `superspec validate` with schema-name and file-path inputs
- [x] 4.3 Add negative tests for unknown top-level/nested fields, dependency graph issues, and executor/field mismatch
- [x] 4.4 Add tests for `--json` diagnostic payload shape and non-zero exit behavior on validation failures

## 5. Documentation and Migration Notes

- [x] 5.1 Update `docs/cli.md` and command help text to document new `superspec validate` purpose and usage
- [x] 5.2 Document complete workflow field contract for authors, including allowed fields and nested structures
- [x] 5.3 Add BREAKING migration note describing removal of old plan-validation semantics and replacement workflow-validation flow
