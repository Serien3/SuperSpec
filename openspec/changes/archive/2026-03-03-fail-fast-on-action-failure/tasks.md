## 1. Protocol and schema simplification

- [x] 1.1 Remove retry configuration fields from plan schema/default constants and related validation logic.
- [x] 1.2 Change protocol failure handling so `fail_action` immediately terminalizes workflow with no retry scheduling path.
- [x] 1.3 Remove retry-focused status payload logic and protocol contract metadata entries.

## 2. CLI and documentation alignment

- [x] 2.1 Remove `superspec plan status --retry` option and any retry wording from CLI/docs.
- [x] 2.2 Update bundled skill instructions to replace retry polling behavior with fail-fast human escalation guidance.
- [x] 2.3 Update OpenSpec specs/docs that still describe retry behavior.

## 3. Tests and verification

- [x] 3.1 Replace retry-oriented tests with fail-fast terminal failure tests.
- [x] 3.2 Update parser/contract tests for removed `--retry` surface.
- [x] 3.3 Run full test suite and confirm all changes pass.
