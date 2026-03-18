# Repository Guidelines

## Structure
- Core package: `src/superspec/`.
- CLI entry: `src/superspec/cli.py`.
- Engine modules: `src/superspec/engine/{changes,execution,storage,scm,workflows}/`.
- Packaged assets: `src/superspec/skills/`, `src/superspec/codex/`, `src/superspec/schemas/`.
- Tests: `tests/`.
- Runtime artifacts created by `superspec init`: `superspec/changes/`, `superspec/specs/`, `.codex/`, `progress.md`.
- `openspec/` in this repo is historical spec/design material, not the active runtime path.

## Commands
- `python3 -m pip install -e .`
- `PYTHONPATH=src python3 -m superspec.cli --help`
- `PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"`
- Targeted tests:
  - `PYTHONPATH=src python3 -m unittest tests.test_change_lifecycle -v`
  - `PYTHONPATH=src python3 -m unittest tests.test_cli_init -v`
  - `PYTHONPATH=src python3 -m unittest tests.test_progress_summary -v`
  - `PYTHONPATH=src python3 -m unittest tests.test_git_worktree_cli -v`

## Conventions
- Python 3.10+, UTF-8, 4-space indentation.
- Keep `cli.py` thin; put behavior in engine or script modules.
- Use `snake_case` for Python names and `UPPER_SNAKE_CASE` for constants.
- Preserve snapshot/protocol field names such as `workflowId` and `finishPolicy`.
- Raise `ProtocolError` for user-facing failures, with stable `code` and optional `details`.
- Do not commit generated artifacts such as `__pycache__/`, `*.pyc`, `*.egg-info/`, or `superspec/**/execution/**`.

## Workflow Notes
- `superspec init --agent codex` installs `.codex/skills`, `.codex/agents`, `.codex/config.toml`, creates `superspec/changes/archive`, `superspec/specs`, `progress.md`, and ensures `.gitignore` contains `superspec/**/execution/**`.
- Active execution state lives in `superspec/changes/<change>/execution/state.json`.
- `superspec change advance --new <workflow>/<change>` creates and binds a change to a workflow.
- `superspec git commit` writes session progress entries; `superspec progress` summarizes them into `progress.md`.

## PRs
- Use commit subjects like `feat: ...`, `fix: ...`, `chore: ...`.
- Keep each commit scoped to one concern.
- PRs should include purpose, affected files/commands, test evidence, and sample CLI/JSON output when contracts change.
