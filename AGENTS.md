# Repository Guidelines

## Project Structure & Module Organization
- Core package: `src/superspec/`.
- CLI entrypoint: `src/superspec/cli.py` (installed as the `superspec` command via `pyproject.toml`).
- Runtime engine: `src/superspec/engine/` (protocol, state store, validation, orchestration).
- Schemas/templates: `src/superspec/schemas/`.
- Tests: `tests/` (notably `test_integration.py`, `test_plan_lifecycle.py`).
- OpenSpec artifacts: `openspec/changes/` and `openspec/specs/`.
- Generated agent outputs belong in `output/`.

## Build, Test, and Development Commands
- `python3 -m pip install -e .` — install the package in editable mode.
- `superspec --help` — inspect CLI groups and flags.
- `PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"` — run the full test suite.
- `PYTHONPATH=src python3 -m unittest tests.test_integration -v` — run integration tests only.
- `PYTHONPATH=src python3 -m unittest tests.test_plan_lifecycle -v` — run plan lifecycle tests only.

## Coding Style & Naming Conventions
- Python 3.10+, UTF-8, 4-space indentation.
- Keep `cli.py` thin; prefer small pure functions in `src/superspec/engine/*`.
- Use `snake_case` for functions/variables/files and `UPPER_SNAKE_CASE` for constants.
- For user-facing failures, raise structured `ProtocolError` instead of ad-hoc exceptions.
- Do not commit generated artifacts (`__pycache__/`, `*.pyc`, `*.egg-info/`).

## Testing Guidelines
- Framework: built-in `unittest`.
- Add or extend tests under `tests/test_*.py` for any behavior change.
- Prefer behavior-focused assertions (state transitions, payload fields, error codes).
- Run targeted tests first, then the full suite before opening a PR.

## Commit & Pull Request Guidelines
- Follow repository commit style: `feat: ...`, `fix: ...`, `chore: ...` (short imperative subject).
- Keep commits scoped to one concern.
- PRs should include: purpose, affected commands/files, test evidence (commands + pass result), and sample JSON/CLI output when contracts change.
