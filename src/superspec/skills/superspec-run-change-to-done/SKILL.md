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

If `change_name` is missing, derive a kebab-case name (e.g., "add user authentication" → `add-user-auth`).

## End-to-End Workflow

### Step 1: Resolve the target change.
   - Reuse existing change when present.
   - Create when absent:
     ```bash
     superspec change new "<change_name>"
     ```

### Step 2:  Ensure change-scoped plan exists and is valid.
   - Initialize when `openspec/changes/<change_name>/plan.json` is missing:
     ```bash
     superspec plan init "<change_name>" --schema sdd
     ```

### Step 3: Run protocol loop until terminal.
   - Pull next action:
     ```bash
     superspec plan next "<change_name>" --owner "<owner>" --json
     ```
   - Handle response state:
     - `ready`: dispatch executor and report `complete` or `fail`.
     - `blocked`: compute wait from retry schedule, then poll again.
     - `done`: stop loop and fetch terminal status.
   - Execution loop contract:
     1. Call `next`.
     2. If `state=ready`, **goto step4**. Execute exactly one action and report `complete` or `fail`.
     3. Immediately call `next` again.
     4. If `state=blocked`, use **blocked polling policy** and call `next` again.
     5. Exit only when `state=done`.

#### Blocked Polling Policy

When `next.state=blocked`, use retry snapshot:
1. Read retry status:
   ```bash
   superspec plan status "<change_name>" --retry --json
   ```
2. If `status=failed` and `retry.scheduledCount=0`, stop polling and report terminal failure.
3. Read `retry.nextWakeInSec`.
4. If present, use:
   - `wait_sec = max(1, retry.nextWakeInSec)`
5. If absent, use fallback fixed polling interval (5s).
6. Sleep `wait_sec`, then call `next` again.
7. Track consecutive blocked cycles; if blocked exceeds 30 consecutive loops, stop and report `execution_stalled`.

Retry behavior comes from plan `retry` config:
- `maxAttempts`: max retry count after a failure report
- `intervalSec`: fixed wait between retry attempts

### Step 4: Dispatch `ready` action by executor.
   - `script` executor:
     - Execute `action.script_command`.
     - On success:
       ```bash
       superspec plan complete "<change_name>" "<actionId>" --result-json '{"ok":true,"executor":"script","actionId":"<actionId>","summary":"script completed"}'
       ```
     - On failure:
       ```bash
       superspec plan fail "<change_name>" "<actionId>" --error-json '{"code":"script_failed","message":"script execution failed","executor":"script"}'
       ```
   - `skill` executor:
     - Invoke `action.skillName` and follow `action.prompt`.
     - On success:
       ```bash
       superspec plan complete "<change_name>" "<actionId>" --result-json '{"ok":true,"executor":"skill","actionId":"<actionId>","summary":"skill completed"}'
       ```
     - On failure:
       ```bash
       superspec plan fail "<change_name>" "<actionId>" --error-json '{"code":"skill_failed","message":"skill execution failed","executor":"skill"}'
       ```

### Step 5: Produce terminal result and feedback.
   - Read terminal status:
     ```bash
     superspec plan status "<change_name>" --json
     ```
   - Read status after loop exits on `next.state=done` (terminal confirmation), not after each action.

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
