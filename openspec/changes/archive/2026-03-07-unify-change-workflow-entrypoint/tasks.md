## 1. CLI Entry Consolidation

- [x] 1.1 Add `change advance` parser shape with three modes: no args (list), `<change-name>` (advance), and `--new <type>/<change-name>` (create+advance).
- [x] 1.2 Implement strict argument validation for mutually exclusive mode selection and malformed `--new` selectors.
- [x] 1.3 Implement `command_change_advance` dispatch logic that routes to list behavior or protocol next behavior depending on mode.

## 2. Change Creation + Workflow Binding

- [x] 2.1 Add helper to parse `--new <type>/<change-name>` into workflow type and change name with existing change-name guardrails.
- [x] 2.2 Implement atomic create-and-bootstrap flow that creates the change directory and writes workflow-backed `plan.json` in one command.
- [x] 2.3 Persist and validate one-workflow-per-change binding so later `change advance <name>` reuses the bound workflow context.

## 3. Legacy Command Migration Layer

- [x] 3.1 Remove `change new`, `plan init`, and `plan next` command parser/dispatch branches.
- [x] 3.2 Ensure no stale code path references removed legacy command modes.
- [x] 3.3 Update CLI help text and examples to make `change advance` the canonical entrypoint.

## 4. Agent Skill and Guidance Updates

- [x] 4.1 Update `src/superspec/skills/superspec-run-change-to-done/SKILL.md` to use `change advance` for list/new/next entry behavior.
- [x] 4.2 Remove references that require explicit `plan init` in run-loop guidance and replace with unified creation flow.
- [x] 4.3 Align human-readable guidance and command snippets with post-removal command surface.

## 5. Test Refactor and Coverage Expansion

- [x] 5.1 Replace parser tests that assume `plan init`/`change new` as required setup with `change advance` mode tests.
- [x] 5.2 Add lifecycle tests for `change advance --new <type>/<name>` that assert immediate plan availability and next-action readiness.
- [x] 5.3 Add negative tests for malformed selectors, mixed argument modes, and workflow-binding conflicts.
- [x] 5.4 Keep protocol behavior regression tests green for `complete|fail|approve|reject|status` paths.

## 6. Migration and Release Notes

- [x] 6.1 Document command mapping to the unified flow (`change advance` list/advance/new forms).
- [x] 6.2 Document expected agent behavior: workflow type inference occurs in skill/agent layer, not CLI parsing.
- [x] 6.3 Document removed-command behavior and supported replacements.
