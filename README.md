# SuperSpec (Protocol-Driven v0.2)

SuperSpec is a change-scoped orchestration layer for spec-driven development.

## Implementation Policy

- Primary language: **Python**.
- Going forward, new SuperSpec engine/CLI features should be implemented in Python first.
- JS/TS implementations are not the default path unless explicitly requested.

## Protocol Mode (v0.2)

Execution is Agent-driven via pull protocol commands:

- `superspec plan next <change> --json`
- `superspec plan complete <change> <action_id> --lease <id> --result-json '{...}'`
- `superspec plan fail <change> <action_id> --lease <id> --error-json '{...}'`
- `superspec plan status <change> --json`

The engine selects work; the agent executes and reports outcomes.

### Action Payload Contract

- Script actions return executable command payloads.
- Skill actions return skill references (`name`, `version`, `input`, `contextFiles`).
- Full rendered prompts are only included in debug mode (`--debug`).

### Lease Lifecycle

Each `next` response may include a lease token for the action:

- Issued when action is claimed
- Validated on `complete` / `fail`
- Expired automatically after TTL
- Reclaimed by a subsequent `next`

Execution storage for protocol mode:

- `openspec/changes/<change>/execution/state.json`
- `openspec/changes/<change>/execution/leases.json`
- `openspec/changes/<change>/execution/events.log`

## Removed in v0.2

- `superspec plan run`
- Legacy run-state storage (`run-state.json`, `runs/<run-id>/...`)

## Command Contract File

See: `superspec/schemas/protocol.contracts.json`

## Known limits

- No parallel DAG scheduling
- No cross-change orchestration
- Skill execution still depends on external agent/runtime wiring

## Tests

```bash
python3 -m unittest discover -s superspec/tests -p "test_*.py"
```
