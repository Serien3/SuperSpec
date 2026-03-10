# CHANGELOG

All notable changes to SuperSpec are documented in this file.

## SuperSpec - v1.1.0

Release date: 2026-03-10

### Added
- Added `superspec init --agent codex` to initialize SuperSpec project directories and sync packaged skills, agent definitions, and config into the repository.
- Added consolidated `superspec change` commands for listing changes, creating and advancing a change with `advance`, checking execution progress with `status`, and reporting step completion/failure with `stepComplete` and `stepFail`.
- Added `superspec git create-worktree`, `superspec git finish-worktree`, and `superspec git commit` to cover worktree lifecycle and persist SuperSpec-managed commit metadata into execution state.
- Added `superspec sdd design` to determine whether a change should include `design.md` based on current change content.

### Changed
- Reworked the workflow contract from `actions` to `steps`, and aligned CLI handling, runtime snapshot structure, workflow schemas, and validation logic around the new execution model.
- Refactored execution state storage to keep workflow metadata and runtime state in a unified snapshot under `execution/state.json`, while continuing to append lifecycle events to `execution/events.log`.
- Improved workflow validation with stricter runtime checks for step dependencies, duplicate IDs, executor payload compatibility, and required `approveLabel`/`rejectLabel` fields for human-executor options.
- Simplified change creation and execution startup by binding a change directly to a selected workflow through `change advance --new <workflow>/<change>`.
- Improved failure handling so a step failure transitions the change into terminal `failed` state and propagates failure status across remaining steps consistently.
- Refined `change status` output to support compact and full JSON views for easier operator inspection and downstream automation.

### Removed
- Removed legacy `plan`-prefixed lifecycle commands in favor of the unified `change` command surface.
- Removed obsolete workflow document fields and overlays such as top-level `plan`, `context`, `title`, `goal`, and `variables` customizations from the supported runtime workflow schema.

## SuperSpec - v1.0.0

Release date: 2026-03-05

🚀 **SuperSpec has officially come into existence!**

### Added
- Added `code-review` skill support to improve review-oriented execution in the SuperSpec workflow.

### Changed
- Improved CLI output formatting for clearer runtime and operator feedback.
- Resolved inconsistencies between protocol files and code handling/validation behavior.
- Defined `workflow.schemas` field formats and clarified their intended downstream usage.
- Temporarily unified communication contracts across static protocol artifacts.

## SuperSpec - v0.6.0

Release date: 2026-03-05

### Changed
- Reworked the SuperSpec entry skill to align with the current execution model and operator workflow.
- Updated the default `SDD` workflow to match the latest SuperSpec orchestration behavior.
- Moved worktree lifecycle handling (`create`/`finish`) into built-in SuperSpec commands and out of workflow actions; worktree operations are now explicitly run before plan execution.
- Switched action failure semantics to fail-fast: any reported action failure now transitions the workflow to terminal `failed`, requiring human intervention.
- Aligned workflow template contracts and validation behavior across engine, schemas, and docs.

### Added
- Added `superspec validate` subcommand for validating custom workflow files against supported template/schema constraints before execution.

### Removed
- Removed retry/continue-style autonomous failure recovery from active runtime behavior in favor of fail-fast human escalation.
