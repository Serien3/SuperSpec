## Why

SuperSpec currently keeps active and historical changes under the same conceptual lifecycle, but it does not expose a first-class way to retire a finished or abandoned active change. That makes `superspec change list` grow noisier over time and forces users to manage archive placement manually.

## What Changes

- Add `superspec change archive <change-name>` to move an active change into `superspec/changes/archive/`.
- Archive target directories use the stable naming convention `<started-date>-<change-name>-<workflow-type>`.
- Remove the change-scoped `execution/` directory before moving the archive so runtime control files do not persist in archived artifacts.
- Reject archiving changes whose runtime status is still `running` unless the user passes `--force`.
- Return structured errors when the target change does not exist or lacks valid execution metadata needed for archive naming.

## Capabilities

### New Capabilities
- `change-archive-entrypoint`: Archive active changes through a dedicated CLI command with force semantics and deterministic naming.

### Modified Capabilities
- `change-advance-entrypoint`: Change lifecycle command surface now includes archive behavior in addition to list and advance flows.

## Impact

- Affected CLI code: parser and dispatch in `src/superspec/cli.py`.
- Affected change path/storage helpers: archive path resolution and execution metadata loading.
- Affected tests: parser coverage, archive success path, running-change guardrails, and missing-change errors.
