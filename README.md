# SuperSpec (Prototype)

SuperSpec is a change-scoped orchestration layer for spec-driven development.

## Implementation Policy

- Primary language: **Python**.
- Going forward, new SuperSpec engine/CLI features should be implemented in Python first.
- JS/TS implementations are not the default path unless explicitly requested.

## What this increment includes

- `plan.json` schema (`superspec.plan/v0.1`)
- Sequential action orchestration with dependency validation
- Run-state persistence and per-action logs
- Action support for:
  - `openspec.proposal`
  - `openspec.specs`
  - `openspec.design`
  - `openspec.tasks`
  - `openspec.apply`
- CLI commands:
  - `superspec change new <name> --summary "..."`
  - `superspec plan init <change>`
  - `superspec plan validate <change>`
  - `superspec plan run <change> [--resume] [--from <action-id>]`
  - `superspec plan status <change>`

## Known limits

- No parallel DAG scheduling
- No cross-change orchestration
- `skill` executor is a placeholder envelope for now

## Test

```bash
python -m unittest discover -s superspec/tests -p "test_*.py"
```
