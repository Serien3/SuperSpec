## Context

An active SuperSpec change lives under `superspec/changes/<change-name>` and currently keeps runtime control artifacts under `execution/`. Archived changes already have a conventional home under `superspec/changes/archive/`, but moving a change there is a manual repository operation with no command-level validation or naming discipline.

The archive operation should stay outside the execution protocol. It is a lifecycle management command that removes a change from the active working set while keeping authored artifacts available for later reference.

## Goals / Non-Goals

**Goals:**
- Provide `superspec change archive <change-name>` as a first-class lifecycle command.
- Use execution metadata already persisted in `execution/state.json` to derive the archive directory name.
- Prevent accidental archival of still-running changes by default.
- Keep archived change directories free of runtime execution control files.

**Non-Goals:**
- Redesign execution state semantics or workflow binding.
- Preserve protocol audit files inside archived change directories.
- Add restore/unarchive behavior in the same change.

## Decisions

1. Archive only active changes rooted at `superspec/changes/<change-name>`.
- The command resolves the active change directory using existing change-name guardrails.
- It does not operate on directories already under `superspec/changes/archive/`.

2. Derive archive naming from persisted execution metadata.
- `started-date` comes from `execution/state.json.runtime.startedAt`, truncated to `YYYY-MM-DD`.
- `workflow-type` comes from `execution/state.json.meta.workflowId`.
- Final directory format: `<started-date>-<change-name>-<workflow-type>`.

3. Treat `running` as a guarded state.
- If `execution/state.json.runtime.status == "running"`, archive fails with a structured error unless `--force` is set.
- Terminal runtime states such as `success` or `failed` archive without `--force`.

4. Delete `execution/` before moving the change directory.
- Archived changes should retain authored artifacts (`proposal.md`, `design.md`, `tasks.md`, `specs/`, etc.) but not runtime control/log files.

5. Keep archive destination names unique.
- If the computed archive directory already exists, append `-2`, `-3`, ... until a free path is found.

## Risks / Trade-offs

- [Lost execution audit trail] Removing `execution/` discards protocol history. This is intentional to keep archive focused on authored artifacts rather than runtime files.
- [Metadata dependency] Archive naming depends on readable `execution/state.json`. Corrupt or missing metadata must fail clearly instead of guessing.
- [Accidental force usage] `--force` allows archiving unfinished work. The command should keep the default safe path by requiring an explicit override.

## Implementation Outline

1. Add archive path helpers that locate active changes, load archive metadata, and compute unique archive destinations.
2. Add `change archive` parser/dispatch with `--force`.
3. Implement archive flow:
- validate active change exists
- load `startedAt`, `workflowId`, and runtime `status`
- reject `running` unless forced
- remove `execution/`
- move change directory into `superspec/changes/archive/<derived-name>`
4. Add test coverage for parser shape, success path, missing change, running guardrail, and `--force` override.
