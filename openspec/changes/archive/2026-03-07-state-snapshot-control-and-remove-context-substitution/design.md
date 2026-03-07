## Context

Current execution flow materializes a change-scoped `plan.json` from workflow + base template, then uses `plan.json` as runtime input while persisting runtime state to `execution/state.json`. This creates two control surfaces for one change/workflow binding. The runtime additionally supports `${...}` expression substitution in action fields, which increases payload behavior complexity and error surface (`invalid_expression`).

The change goal is to make execution model single-source and deterministic for development stage usage:
- no `plan.json`
- workflow snapshot captured once at change creation
- runtime executes from `execution/state.json` only
- no runtime expression substitution

## Goals / Non-Goals

**Goals:**
- Replace `plan.json` runtime dependency with a snapshot-based `execution/state.json` control file.
- Initialize `execution/state.json` and `execution/events.log` during `change advance --new <workflow>/<change>`.
- Store immutable workflow definition and mutable runtime state in one file with clear boundaries.
- Remove runtime action expression substitution and related validation/error paths.
- Keep CLI protocol behavior (`next/complete/fail/status`) stable at contract level where possible.

**Non-Goals:**
- Backward compatibility for existing changes that rely on `plan.json`.
- Automatic migration tooling from legacy change directories.
- Introducing new executor types or execution policies.

## Decisions

### Decision: `execution/state.json` becomes the only workflow control source

`execution/state.json` will include:
- `meta`: schema version, change name, workflow id/version, timestamps
- `definition`: frozen action/workflow definition resolved from selected workflow at change creation
- `runtime`: execution status and per-action runtime fields

Rationale:
- Eliminates split-brain between `plan.json` and `state.json`.
- Matches one-change-one-workflow invariant.
- Keeps snapshot deterministic and self-contained.

Alternatives considered:
- Keep `plan.json` + `state.json`: rejected as redundant for current model.
- Read workflow file on every runtime call: rejected due to non-determinism if workflow file changes after change creation.

### Decision: Change creation performs full snapshot bootstrap

`change advance --new <workflow>/<change>` must:
- create change directory
- resolve + validate workflow
- write `execution/state.json` with `definition` and initialized `runtime`
- create `execution/events.log`
- then execute first `next` pull

Rationale:
- Ensures new changes are immediately executable with no additional init step.
- Ensures lifecycle artifacts exist from creation moment.

Alternatives considered:
- Lazy-init state on first protocol call: rejected to avoid hidden side effects and reduce debugging ambiguity.

### Decision: Remove runtime `${...}` substitution entirely

Payload fields (`executor`, `skill`, `script`, `prompt`, `human`, `inputs`) are treated as literal values from definition snapshot. No dynamic interpolation from context/state/env/actions is performed.

Rationale:
- Reduces runtime complexity and unpredictability.
- Removes substitution-specific failure mode (`invalid_expression`).
- Simplifies validation and test matrix.

Alternatives considered:
- Keep limited substitution subset: rejected to keep system minimal during development stage.

### Decision: Remove `plan` naming from execution internals over time

Internal functions that currently operate on `plan` documents will be shifted to snapshot definition terminology (`workflow definition` / `state definition`) where changed in this implementation.

Rationale:
- Aligns code semantics with new architecture.
- Prevents accidental reintroduction of `plan.json` assumptions.

## Risks / Trade-offs

- [Risk] Larger `state.json` combines definition + runtime and may become noisy.
  → Mitigation: strict top-level partitioning (`meta`, `definition`, `runtime`) and stable serialization.

- [Risk] Removing substitutions reduces flexibility for advanced dynamic workflows.
  → Mitigation: accept intentional simplification now; future reintroduction can be explicit and capability-scoped.

- [Risk] Existing tests and docs heavily reference `plan.json`.
  → Mitigation: update tests/specs atomically in same change so contracts stay coherent.

## Migration Plan

- No legacy compatibility path is provided.
- Implementation immediately switches runtime to snapshot-only model.
- Tests and schemas are updated in same change to enforce the new source-of-truth.

## Open Questions

- Should `definition` preserve legacy envelope names (`planId`, `schemaVersion`) temporarily, or rename now to workflow-specific names? This change keeps minimal churn and can refine naming in a later cleanup.
