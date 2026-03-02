# SuperSpec (Protocol-Driven v0.3)

SuperSpec is a change-scoped orchestration layer for spec-driven development.

## Implementation Policy

- Primary language: **Python**.
- Going forward, new SuperSpec engine/CLI features should be implemented in Python first.
- JS/TS implementations are not the default path unless explicitly requested.

## Protocol Mode (v0.3)

Execution is Agent-driven via pull protocol commands:

- `superspec plan next <change> --json`
- `superspec plan complete <change> <action_id> --result-json '{...}'`
- `superspec plan fail <change> <action_id> --error-json '{...}'`
- `superspec plan status <change> --json`

The engine selects work; the agent executes and reports outcomes in a single-agent serial loop.

### Action Payload Contract

- Script actions return executable command payloads.
- Skill actions return skill references (`name`, `version`, `input`, `contextFiles`).
- Full rendered prompts are only included in debug mode (`--debug`).

Execution storage for protocol mode:

- `openspec/changes/<change>/execution/state.json`
- `openspec/changes/<change>/execution/events.log`

## Removed in v0.3

- Lease token flow (`leaseId`, `--lease`, `--lease-ttl-sec`)
- `superspec plan run`
- Legacy run-state storage (`run-state.json`, `runs/<run-id>/...`)

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
2. `superspec plan init <change> --mode sdd` (or `superspec plan init <change>` for compatibility)
3. `superspec plan validate <change>`
4. Loop on `superspec plan next <change> --json` and report with `plan complete` / `plan fail` until `done`

## Tests

```bash
python3 -m unittest discover -s superspec/tests -p "test_*.py"
```
