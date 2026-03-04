# CHANGELOG

All notable changes to SuperSpec are documented in this file.

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
