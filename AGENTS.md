# Repository Guidelines

## Project Structure & Module Organization
- Core package: `superspec/`.
- CLI entrypoint: `superspec/cli.py` (`superspec` command from `pyproject.toml`).
- Runtime engine: `superspec/engine/` (protocol, state store, validation, orchestration).
- Schemas and templates: `superspec/schemas/`, `superspec/templates/`.
- Tests: `superspec/tests/` (`test_integration.py`, `test_plan_lifecycle.py`).
- Spec/change artifacts: `openspec/changes/` and `openspec/specs/`.
- Generated/agent outputs should go under `output/` (not `.codex/` or `.github/`).

## Build, Test, and Development Commands
- `python3 -m pip install -e .` — install local editable package.
- `superspec --help` — inspect available CLI groups and flags.
- `python3 -m unittest discover -s superspec/tests -p "test_*.py"` — run full test suite.
- `python3 -m unittest superspec.tests.test_integration -v` — run integration tests only.
- `python3 -m unittest superspec.tests.test_plan_lifecycle -v` — run plan lifecycle tests only.

## Coding Style & Naming Conventions
- Language: Python (3.10+), 4-space indentation, UTF-8 text.
- Prefer small pure functions in `superspec/engine/*`; keep CLI logic in `cli.py` thin.
- Naming: `snake_case` for functions/variables/files, `UPPER_SNAKE_CASE` for constants.
- Use structured protocol errors (`ProtocolError`) instead of ad-hoc exceptions for user-facing failures.
- Do not commit generated artifacts: `__pycache__/`, `*.pyc`, `*.egg-info/`.

## Testing Guidelines
- Framework: built-in `unittest`.
- Add/extend tests in `superspec/tests/test_*.py` for any protocol or CLI behavior change.
- Prefer behavior-focused assertions (state transitions, payload fields, error codes).
- Run targeted tests first, then full suite before opening a PR.

## Commit & Pull Request Guidelines
- Follow existing history style: `feat: ...`, `fix: ...`, `chore: ...` (short imperative subject).
- Keep commits scoped (one concern per commit); avoid mixing workflow/spec noise with engine logic.
- PRs should include:
  - What changed and why.
  - Affected commands/files (for example `superspec plan status --json --full`).
  - Test evidence (commands + pass result).
  - Sample JSON/CLI output when contracts change.
