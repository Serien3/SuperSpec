## Why

Current plan initialization mixes two concerns in one file: the plan document format and the predefined action sequence itself. This makes the default template noisy, hard to evolve, and difficult to extend when new planning patterns are needed. We need a scheme-driven model so teams can add or customize plan generation patterns over time without rewriting core plan scaffolding logic.

## What Changes

- Introduce a scheme abstraction for plan generation, where each scheme defines action-sequence metadata, action list, and related defaults.
- Introduce a generic base plan template that captures structural fields only, separating format from scheme content.
- Add a scheme directory convention so users can add custom schemes later (for example under a dedicated `schemes/` folder).
- Update plan initialization flow to render `plan.json` by combining base template + selected scheme + change-scoped variables.
- Define deterministic merge/override rules for template, scheme, and CLI/runtime-provided values.

## Capabilities

### New Capabilities
- `plan-scheme-management`: Defines discoverable, file-based scheme definitions and validation requirements for scheme metadata and action sequence content.
- `plan-generation-from-scheme`: Defines deterministic rendering of a change plan from base template plus selected scheme.

### Modified Capabilities
- `plan-mode-initialization`: Replace or extend fixed mode-to-template behavior with scheme selection semantics during `plan init`.
- `change-plan-orchestration`: Update lifecycle expectations so orchestration consumes rendered `plan.json` while generation strategy remains scheme-driven.

## Impact

- Affected CLI: plan initialization commands and any mode/scheme selection flags and validation errors.
- Affected templates/assets: existing `plan.template.json` semantics split into base template and scheme files.
- Affected engine boundaries: clearer separation between generation-time concerns and runtime orchestration that reads `plan.json` only.
- Affected tests: new coverage for scheme discovery, merge rules, and generated plan correctness.
