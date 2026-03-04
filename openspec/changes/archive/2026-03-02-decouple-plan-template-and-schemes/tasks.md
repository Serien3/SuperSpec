## 1. Scheme Model And Validation

- [x] 1.1 Define a scheme file contract (required metadata, defaults, actions, optional variables) and add schema-based validation for scheme documents.
- [x] 1.2 Introduce canonical scheme discovery rules for a dedicated scheme directory and implement clear errors for missing/unknown scheme names.
- [x] 1.3 Add tests for valid scheme loading and invalid scheme rejection paths.

## 2. Base Template And Rendering Pipeline

- [x] 2.1 Split current monolithic plan template into a generic base plan template and first-party scheme content for the default flow.
- [x] 2.2 Implement deterministic plan rendering that merges base template and scheme payload with documented precedence.
- [x] 2.3 Enforce protected change context fields (`changeName`, `changeDir`) so generated plans always bind to the active change.
- [x] 2.4 Add tests that assert generated `plan.json` shape, merge precedence, and protected-field behavior.

## 3. CLI Integration And Compatibility

- [x] 3.1 Update `superspec plan init` to accept explicit scheme selection while preserving `--mode sdd` compatibility via alias mapping.
- [x] 3.2 Update initialization error handling/messages for unsupported mode aliases and unsupported scheme names.
- [x] 3.3 Add CLI tests covering scheme selection, compatibility alias behavior, and failure modes.

## 4. Documentation And Rollout

- [x] 4.1 Document how to create and place custom scheme files for future extension.
- [x] 4.2 Document generation semantics (base template vs scheme) and runtime boundary (`plan.json` is still the only execution input).
- [x] 4.3 Validate end-to-end workflow by generating a plan from a custom scheme and confirming `plan validate`/protocol commands still operate normally.
