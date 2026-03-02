## 1. Protocol Contract Simplification

- [x] 1.1 Remove lease fields from `next`/`complete`/`fail` command contracts and protocol response payloads.
- [x] 1.2 Refactor protocol state handling to single-agent serial ownership assumptions without lease lifecycle storage.
- [x] 1.3 Update CLI command surface to remove `--lease` requirements and align error messages with simplified contract.

## 2. Plan Template Simplification

- [x] 2.1 Simplify default plan template content to a minimal serial single-agent baseline.
- [x] 2.2 Remove or relocate advanced concurrency-oriented starter knobs from default template while preserving valid schema output.
- [x] 2.3 Verify `plan init` output remains valid and immediately executable under the simplified protocol.

## 3. Documentation and Guidance Cleanup

- [x] 3.1 Update active specs and protocol contract docs to remove lease-centric language and examples.
- [x] 3.2 Update agent-loop skill/guidance examples to use lease-free reporting flow.
- [x] 3.3 Remove or rewrite obsolete documentation sections that describe lease lifecycle as current behavior.

## 4. Tests and Verification

- [x] 4.1 Replace lease-conflict/expiry-focused tests with single-agent serial protocol lifecycle tests.
- [x] 4.2 Add/adjust integration tests for `next -> execute -> complete|fail` loop behavior without lease tokens.
- [x] 4.3 Run full relevant test suite and confirm no lease artifacts are required in baseline execution state.
