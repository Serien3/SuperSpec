## Why

The current change lifecycle assumes every completed change should be archived, which fits `spec-dev` but creates noise for short-lived workflows like `bug-fix`, `fast-dev`, and `code-review`. We need a single completion command that applies the right retention behavior by workflow so finished work does not accumulate meaningless artifacts.

## What Changes

- Replace the archive-only completion model with `superspec change finish <change-name>`.
- Add workflow-level completion policy metadata so each workflow declares whether finished changes are archived or deleted.
- Make `change finish` apply the workflow default by default and allow explicit override to `archive`, `delete`, or `keep`.
- **BREAKING**: remove `superspec change archive <change-name>` and its dedicated archive-only lifecycle surface.
- Remove archive-only implementation paths that become redundant once finish owns terminal change cleanup.

## Capabilities

### New Capabilities
- `change-finish-entrypoint`: Complete a change through a single CLI command that applies workflow retention policy or an explicit override.

### Modified Capabilities
- `workflow-core-contract-normalization`: Extend workflow metadata with bounded completion policy values that drive terminal cleanup behavior.
- `change-advance-entrypoint`: Replace archive lifecycle exposure in the `superspec change` surface with finish lifecycle exposure.
- `change-archive-entrypoint`: Remove the standalone archive command contract because terminal cleanup is handled by `change finish`.

## Impact

- Affected code in `src/superspec/cli.py`, `src/superspec/engine/changes/`, workflow schemas, and change lifecycle tests.
- Removes one CLI command and introduces one new CLI command with force and retention override semantics.
- Changes default end-of-workflow behavior for non-spec workflows through workflow metadata rather than user convention.
