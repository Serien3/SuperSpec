## Why

Current protocol step payload generation does not correctly inherit `defaults.executor` from the plan-level defaults when an step omits explicit executor fields. This can route an step to the wrong executor type and break agent dispatch behavior.

## What Changes

- Fix executor resolution so steps without explicit `executor`/`script`/`skill` correctly inherit from plan defaults.
- Add regression tests for steps with no explicit executor fields to validate script-default inheritance behavior.
- Keep existing explicit step executor behavior unchanged.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `change-plan-orchestration`: Clarify and enforce executor inheritance from plan defaults when step-level executor fields are omitted.

## Impact

- Affected code: `superspec/engine/protocol.py`, `superspec/tests/test_integration.py`.
- No API surface expansion; behavior is corrected to match intended contract.
- Reduces risk of incorrect skill/script dispatch in agent loops.
