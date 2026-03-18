## 1. Finish Lifecycle Contract

- [x] 1.1 Add change specs that define the new `change finish` command, workflow `finishPolicy`, and removal of the standalone archive command.
- [x] 1.2 Update built-in workflow schemas to declare explicit `finishPolicy` defaults for each workflow type.

## 2. CLI And Engine Implementation

- [x] 2.1 Replace the `change archive` parser and CLI handler with `change finish` and explicit override flags.
- [x] 2.2 Implement finish lifecycle logic for archive, delete, and keep outcomes, including running-state force checks and structured payloads.
- [x] 2.3 Remove archive-only code paths that are no longer needed after finish owns terminal cleanup.

## 3. Verification

- [x] 3.1 Update change lifecycle and parser tests to cover finish defaults, overrides, running-state guards, and removal of archive parser support.
- [x] 3.2 Run targeted tests for workflow validation and change lifecycle, then run the full unittest suite.
