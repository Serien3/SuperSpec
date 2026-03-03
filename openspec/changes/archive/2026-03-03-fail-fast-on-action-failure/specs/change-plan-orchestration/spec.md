## MODIFIED Requirements

### Requirement: Runtime-relevant defaults surface
The system MUST keep runtime defaults constrained to fields with active execution semantics.

#### Scenario: Persist effective runtime defaults
- **WHEN** protocol execution state is initialized
- **THEN** persisted defaults include only execution-relevant fields (`executor`)
- **AND** retry policy fields are not persisted as runtime configuration

### Requirement: Failure policy enum constraints
The system MUST use fail-fast terminal semantics for action failure handling.

#### Scenario: Reported failure always halts workflow
- **WHEN** any action failure is reported through the protocol
- **THEN** the workflow enters terminal `failed`
- **AND** no continuation policy is applied for further autonomous action execution

## REMOVED Requirements

### Requirement: Fixed-interval retry configuration
**Reason**: Retry timing controls (`maxAttempts`, `intervalSec`) are removed to simplify execution semantics and force human intervention after failure.

**Migration**: Remove `defaults.retry` and action-level `retry` from plans/workflows; rely on fail-fast handling and human-guided reruns.
