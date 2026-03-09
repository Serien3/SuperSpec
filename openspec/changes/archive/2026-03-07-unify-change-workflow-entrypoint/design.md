## Context

SuperSpec currently exposes separate lifecycle commands for change scaffolding (`change new`), workflow materialization (`plan init`), and step dispatch (`plan next`). This split causes agent logic and CLI UX to branch before useful execution can begin, and it weakens the conceptual model when new workflow types are introduced. We need a single entrypoint that supports list, create+bind workflow, and advance behavior while preserving protocol execution semantics.

## Goals / Non-Goals

**Goals:**
- Provide one command surface (`change advance`) for change lifecycle entry.
- Bind workflow type to change identity at creation time.
- Preserve existing protocol step loop behavior once a change is selected.
- Deliver compatibility path for existing users and skills.

**Non-Goals:**
- Redesign protocol state machine semantics (`next/complete/fail/status`).
- Remove all legacy `plan` subcommands in the same change.
- Implement natural-language workflow inference inside CLI.

## Decisions

1. Introduce a tri-modal `change advance` command.
- No arguments: list available changes (current `change list` behavior).
- `<change-name>`: advance existing change (current `plan next` behavior).
- `--new <type>/<change-name>`: create change, select workflow type, materialize plan, and return next step payload.

2. Persist workflow binding in change metadata.
- At creation (`--new`), write binding metadata in change-scoped state (e.g., plan metadata/workflow id and auxiliary manifest if needed).
- Runtime `advance <change-name>` reads binding; it does not re-negotiate workflow type.

3. Make plan bootstrap implicit for the unified path.
- Explicit `plan init` is replaced by internal bootstrap logic for new changes.
- Existing changes without `plan.json` may be auto-bootstrapped only if workflow binding is discoverable; otherwise return structured error.

4. Keep protocol report commands in place.
- `plan complete|fail|approve|reject|status` remain valid so existing loop integrations continue to function while entrypoint changes.

5. Keep workflow inference responsibility in agent/skill layer.
- CLI requires explicit `--new <type>/<change-name>`.
- Agent may infer `<type>` from user description and supply explicit CLI arguments.

## Risks / Trade-offs

- [Migration complexity] Existing skills and docs hardcode old commands -> Mitigation: synchronized skill/doc updates in the same release.
- [Ambiguous legacy state] Existing change directories may lack explicit workflow binding -> Mitigation: fallback to plan metadata detection and clear `invalid_workflow_binding` errors.
- [Behavior drift] Users may expect `change advance` to include status/complete semantics -> Mitigation: keep protocol report operations under `plan` in this phase and document boundary clearly.
- [Parser complexity] Mixed positional and `--new` forms can create ambiguous CLI parsing -> Mitigation: strict mutual exclusivity checks and explicit error text.

## Migration Plan

1. Add new parser and dispatch branch for `change advance` with three modes.
2. Implement internal create+bootstrap helper that replaces external `change new + plan init` sequence.
3. Update run-loop skill and AGENT guidance to use `change advance` entry.
4. Remove legacy parser/dispatch branches for `change new`, `plan init`, and `plan next`.
5. Update tests for parser and lifecycle behavior around the unified entrypoint.

## Open Questions

- Should `change advance <name>` auto-bootstrap when `plan.json` is missing but only one workflow template exists?
- Where should workflow binding live long-term: plan metadata only or dedicated per-change manifest?
- Do we need an explicit compatibility alias layer for external tooling, or is direct command removal acceptable?
