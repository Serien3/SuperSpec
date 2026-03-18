## Context

`superspec` currently exposes `superspec change archive` as the only explicit terminal lifecycle command. The implementation loads execution metadata, rejects running changes unless forced, deletes `execution/`, and moves the remaining directory into `superspec/changes/archive/...`. That behavior is reasonable for `spec-dev`, where proposal/design/spec/task artifacts are long-lived assets, but it is a poor fit for workflows that mostly exist to coordinate one-off work.

The workflow contract already supports explicit top-level fields, and finish behavior now belongs in that explicit contract instead of in annotation-style metadata. This change makes finish cleanup part of workflow definition and removes the archive-only command surface instead of layering a second terminal command beside it.

## Goals / Non-Goals

**Goals:**
- Introduce one terminal command, `superspec change finish`, that handles archive/delete/keep decisions.
- Make retention defaults part of workflow definition through top-level `finishPolicy`.
- Keep safety semantics simple: running changes require `--force` before destructive finish actions.
- Remove archive-only code paths that no longer add value.

**Non-Goals:**
- Preserve backward compatibility for `superspec change archive`.
- Add configurable retention policies outside workflow metadata.
- Introduce partial cleanup modes beyond `archive`, `delete`, and `keep`.

## Decisions

### Decision: `change finish` owns terminal cleanup

Add a new engine entrypoint that resolves change metadata, checks running state, and then dispatches one of three actions:
- `archive`: delete `execution/` and move the change directory to `superspec/changes/archive/<started-date>-<change-name>-<workflow-id>`
- `delete`: remove the entire active change directory
- `keep`: leave the change directory in place and return a payload indicating no cleanup was performed

This keeps the lifecycle model centered on “finish a change” instead of forcing users to think in terms of one cleanup mechanism.

Alternative considered: keep `change archive` and add `change delete`.
Rejected because it pushes policy selection onto users every time and leaves the lifecycle surface fragmented.

### Decision: workflow top-level field declares default finish policy

Use top-level `finishPolicy` in workflow documents with bounded values `archive`, `delete`, and `keep`. Runtime resolution should require a valid policy whenever `change finish` is invoked; invalid or missing policy is a structured protocol error because terminal lifecycle semantics are part of workflow definition.

Recommended workflow defaults for this change:
- `spec-dev`: `archive`
- `bug-fix`: `delete`
- `code-review`: `delete`
- `fast-dev`: `delete`

Alternative considered: infer policy from workflow id in code.
Rejected because it duplicates workflow intent outside workflow definition and makes lifecycle behavior harder to inspect.

### Decision: explicit CLI overrides are narrow and non-combinable

`superspec change finish <change-name>` uses the workflow default. Optional flags `--archive`, `--delete`, and `--keep` override that default, but exactly one override may be supplied. `--force` bypasses the running-change guard for `archive` and `delete`. `keep` does not need force because it is non-destructive, but parsing remains uniform by allowing `--force` without changing behavior.

Alternative considered: `--mode <policy>`.
Rejected because dedicated flags are more discoverable and easier to validate at the parser layer.

### Decision: remove archive-only command surface and implementation

Delete the `superspec change archive` parser entrypoint, archive-specific CLI command handler, and archive-specific tests that only prove the old entrypoint exists. Keep archive path generation and metadata loading only if they are still useful to the finish implementation; otherwise collapse them into a finish-focused module.

Alternative considered: leave `change archive` as an alias.
Rejected because this project is still in development and the extra entrypoint adds noise without meaningful benefit.

## Risks / Trade-offs

- [Workflow files missing completion policy] -> Update all built-in workflow schemas in the same change and validate metadata strictly.
- [Deleting change directories may remove useful ad hoc notes] -> Make `spec-dev` archive by default and keep explicit `--archive` override available for other workflows.
- [Removing `change archive` may require test updates across the CLI surface] -> Update parser and lifecycle tests in the same change instead of carrying compatibility branches.

## Migration Plan

1. Add completion policy metadata to built-in workflow schemas.
2. Replace archive command parsing and dispatch with finish command parsing and dispatch.
3. Implement finish engine behavior and remove archive-only entrypoint code.
4. Update tests and specs to reflect the new lifecycle contract.

No backward-compatibility shim is planned. Reverting the change would mean restoring the archive command and removing finish.

## Open Questions

None. This change intentionally chooses cleanup simplicity over compatibility.
