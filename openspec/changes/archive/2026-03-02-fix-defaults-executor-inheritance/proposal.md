## Why

Current protocol action payload generation does not correctly inherit `defaults.executor` from the plan-level defaults when an action omits explicit executor fields. This can route an action to the wrong executor type and break agent dispatch behavior.

## What Changes

- Fix executor resolution so actions without explicit `executor`/`script`/`skill` correctly inherit from plan defaults.
- Add regression tests for actions with no explicit executor fields to validate script-default inheritance behavior.
- Keep existing explicit action executor behavior unchanged.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `change-plan-orchestration`: Clarify and enforce executor inheritance from plan defaults when action-level executor fields are omitted.

## Impact

- Affected code: `superspec/engine/protocol.py`, `superspec/tests/test_integration.py`.
- No API surface expansion; behavior is corrected to match intended contract.
- Reduces risk of incorrect skill/script dispatch in agent loops.
