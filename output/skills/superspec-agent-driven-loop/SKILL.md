---
name: superspec-agent-driven-loop
description: Run the full SuperSpec workflow in agent-driven mode by polling next actions and reporting completion/failure until done.
license: MIT
compatibility: Requires superspec CLI and openspec CLI.
metadata:
  author: superspec
  version: "1.1"
---

Run SuperSpec end-to-end in protocol mode.

This skill is the execution playbook for:
- creating or selecting a change
- initializing and validating a plan
- running `next -> execute -> complete|fail` in a pull loop
- stopping only at terminal `done`

**Input**: change name (recommended), optional change summary, optional owner label.

## Steps

1. **Select or create change**
   - If a change name is provided and exists, use it.
   - If a change name is provided and does not exist, create it:
     ```bash
     superspec change new "<name>" --summary "<summary>"
     ```
   - Optional one-step create+init:
     ```bash
     superspec change new "<name>" --summary "<summary>" --init-plan --plan-schema sdd
     ```
   - If no name is provided, list changes and ask user to choose:
     ```bash
     openspec list --json
     ```

2. **Initialize plan**
   - Current contract:
     ```bash
     superspec plan init "<name>" --schema sdd
     ```
   - Optional init-time overrides:
     ```bash
     superspec plan init "<name>" --schema sdd --title "<title>" --goal "<goal>"
     ```

3. **Validate plan**
   ```bash
   superspec plan validate "<name>"
   ```

4. **Loop until terminal state**
   - Repeatedly call:
     ```bash
     superspec plan next "<name>" --owner "<owner>" --json
     ```
   - Handle by `state`:
     - `ready`: execute action, then report `complete` or `fail`
     - `blocked`: wait/poll with backoff, then call `next` again
     - `done`: stop loop and report final status

5. **Dispatch by executor for `ready`**
   - If `action.executor == "script"`:
     - Run `action.script.command`
     - On success:
       ```bash
       superspec plan complete "<name>" "<actionId>" --result-json '{"ok":true,"executor":"script","actionId":"<actionId>","exitCode":0}'
       ```
     - On failure:
       ```bash
       superspec plan fail "<name>" "<actionId>" --error-json '{"code":"script_failed","message":"...","executor":"script"}'
       ```
   - If `action.executor == "skill"`:
     - Invoke the named skill with provided `skill.name`, `skill.version`, `skill.input`, and `contextFiles`
     - On success, report `complete`
     - On failure, report `fail`

6. **Use `status` for progress and terminal detail**
   ```bash
   superspec plan status "<name>" --json
   ```
   - Use this for progress counters and last failure details.

## Required report payload fields

- `complete --result-json` SHOULD include (JSON object):
  - `ok` (boolean)
  - `executor` (`script` or `skill`)
  - `actionId` (string)
  - `summary` (string, optional)
  - `outputs` (object, optional)

- `fail --error-json` SHOULD include (JSON object):
  - `code` (string machine-readable)
  - `message` (string human-readable)
  - `executor` (`script` or `skill`)
  - `retryable` (boolean, optional)
  - `details` (object, optional)

## Blocked-state polling guidance

- For `state == "blocked"`, do not fail the run immediately.
- Poll `next` again after backoff (e.g., 2s, then 4s, capped at 15s).
- Continue until `ready` or terminal `done`.

## Terminal signaling

- If `done` with status `success`: report workflow success.
- If `done` with status `failed`: report workflow failure and include last failure details from:
  ```bash
  superspec plan status "<name>" --json
  ```

## Minimal example sequence

```bash
superspec change new demo-change --summary "demo"
superspec plan init demo-change --schema sdd
superspec plan validate demo-change
superspec plan next demo-change --owner agent --json
# execute payload...
superspec plan complete demo-change a1 --result-json '{"ok":true,"executor":"skill","actionId":"a1"}'
```
