# SuperSpec (v0.5.0, Protocol-Driven v0.3)

SuperSpec is a change-scoped orchestration layer for spec-driven development.

## Implementation Policy

- Primary language: **Python**.
- Going forward, new SuperSpec engine/CLI features should be implemented in Python first.
- JS/TS implementations are not the default path unless explicitly requested.

## Plan Generation (v0.5.0)

Plan initialization is now schema/workflow-driven:

- Base template: `superspec/templates/plan.base.json`
- Workflow definitions: `superspec/schemas/workflows/*.workflow.json`
- Workflow file schema: `superspec/schemas/workflow.schema.json`

Initialization options:

- `superspec plan init <change> --schema <name>`
- Optional init-time overrides: `--title`, `--goal`

Merge precedence for generated `plan.json`:

1. Base template
2. Workflow payload
3. Init-time overrides

Protected fields always come from the active change context:

- `context.changeName`
- `context.changeDir`

Execution-relevant defaults in v0.5.0:
- `executor`
- `onFail`
- `retry`

Runtime execution remains unchanged: protocol commands only consume rendered `openspec/changes/<change>/plan.json`.

## Protocol Mode (v0.3)

Execution is Agent-driven via pull protocol commands:

- `superspec plan next <change> --json`
- `superspec plan complete <change> <action_id> --result-json '{...}'`
- `superspec plan fail <change> <action_id> --error-json '{...}'`
- `superspec plan status <change> --json`
- `superspec plan status <change> --json --debug` (includes protocol `contracts`)

The engine selects work; the agent executes and reports outcomes in a single-agent serial loop.

### Action Payload Contract

- `plan next` response contains only: `state`, `changeName`, `action`.
- Script actions return: `actionId`, `executor`, `script_command`, `prompt`.
- Skill actions return: `actionId`, `executor`, `skillName`, `prompt`.
- Runtime expression resolution for `next` payload is limited to: `executor`, `script`, `skill`, and `inputs.prompt`.
- Action statuses are: `PENDING`, `READY`, `RUNNING`, `SUCCESS`, `FAILED`.
- Debug rendered prompt is only included in debug mode (`--debug`).
- `plan status` omits `contracts` by default; `contracts` are returned only when `status --debug` is set.

Execution storage for protocol mode:

- `openspec/changes/<change>/execution/state.json`
- `openspec/changes/<change>/execution/events.log`

## Removed in v0.3

- Lease token flow (`leaseId`, `--lease`, `--lease-ttl-sec`)
- `superspec plan run`
- Legacy run-state storage (`run-state.json`, `runs/<run-id>/...`)
- In-process action handlers/runners (`superspec/actions/*`, `superspec/runners/*`): execution is external-agent only

## Command Contract File

See: `superspec/schemas/protocol.contracts.json`

## Known limits

- No parallel DAG scheduling
- No cross-change orchestration
- Skill execution still depends on external agent/runtime wiring

## Agent Guidance Skill

Use the `superspec-agent-driven-loop` skill as the standard playbook for external agents:

- `output/skills/superspec-agent-driven-loop/SKILL.md`

Skill output location policy:
- All newly produced SuperSpec skills MUST be written under `output/`.
- Do not place newly produced SuperSpec skills under `.codex/` or `.github/`.

Recommended flow:

1. `superspec change new <change>`
2. `superspec plan init <change> --schema sdd`
3. `superspec plan validate <change>`
4. Loop on `superspec plan next <change> --json` and report with `plan complete` / `plan fail` until `done`

## Tests

```bash
python3 -m unittest discover -s superspec/tests -p "test_*.py"
```
