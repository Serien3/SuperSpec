---
name: superspec-agent-driven-loop
description: Run the full SuperSpec workflow in agent-driven mode by polling next actions and reporting completion/failure until done.
license: MIT
metadata:
  author: superspec
  version: "1.4"
---

Run SuperSpec end-to-end in protocol mode.

This skill is the execution playbook for:
- creating or selecting a change
- initializing and validating a plan
- running `next -> execute -> complete|fail` in a pull loop
- stopping only at terminal `done`

**Input**: change name (recommended), optional owner label.

## Steps

1. **Select or create change**
   - If a change name is provided and exists, use it.
   - If a change name is provided and does not exist, create it:
     ```bash
     superspec change new "<name>"
     ```
   - If no name is provided, list changes and ask user to choose:
     ```bash
     openspec list --json
     ```

2. **Initialize plan**
   - `--schema` is required:
     ```bash
     superspec plan init "<name>" --schema SDD
     ```
   - Optional init-time overrides:
     ```bash
     superspec plan init "<name>" --schema SDD --title "<title>" --goal "<goal>"
     ```

3. **Loop until terminal state**
   - Repeatedly call:
     ```bash
     superspec plan next "<name>" --owner "<owner>" --json
     ```
   - Handle by `state`:
     - `ready`: goto **step4**
     - `blocked`: use blocked polling policy, then call `next` again
     - `done`: stop loop and report final status
   - Treat `plan fail` as in-loop state update, not terminal signal. Continue polling until `next` returns `done`.

4. **Dispatch by executor for `ready`**
  - If `action.executor == "script"`:
    - Run `action.script_command`
     - On success:
       ```bash
       superspec plan complete "<name>" "<actionId>" --output-json '{"ok":true,"executor":"script","actionId":"<actionId>","exitCode":0}'
       ```
     - On failure:
       ```bash
       superspec plan fail "<name>" "<actionId>" --error-json '{"code":"script_failed","message":"...","executor":"script"}'
       ```
   - If `action.executor == "skill"`:
   - Invoke the named skill in `action.skillName`
   - Use `action.prompt` as the execution guidance text
     - On success:
       ```bash
       superspec plan complete "<name>" "<actionId>" --output-json '{"ok":true,"executor":"skill","actionId":"<actionId>","exitCode":0}'
       ```
     - On failure:
       ```bash
       superspec plan fail "<name>" "<actionId>" --error-json '{"code":"skill_failed","message":"...","executor":"skill"}'
       ```

5. **Use `status` for checkpoints, not every action**
   ```bash
   superspec plan status "<name>" --json
   ```
   - Do not call `status` after each successful action; `next` already drives progress.
   - Call `status` at major checkpoints (start, unexpected blockage, terminal `done`, or failure triage).
   - Use `--retry` for retry timing and next wake-up:
     ```bash
     superspec plan status "<name>" --retry --json
     ```
   - Default JSON is compact summary; use `--full` only when full action objects are needed:
     ```bash
     superspec plan status "<name>" --json --full
     ```
   - For protocol contract inspection/debugging only:
     ```bash
     superspec plan status "<name>" --json --debug
     ```

## Required report payload fields

- `complete --output-json` SHOULD include (JSON object):
  - `ok` (boolean)
  - `executor` (`script` or `skill`)
  - `actionId` (string)
  - `summary` (string, optional)
  - `outputs` (object, optional)

- `fail --error-json` SHOULD include (JSON object):
  - `code` (string machine-readable)
  - `message` (string human-readable)
  - `executor` (`script` or `skill`)
  - `details` (object, optional)

## Blocked-state polling guidance

- For `state == "blocked"`, do not fail the run immediately.
- Prefer retry snapshot from execution state:
  1. Run `superspec plan status "<name>" --retry --json`.
  2. If `status=failed` and `retry.scheduledCount=0`, stop polling and report terminal failure.
  3. Read `retry.nextWakeInSec`.
  4. If present, wait using `wait_sec = max(1, retry.nextWakeInSec)`.
  5. If absent, fallback to fixed 2s polling.
- Continue until `ready` or terminal `done`.
- If the previous step was `plan fail`, keep following the same polling rules above.
- Retry settings are fixed-interval from plan `retry` config:
  - `maxAttempts`: max retry count after a failure report
  - `intervalSec`: fixed wait between retry attempts
- Track consecutive blocked cycles; if blocked exceeds 30 consecutive loops, stop and report `execution_stalled`.

## Terminal signaling

- If `next` returns `done`, query `status` to determine terminal result.
- If `status` is `success`: report workflow success.
- If `status` is `failed`: report workflow failure and include last failure details from:
  ```bash
  superspec plan status "<name>" --json
  ```

## Minimal example sequence

```bash
superspec change new demo-change
superspec plan init demo-change --schema SDD
superspec validate --schema SDD
superspec plan next demo-change --owner agent --json
# execute payload...
superspec plan complete demo-change a1 --output-json '{"ok":true,"executor":"skill","actionId":"a1"}'
```
