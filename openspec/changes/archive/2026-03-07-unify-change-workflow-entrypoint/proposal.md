## Why

Current SuperSpec change execution is split across `change new`, `plan init`, and `plan next`, which forces agents to coordinate a two-step bootstrap before any work can start. This creates unnecessary branching in skills and makes it harder to support multiple workflow types consistently.

## What Changes

- Introduce a unified command: `superspec change advance` as the primary runtime entrypoint for listing, creating, and advancing changes.
- Enforce that each change binds to exactly one workflow type at creation time.
- Add `superspec change advance --new <workflow-type>/<change-name>` to create a change and initialize its workflow-backed plan in one step.
- Make `superspec change advance <change-name>` the canonical next-action pull behavior.
- Make `superspec change advance` (without args) equivalent to `superspec change list`.
- Remove `superspec change new`, `superspec plan init`, and `superspec plan next` from CLI surface in favor of the unified entrypoint.
- Keep existing protocol report commands (`plan complete|fail|approve|reject|status`) during migration.
- **BREAKING**: workflows are no longer initialized as an independent phase; change creation and workflow binding become a single operation.

## Capabilities

### New Capabilities
- `change-advance-entrypoint`: Unified CLI entrypoint that supports list, advance existing change, and create+advance new change.
- `single-workflow-per-change`: Persistent one-to-one binding between a change and selected workflow schema.

### Modified Capabilities
- `change-plan-orchestration`: Change orchestration now assumes workflow binding at creation and removes explicit plan-init dependency from the execution path.
- `agent-loop-runner-entry`: Agent runtime/skills switch from `change new + plan init + plan next` to `change advance` forms.

## Impact

- Affected CLI code: parser and command dispatch in `src/superspec/cli.py`.
- Affected engine code: plan/workflow bootstrapping paths in `src/superspec/engine/workflow_loader.py` and `src/superspec/engine/plan_loader.py`.
- Affected skill assets: `src/superspec/skills/superspec-run-change-to-done/SKILL.md` and related command examples.
- Affected tests: parser and lifecycle tests currently asserting explicit `plan init` / `change new` behavior.
- User-facing command contracts and documentation require migration notes.
