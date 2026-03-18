## 1. CLI Surface

- [x] 1.1 Add `superspec change archive <change-name>` parser support with an optional `--force` flag.
- [x] 1.2 Wire command dispatch so archive is part of the `change` command surface.

## 2. Archive Flow

- [x] 2.1 Add helpers to load archive metadata (`startedAt`, `workflowId`, runtime status) from an active change.
- [x] 2.2 Implement guarded archive behavior that rejects `running` changes unless `--force` is provided.
- [x] 2.3 Remove the `execution/` directory and move the change into a unique archive path named `<YYYY-MM-DD>-<change-name>-<workflow-type>`.

## 3. Specs and Tests

- [x] 3.1 Add OpenSpec specs for archive command behavior and lifecycle guardrails.
- [x] 3.2 Add parser and command tests for success, missing change, running rejection, and `--force` override.
