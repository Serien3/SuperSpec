## Context

Workflow authoring currently allows both explicit executor declaration and implicit executor inference from payload fields (`skill`, `script`, `human`). This dual model creates ambiguity for users and for validation outcomes, especially when step fields are mixed. The project already has a requirement for a minimal and finite customization contract, but executor authoring remains split in practice.

## Goals / Non-Goals

**Goals:**
- Define a minimal workflow core contract with explicit required fields.
- Separate execution-critical fields from readability/annotation fields.
- Enforce exact executor payload matching rules during workflow validation.
- Keep schema validation and runtime validation behavior aligned.
- Update built-in workflow templates and tests to the normalized format.

**Non-Goals:**
- Backward compatibility with legacy executor inference authoring.
- New executor types.
- Changes to runtime step scheduling semantics.

## Decisions

1. Enforce explicit executor for every step.
- Decision: `steps[].executor` is mandatory in workflow authoring.
- Rationale: avoids inference ambiguity and creates a single mental model.
- Alternative considered: keep inference and add warnings. Rejected because it prolongs confusion and adds branchy validation behavior.

2. Enforce exactly-one executor payload model.
- Decision: each step must contain exactly one matching payload for its executor:
  - `skill` => requires `skill`, forbids `script`/`human`
  - `script` => requires `script`, forbids `skill`/`human`
  - `human` => requires `human.instruction`, forbids `skill`/`script`
- Rationale: makes behavior deterministic and improves extensibility for future validators.
- Alternative considered: allow extra payload fields but ignore them. Rejected because silent acceptance causes author mistakes.

3. Split fields into core vs annotations in contract and docs.
- Decision: maintain strict validation for core fields while retaining optional annotation fields (`title`, `notes`, `tags`, `artifacts`, etc.).
- Rationale: preserves readability without coupling annotations to execution semantics.

4. Keep validate diagnostics stable and actionable.
- Decision: add/normalize executor-core related error codes and preserve path-based error reporting.
- Rationale: users need deterministic fixes when writing custom workflows.

## Risks / Trade-offs

- [Risk] Existing custom workflows using implicit executor inference will fail validation.
  - Mitigation: update templates/examples and provide precise validation hints.
- [Risk] Schema and semantic validation may drift again.
  - Mitigation: add tests that assert matching behavior for schema checks, semantic checks, and `superspec validate` output.
- [Risk] Tightening fields may block some ad-hoc metadata usage.
  - Mitigation: keep annotation fields explicit and allow top-level/step metadata-style fields already defined by schema.

## Migration Plan

1. Update workflow schema to enforce explicit `executor` and one-of payload constraints.
2. Update semantic validation in workflow loader to reject mixed/extra executor payloads consistently.
3. Update packaged workflow templates to explicit executor style.
4. Update tests for validate and integration behavior under strict contract.
5. Run targeted tests and full suite.

Rollback strategy:
- Revert this change set if downstream migration blockers are unacceptable.

## Open Questions

- Should `inputs` be mandatory for `skill` steps in a future schema version, or remain optional?
- Should we add a dedicated machine-readable migration guide command for workflow authors?
