## Context

SuperSpec currently initializes plans through a mode-to-template mapping where the selected template contains both structural plan fields and a concrete step sequence. In practice, this mixes two different concerns: plan document shape and planning strategy. As more planning strategies are needed, this approach scales poorly because each new strategy tends to duplicate structural fields while only changing sequence metadata and step definitions.

This change introduces a scheme-driven generation model: base template provides stable plan structure, scheme files provide sequence semantics. Runtime orchestration remains unchanged and continues to consume only rendered `plan.json`.

## Goals / Non-Goals

**Goals:**
- Separate plan format (base template) from plan strategy content (scheme definitions).
- Allow users to add custom scheme files over time without changing core command semantics.
- Make `plan init` deterministic and auditable via explicit merge precedence.
- Preserve backward-compatible runtime behavior where protocol execution uses only rendered `plan.json`.

**Non-Goals:**
- Reworking protocol execution semantics (`next/complete/fail/status`).
- Introducing parallel DAG scheduling or multi-agent coordination.
- Implementing remote scheme registries or dynamic network fetch.

## Decisions

### Decision: Introduce file-based scheme definitions
- Schemes will be stored in a dedicated scheme directory and treated as declarative inputs.
- Each scheme contains metadata (`schemeId`, `version`, description), defaults, and step sequence definitions.
- Rationale: keeps planning patterns composable and user-extensible while remaining reviewable in git.

Alternatives considered:
- Keep adding hardcoded mode constants in CLI: simple initially but creates recurring code edits and poor extensibility.
- Store schemes inside Python modules: stronger typing but blocks user-defined schemes without code changes.

### Decision: Keep a generic base template with no predefined step sequence
- Base template defines stable plan envelope (`schemaVersion`, `context`, optional metadata scaffolding).
- Scheme contributes strategy-dependent content (`defaults`, `steps`, optional scheme variables).
- Rationale: clean separation of concerns and lower duplication across planning patterns.

Alternatives considered:
- Per-scheme full template files: easier migration from current state but perpetuates duplication and drift.

### Decision: Deterministic merge precedence during plan generation
- Merge order: `base template` < `scheme`.
- Protected fields (`context.changeName`, `context.changeDir`) are always generated from change context and cannot be overwritten by scheme files.
- Rationale: predictable behavior and safer generated plans.

Alternatives considered:
- Let scheme override all fields: flexible but can generate invalid or misleading change-scoped context.

### Decision: Runtime boundary remains unchanged
- `plan_loader` and protocol orchestration continue to validate and execute only `openspec/changes/<change>/plan.json`.
- Scheme metadata is generation-time concern, not execution-time dependency.
- Rationale: minimizes blast radius and avoids coupling runtime with plan authoring mechanics.

## Risks / Trade-offs

- [Risk] Scheme schema too loose leads to invalid or inconsistent plans. -> Mitigation: add explicit scheme schema validation and fail-fast init errors.
- [Risk] Multiple locations for scheme files create discovery ambiguity. -> Mitigation: define a single default directory with clear precedence rules.
- [Risk] Backward compatibility confusion for `--mode` users. -> Mitigation: map existing `sdd` mode to a first-party scheme and provide clear deprecation/alias guidance.
- [Risk] Merge logic complexity introduces subtle precedence bugs. -> Mitigation: add targeted tests for precedence and protected-field behavior.

## Migration Plan

1. Introduce base template and first-party `sdd` scheme while keeping current command flow.
2. Update `plan init` to resolve scheme and render merged `plan.json`.
3. Keep `--mode sdd` behavior via compatibility alias to the corresponding scheme.
4. Add tests for scheme discovery, rendering precedence, and generated plan validity.
5. Update docs to describe custom scheme authoring and selection.

Rollback strategy:
- Revert to fixed mode-to-template mapping and preserve generated plans already written in change directories.

## Open Questions

- Should custom scheme lookup support both repository-local and user-global directories in v1?
- Do we want optional `superspec scheme list/show/validate` commands in the first release or follow-up?
- Should scheme files support lightweight templating for repeated step fragments, or keep them strictly explicit initially?
