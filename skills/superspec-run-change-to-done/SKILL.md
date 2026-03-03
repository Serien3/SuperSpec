---
name: superspec-run-change-to-done
description: Entry skill for SuperSpec autonomous delivery. Use when Codex needs to create or select a change, initialize and validate its plan, execute all actions via the protocol loop until terminal done, and return structured success or failure feedback.
---

# SuperSpec Run Change To Done

Drive one change from setup to terminal outcome using the SuperSpec pull protocol.

## Inputs

Resolve these inputs first:
- `change_name` (recommended)
- `owner` for `plan next` (default: `agent`)

If `change_name` is missing, derive a short slug and report it in the final feedback.

## Command Baseline

Prefer installed CLI commands:
- `superspec ...`

## End-to-End Workflow

1. Prepare runtime once.
   - Initialize agent integration when missing:
     ```bash
     superspec init --agent codex
     ```

2. Resolve the target change.
   - Reuse existing change when present.
   - Create when absent:
     ```bash
     superspec change new "<change_name>"
     ```

3. Ensure change-scoped plan exists and is valid.
   - Initialize when `openspec/changes/<change_name>/plan.json` is missing:
     ```bash
     superspec plan init "<change_name>" --schema sdd
     ```
   - Validate before execution:
     ```bash
     superspec plan validate "<change_name>"
     ```

4. Run protocol loop until terminal.
   - Pull next action:
     ```bash
     superspec plan next "<change_name>" --owner "<owner>" --json
     ```
   - Handle response state:
     - `ready`: dispatch executor and report `complete` or `fail`.
     - `blocked`: use blocked polling policy and poll again.
     - `done`: stop loop and fetch terminal status.

#### Blocked Polling Policy

When `next.state=blocked`, use retry snapshot:
1. Read retry status:
   ```bash
   superspec plan status "<change_name>" --retry --json
   ```
2. Read `retry.nextWakeInSec`.
3. If present, use:
   - `wait_sec = max(1, retry.nextWakeInSec)`
4. If absent, use fallback fixed polling interval (2s).
5. Sleep `wait_sec`, then call `next` again.

Retry behavior comes from plan `retry` config:
- `maxAttempts`: max retry count after a failure report
- `intervalSec`: fixed wait between retry attempts

5. Dispatch `ready` action by executor.
   - `script` executor:
     - Execute `action.script_command`.
     - On success:
       ```bash
       superspec plan complete "<change_name>" "<actionId>" --result-json '{"ok":true,"executor":"script","actionId":"<actionId>","summary":"script completed"}'
       ```
     - On failure:
       ```bash
       superspec plan fail "<change_name>" "<actionId>" --error-json '{"code":"script_failed","message":"script execution failed","executor":"script","details":"<...>"}'
       ```
   - `skill` executor:
     - Invoke `action.skillName` and follow `action.prompt`.
     - On success:
       ```bash
       superspec plan complete "<change_name>" "<actionId>" --result-json '{"ok":true,"executor":"skill","actionId":"<actionId>","summary":"skill completed"}'
       ```
     - On failure:
       ```bash
       superspec plan fail "<change_name>" "<actionId>" --error-json '{"code":"skill_failed","message":"skill execution failed","executor":"skill","details":"<...>"}'
       ```

6. Produce terminal result and feedback.
   - Read terminal status:
     ```bash
     superspec plan status "<change_name>" --json
     ```
   - Use `--full` only when action-level triage is needed.
   - Use `--debug` only when protocol contract inspection is needed.

## Reporting Contract

Use structured payloads.

`complete --result-json` should include:
- `ok` (boolean)
- `executor` (`script` or `skill`)
- `actionId` (string)
- optional `summary`, `outputs`

`fail --error-json` should include:
- `code` (machine-readable)
- `message` (human-readable)
- `executor` (`script` or `skill`)
- optional `details`

## Guardrails

- Use the exact `action.id` returned by `next`.
- Do not report `complete` or `fail` before real execution.
- Do not call `status` after every success; use checkpoint/terminal reads.
- Do not call `status --retry` or `status --full` after every failure; keep the loop pull-driven by `next`.
- Do not treat `plan fail` as terminal; continue `next` polling until `next.state=done`.
- Do not terminate on first `blocked`; continue polling.
- Stop only when `next` returns `done`.

## Final Feedback Template

On success, report:
- `change_name`
- terminal `status`
- progress (`done/total`, `failed`, `running`)
- key completed actions

On failure, report:
- `change_name`
- terminal `status`
- failed action id(s)
- error code/message and whether retry/replan is required
